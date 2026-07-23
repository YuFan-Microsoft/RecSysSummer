"""
LLM-based analysis of SID generative-rec inference results, to mine RL-training insights.

WHAT IT DOES
  Loads the per-example inference dump `yufan/rec_inference_results` (history, ground-truth
  target, top-10 constrained beam, native greedy decode, chain-of-thought) and asks
  GPT-5.6-sol to label each example along dimensions that a rule-based / numeric pass cannot
  judge -- the SEMANTIC gap between our beam-10 and the target, what KIND of next-item the
  target is (continuation vs exploration ...), slate diversity, and CoT reasoning quality.
  Each labelled example carries a suggested `rl_signal` so the aggregate tells us how to
  reshape the Phase-3 GRPO reward / curriculum.

  Each example is scored against an anchored RUBRIC (every 1-5 level and every category is
  defined in SYSTEM_PROMPT) and, crucially, the judge first writes three GROUNDED PROSE
  analyses that quote the actual titles and give the logic, so the scores follow from a
  stated argument rather than being bare numbers:
    prose  : target_analysis (what the target is & how it relates to history),
             prediction_analysis (what the beam-10 bet on & how/why it hit or missed),
             cot_analysis (whether the reasoning found the right interest & is consistent)
    A. Target characterization  : target_relation, predictability, history_coherence
    B. Beam-10 <-> target gap   : beam_captured_intent, best_beam_relation, n_beams_satisfying,
                                  target_recoverable, failure_mode
    C. Beam-10 slate quality    : beam_interest_coverage, beam_relevance_count, beam_redundancy,
                                  beam_explore_exploit, beam_personalization
    D. CoT reasoning quality    : cot_grounded, cot_identified_target_interest,
                                  cot_answer_consistency, cot_hallucination, cot_quality
    E. Rollup                   : key_insight, rl_signal

HOW TO RUN
  Prereq: `az login` (gpt5_endpoint_test.get_GPT5_client uses DefaultAzureCredential).

    # pilot: 200 rows of one config/domain, all 3 endpoints, 8 workers/endpoint
    python analyze_inference_gpt5.py --config reproduced --domain Video_Games --limit 200

    # full run of one split
    python analyze_inference_gpt5.py --config reproduced --domain Office_Products

    # push throughput / restrict endpoints / stronger reasoning
    python analyze_inference_gpt5.py --config baseline --domain Industrial_and_Scientific \
        --per-endpoint 12 --reasoning-effort medium \
        --endpoints feedscopilot-azureopenai-au feedscopilot-azureopenai-sweden

THROUGHPUT
  Every endpoint runs in parallel; each drives --per-endpoint client-bound worker threads,
  so total concurrency = #endpoints * per-endpoint, auto load-balanced through one queue.

RESUME (crash-safe)
  Each finished row is streamed to <out-dir>/<config>.<domain>.analysis.jsonl immediately
  (keyed by row_key). Re-run the SAME command to resume: done rows are skipped, failures retried.

OUTPUT
  <out-dir>/<config>.<domain>.analysis.jsonl   (raw, one JSON object per row)
  <out-dir>/<config>.<domain>.analysis.csv     (flattened, for aggregation / plotting)
"""

import argparse
import json
import os
import queue
import re
import threading
import time

import pandas as pd
from datasets import load_dataset

from gpt5_endpoint_test import ENDPOINTS, get_GPT5_client

# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------
HF_REPO = "yufan/rec_inference_results"
CONFIGS = ["baseline", "reproduced"]
DOMAINS = ["Video_Games", "Office_Products", "Industrial_and_Scientific"]

MODEL = "gpt-5.6-sol"                     # judge model; deployed on the 3 endpoints below
DEFAULT_ENDPOINTS = [                     # only these carry gpt-5.6-sol
    "feedscopilot-azureopenai-au",
    "feedscopilot-azureopenai-eastus",
    "feedscopilot-azureopenai-sweden",
]

DEFAULT_PER_ENDPOINT = 8                  # worker threads per endpoint (total = #ep * this)
MAX_COMPLETION_TOKENS = 2600             # room for 3 prose analyses + all rubric scores
DEFAULT_REASONING_EFFORT = "low"         # minimal|low|medium|high
MAX_TITLE_CHARS = 90                      # truncate each item title
MAX_HISTORY_ITEMS = 25                    # cap history length shown to the judge
MAX_COT_CHARS = 2000                      # truncate the chain-of-thought
LOG_EVERY_SEC = 10

SID_RE = re.compile(r"<[^>]+>")
_write_lock = threading.Lock()


# --------------------------------------------------------------------------------------
# Prompt: rubric-style judge. First force three GROUNDED PROSE analyses, then anchored
# scores derived from them. Single system + user; returns one strict-JSON object.
# --------------------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a meticulous recommender-systems research analyst auditing a SID-based generative recommendation model. Your labels drive reward redesign, so they must be consistent and defensible.

SETUP. The model reads a user's chronological interaction history and predicts the next item as a semantic ID (SID, format <a_XX><b_YY><c_ZZ>). It writes a chain-of-thought (CoT), then decodes the next item with constrained beam search (top-10). For ONE user you receive: the history, the ground-truth next item (target), the model's top-10 beam predictions, its unconstrained greedy prediction (native), `exact_hit_rank` (ground-truth: the 1-based rank at which the target appears in the beam list, or 0 if absent), and the CoT.

GROUNDING RULES.
- Judge SEMANTICS from item TITLES; SIDs are opaque codes, use them ONLY to check exact identity or shared prefixes.
- Base every judgment ONLY on the provided history and titles. NEVER invent facts about an item beyond what its title implies.
- `exact_hit_rank` is authoritative for whether the model hit; use it for `failure_mode` and `best_beam_relation=exact`, but judge every SEMANTIC dimension independently of it.

METHOD. Work in two passes. PASS 1 - write the three prose analyses below, quoting specific titles and giving the reasoning (what, and WHY). PASS 2 - assign every rubric score so it is justified by what you wrote; obey the anchors exactly and stay internally consistent (e.g. if failure_mode='right_interest_wrong_item' then beam_captured_intent must be true).

PROSE FIELDS (2-4 grounded sentences each; name real items).
- target_analysis: What is the target item? Which specific history items / interest does it connect to (or not)? Is it a natural continuation, a complement, or a jump, and is it fairly inferable from the history? Explain the logic.
- prediction_analysis: What did the 10 beams collectively bet on (name the dominant items/interests)? Did they capture the target's need? If they missed, state the precise reason (which interest was over- or under-weighted, whether the slate collapsed onto one interest, whether any beam is a viable substitute for the target).
- cot_analysis: Did the reasoning identify the user's real interest and the target's interest? Is it grounded in specific history items or generic? Is its stated conclusion consistent with the beams the model actually emitted?

RUBRIC (anchors are binding).

[A. TARGET CHARACTERIZATION]
target_relation - single best fit of target vs history:
  repeat = target is (near-)identical to an item already in history (replenishment / re-engagement).
  same_subcategory = same fine-grained type/genre as recent items, different specific item.
  same_brand_or_series = same franchise/brand/sequel, or a direct accessory for a device in history.
  complementary = different type but functionally complements history (console->game, printer->ink, microscope->slides).
  broadening = a related but NEW sub-interest within the same broad domain.
  exploration = a genuine jump to an unrelated domain/interest.
predictability (1-5): 5 = history points almost directly at this item (next in series / obvious accessory / consumable refill). 4 = same sub-genre or brand as recent items; strong natural continuation. 3 = tied to a broad interest in history but many equally likely alternatives. 2 = weak, indirect link; a stretch. 1 = essentially unpredictable, no signal in history points to it.
history_coherence (1-5): 5 = all items reflect one clear consistent interest. 4 = one dominant interest with minor detours. 3 = 2-3 distinct but readable interests. 2 = mostly scattered, weak thread. 1 = no discernible pattern.

[B. BEAM-10 vs TARGET]
beam_captured_intent (bool): true if ANY beam is in the target's interest/category (even if not the exact item).
best_beam_relation - the SINGLE closest beam to the target: exact = a beam equals the target SID. substitute = a near-interchangeable item that satisfies the SAME need (e.g. same title on another platform, same product different pack size). same_category = in the target's category but not a true substitute. complementary = complements the target but isn't it. unrelated = nothing close.
n_beams_satisfying (0-10): STRICT count of beams that would genuinely satisfy the same need as the target (true substitutes). Count only items a user seeking the target would actually accept.
target_recoverable: yes = a well-trained model should rank target in top-10 from this history. borderline = reasonable but not obvious; hinges on tie-breaking among many candidates. no = not fairly recoverable; target is noise/unpredictable given the history.
failure_mode - set 'none' IFF exact_hit_rank > 0; otherwise the single dominant cause of the miss: right_interest_wrong_item = beams found the correct interest but wrong specific items. wrong_interest_selected = beams committed to a different interest than the target's. too_conservative = beams over-repeat history / stay too close, missing a natural next step. too_popular_generic = beams default to broadly popular items over personalized ones. hallucinated_unrelated = beams are largely irrelevant to the history. target_unpredictable = the miss is unavoidable, the target is not inferable.

[C. BEAM-10 SLATE QUALITY]
beam_interest_coverage (int, >=1): number of DISTINCT user interests represented across the 10 beams (1 = all beams collapse to one interest).
beam_relevance_count (0-10): how many of the 10 beams are plausible next items given the history.
beam_redundancy (1-5): 1 = 10 clearly distinct items. 3 = a few near-duplicates (same title different platform, etc.). 5 = heavily redundant, most beams are minor variants of one item.
beam_explore_exploit: mostly_exploit = nearly all beams reinforce existing history interests. balanced = a mix. mostly_explore = many beams venture into new interests.
beam_personalization (1-5): 5 = clearly tailored to this user's specific history. 3 = partly tailored, partly generic. 1 = generic / popularity-driven, ignores this user.

[D. CoT REASONING QUALITY]
cot_grounded (1-5): 5 = explicitly references concrete history items/attributes. 3 = references general themes but vague. 1 = generic boilerplate unrelated to this user.
cot_identified_target_interest (bool): did the reasoning name/derive the interest the target belongs to?
cot_answer_consistency (1-5): 5 = the reasoning's conclusion matches the emitted beams. 3 = partial alignment. 1 = concludes one thing, predicts another.
cot_hallucination (bool): does the reasoning assert facts about items/user not supported by the history?
cot_quality (1-5): overall soundness and usefulness of the reasoning toward a correct recommendation.

[E. ROLLUP]
key_insight: ONE sentence - the single most useful takeaway for improving TRAINING on this example.
rl_signal - the single most impactful lever for this example: reward_soft_hit = beams contain good substitutes, so exact-match reward is too harsh (give graded/semantic credit). downweight_noise = target is unpredictable/unrecoverable, reduce this example's training weight. reward_exploration = target is a valid exploration the model was too conservative to reach. process_reward_cot = reasoning quality (grounding/consistency) is the main lever here. add_diversity_reward = beams collapse onto one interest while other valid interests exist. keep_as_is = exact hit or already well handled.

OUTPUT. Return ONLY one JSON object (no markdown, no code fences, no text before/after), with EXACTLY these keys in this order:
{
  "target_analysis": string,
  "prediction_analysis": string,
  "cot_analysis": string,
  "dominant_interest": string,
  "target_interest": string,
  "target_relation": string,
  "predictability": integer,
  "history_coherence": integer,
  "beam_captured_intent": boolean,
  "best_beam_relation": string,
  "n_beams_satisfying": integer,
  "target_recoverable": string,
  "failure_mode": string,
  "beam_interest_coverage": integer,
  "beam_relevance_count": integer,
  "beam_redundancy": integer,
  "beam_explore_exploit": string,
  "beam_personalization": integer,
  "cot_grounded": integer,
  "cot_identified_target_interest": boolean,
  "cot_answer_consistency": integer,
  "cot_hallucination": boolean,
  "cot_quality": integer,
  "key_insight": string,
  "rl_signal": string
}"""

USER_TEMPLATE = """DOMAIN: {domain}

USER INTERACTION HISTORY (chronological; title [sid]):
{history_block}

GROUND-TRUTH NEXT ITEM (target):
{target_line}

MODEL TOP-10 BEAM PREDICTIONS (rank. title [sid]):
{beam_block}

NATIVE (unconstrained greedy) PREDICTION:
{native_line}

EXACT-MATCH INFO: exact_hit_rank = {exact_hit_rank}   (0 = target NOT in the beam list; otherwise its 1-based rank)

MODEL CHAIN-OF-THOUGHT:
{cot}

Follow the two-pass METHOD: write the three grounded prose analyses first, then assign every rubric score consistently. Return ONLY the JSON object."""


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def _fmt(seconds):
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def as_list(x):
    """HF list columns come back as numpy arrays; normalize to a python list."""
    if x is None:
        return []
    if hasattr(x, "tolist"):
        return x.tolist()
    if isinstance(x, list):
        return x
    return [x]


def _clip(s, n):
    s = "" if s is None else str(s)
    return s if len(s) <= n else s[:n] + "…"


def _item_line(title, sid, idx=None):
    prefix = f"{idx}. " if idx is not None else ""
    return f"{prefix}{_clip(title, MAX_TITLE_CHARS)} [{sid}]"


def exact_hit_rank(target_sid, predict_sids):
    for i, p in enumerate(predict_sids):
        if p == target_sid:
            return i + 1
    return 0


def build_context(row, domain):
    hist_sids = as_list(row["history_sid"])
    hist_titles = as_list(row["history_title"])
    if len(hist_sids) > MAX_HISTORY_ITEMS:            # keep the most recent items
        hist_sids = hist_sids[-MAX_HISTORY_ITEMS:]
        hist_titles = hist_titles[-MAX_HISTORY_ITEMS:]
    history_block = "\n".join(
        _item_line(t, s, i + 1) for i, (s, t) in enumerate(zip(hist_sids, hist_titles))
    ) or "(empty)"

    pred_sids = as_list(row["predict_sid"])
    pred_titles = as_list(row["predict_title"])
    beam_block = "\n".join(
        _item_line(t, s, i + 1) for i, (s, t) in enumerate(zip(pred_sids, pred_titles))
    ) or "(empty)"

    target_line = _item_line(row["target_title"], row["target_sid"])
    native_line = _item_line(row.get("native_title", ""), row.get("native_sid", ""))
    rank = exact_hit_rank(row["target_sid"], pred_sids)

    user = USER_TEMPLATE.format(
        domain=domain,
        history_block=history_block,
        target_line=target_line,
        beam_block=beam_block,
        native_line=native_line,
        exact_hit_rank=rank,
        cot=_clip(row.get("cot", ""), MAX_COT_CHARS) or "(none)",
    )
    return user, rank


def parse_json(text):
    """Extract the JSON object from the model reply (tolerant of ```json fences / prose)."""
    if not text:
        raise ValueError("empty reply")
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in reply: {text[:120]!r}")
    return json.loads(t[start:end + 1])


def chat_json(client, system, user, reasoning_effort):
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        reasoning_effort=reasoning_effort,
    )
    return parse_json(resp.choices[0].message.content or "")


def load_done_keys(path, key="row_key"):
    done = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)[key])
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


def append_jsonl(path, obj):
    line = json.dumps(obj, ensure_ascii=False) + "\n"
    with _write_lock:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())


def jsonl_to_csv(jsonl_path, csv_path):
    if not os.path.exists(jsonl_path):
        return
    records = [json.loads(l) for l in open(jsonl_path, "r", encoding="utf-8")]
    pd.json_normalize(records).to_csv(csv_path, index=False)
    print(f"  wrote {csv_path} ({len(records)} rows)")


# --------------------------------------------------------------------------------------
# Concurrency engine (client-bound workers over a shared queue)
# --------------------------------------------------------------------------------------
def run_pool(tasks, process_fn, out_path, endpoints, per_endpoint, label):
    total = len(tasks)
    if total == 0:
        print(f"  [{label}] nothing to do")
        return

    q = queue.Queue()
    for t in tasks:
        q.put(t)
    counter = {"done": 0, "fail": 0}
    clock = threading.Lock()

    t0 = time.time()
    last_log = {"t": 0.0}
    log_lock = threading.Lock()

    def emit(d, force=False):
        now = time.time()
        with log_lock:
            if not force and now - last_log["t"] < LOG_EVERY_SEC:
                return
            last_log["t"] = now
        elapsed = now - t0
        rate = d / elapsed if elapsed > 0 else 0.0
        eta = (total - d) / rate if rate > 0 else 0.0
        print(f"  [{label}] {d}/{total} ({d / total * 100:.1f}%) | "
              f"{rate:.2f} rows/s | elapsed {_fmt(elapsed)} | ETA {_fmt(eta)} | "
              f"{counter['fail']} failed", flush=True)

    def worker(endpoint):
        client = get_GPT5_client(endpoint)
        while True:
            try:
                task = q.get_nowait()
            except queue.Empty:
                return
            try:
                append_jsonl(out_path, process_fn(task, client))
                with clock:
                    counter["done"] += 1
                    d = counter["done"]
                emit(d, force=(d == total))
            except Exception as err:  # keep the pool alive; re-run resumes/retries
                with clock:
                    counter["fail"] += 1
                print(f"  [{label}] FAIL: {str(err)[:150]}", flush=True)
            finally:
                q.task_done()

    threads = []
    for ep in endpoints:
        for _ in range(per_endpoint):
            th = threading.Thread(target=worker, args=(ep,), daemon=True)
            th.start()
            threads.append(th)
    print(f"  [{label}] {total} tasks / {len(endpoints)} endpoints x {per_endpoint} "
          f"= {len(threads)} workers")
    for th in threads:
        th.join()
    print(f"  [{label}] finished: {counter['done']} ok, {counter['fail']} failed "
          f"in {_fmt(time.time() - t0)}")


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="LLM-analyze rec inference results with GPT-5.6-sol.")
    ap.add_argument("--config", default="reproduced", choices=CONFIGS)
    ap.add_argument("--domain", default="Video_Games", choices=DOMAINS)
    ap.add_argument("--out-dir", default="./inference_analysis")
    ap.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT,
                    help="worker threads PER endpoint (total concurrency = #endpoints * this)")
    ap.add_argument("--endpoints", nargs="*", default=None,
                    help=f"subset of endpoints (default: {DEFAULT_ENDPOINTS})")
    ap.add_argument("--reasoning-effort", default=DEFAULT_REASONING_EFFORT,
                    choices=["minimal", "low", "medium", "high"])
    ap.add_argument("--limit", type=int, default=-1, help="cap #rows (pilot); <=0 = all")
    ap.add_argument("--shuffle", action="store_true", help="shuffle before applying --limit")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    endpoints = args.endpoints or list(DEFAULT_ENDPOINTS)
    bad = [e for e in endpoints if e not in ENDPOINTS]
    if bad:
        ap.error(f"unknown endpoint(s): {bad}")
    os.makedirs(args.out_dir, exist_ok=True)

    ds = load_dataset(HF_REPO, args.config, split=args.domain)
    idx = list(range(len(ds)))
    if args.shuffle:
        import random
        random.Random(args.seed).shuffle(idx)
    if args.limit > 0:
        idx = idx[:args.limit]

    out_path = os.path.join(args.out_dir, f"{args.config}.{args.domain}.analysis.jsonl")
    done = load_done_keys(out_path)

    tasks = []
    for i in idx:
        row_key = f"{args.config}/{args.domain}/{i}"
        if row_key not in done:
            tasks.append((row_key, i, ds[i]))
    print(f"[{args.config}/{args.domain}] {len(tasks)} to analyze "
          f"({len(done)} already done, {len(idx)} selected of {len(ds)})")

    def process(task, client):
        row_key, i, row = task
        user, rank = build_context(row, args.domain)
        labels = chat_json(client, SYSTEM_PROMPT, user, args.reasoning_effort)
        return {
            "row_key": row_key,
            "config": args.config,
            "domain": args.domain,
            "row_index": i,
            "target_sid": row["target_sid"],
            "target_title": row["target_title"],
            "exact_hit_rank": rank,          # 0 = miss (computed ground truth)
            "n_history": len(as_list(row["history_sid"])),
            **labels,                        # all GPT-5.6-sol judgments
        }

    run_pool(tasks, process, out_path,
             endpoints, args.per_endpoint, f"{args.config}/{args.domain}")
    jsonl_to_csv(out_path, out_path.replace(".jsonl", ".csv"))


if __name__ == "__main__":
    main()
