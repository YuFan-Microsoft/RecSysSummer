"""
LLM-based analysis of SID generative-rec inference results, to mine RL-training insights.

WHAT IT DOES
    Loads the per-example inference dump `yufan/rec_inference_results` (history, ground-truth
    target, top-10 constrained beam, chain-of-thought) and asks
  GPT-5.6-sol to label each example along dimensions that a rule-based / numeric pass cannot
    judge -- whether the target is inferable, whether beam diversity matches the user's interest
    structure, whether the CoT contains decision-relevant reasoning, and where the pipeline fails.
    Each labelled example carries one primary intervention so the aggregate tells us what to fix.

  Each example is scored against an anchored RUBRIC (every 1-5 level and every category is
  defined in SYSTEM_PROMPT) and, crucially, the judge first writes three GROUNDED PROSE
  analyses that quote the actual titles and give the logic, so the scores follow from a
  stated argument rather than being bare numbers:
    prose  : target_analysis (what the target is & how it relates to history),
             prediction_analysis (what the beam-10 bet on & how/why it hit or missed),
             cot_analysis (whether the reasoning found the right interest & is consistent)
    A. History and target       : history_interest_structure, target_relation, predictability
    B. Beam-10 slate            : best_beam_relation, beam_interest_coverage,
                                  beam_relevance_count, beam_redundancy, diversity_calibration
    C. CoT decision value       : cot_value, cot_identified_target_interest,
                                  cot_answer_consistency, cot_failure_mode
    D. Diagnosis                : pipeline_bottleneck, key_insight, primary_intervention

HOW TO RUN
  Prereq: `az login` (gpt5_endpoint_test.get_GPT5_client uses DefaultAzureCredential).

        # full baseline run: all 3 domains sequentially
        python gpt5_analyze_inference.py

    # pilot: 200 rows of one config/domain, all 3 endpoints, 8 workers/endpoint
        python gpt5_analyze_inference.py --domain Video_Games --limit 200

    # full run of one split
        python gpt5_analyze_inference.py --domain Office_Products

    # push throughput / restrict endpoints / highest reasoning effort
        python gpt5_analyze_inference.py --domain Industrial_and_Scientific \
        --per-endpoint 12 --reasoning-effort high \
        --endpoints feedscopilot-azureopenai-au feedscopilot-azureopenai-sweden

THROUGHPUT
    Every endpoint runs in parallel; each drives --per-endpoint client-bound worker processes,
  so total concurrency = #endpoints * per-endpoint, auto load-balanced through one queue.

RESUME (crash-safe)
  Each finished row is streamed to <out-dir>/<config>.<domain>.analysis.jsonl immediately.
  Rows are identified by their content (target_sid + history_sid), so re-running the SAME
  command resumes: done rows are skipped, failures retried.

OUTPUT
  <out-dir>/<config>.<domain>.analysis.jsonl   (raw, one JSON object per row)
  <out-dir>/<config>.<domain>.analysis.csv     (flattened, for aggregation / plotting)
"""

import argparse
import json
import multiprocessing as mp
import os
import queue
import re
import time

import pandas as pd
from datasets import load_dataset

from gpt5_endpoint_test import ENDPOINTS, get_GPT5_client

# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------
HF_REPO = "yufan/rec_inference_results"
CONFIGS = ["baseline"]
DOMAINS = ["Video_Games", "Office_Products", "Industrial_and_Scientific"]

MODEL = "gpt-5.6-sol"                     # judge model; deployed on the 3 endpoints below
DEFAULT_ENDPOINTS = [                     # only these carry gpt-5.6-sol
    "feedscopilot-azureopenai-au",
    "feedscopilot-azureopenai-eastus",
    "feedscopilot-azureopenai-sweden",
]

DEFAULT_PER_ENDPOINT = 8                  # worker processes per endpoint (total = #ep * this)
MAX_COMPLETION_TOKENS = 6000             # high-effort reasoning + prose analyses + JSON scores
DEFAULT_REASONING_EFFORT = "high"        # minimal|low|medium|high
MAX_TITLE_CHARS = 90                      # truncate each item title
MAX_HISTORY_ITEMS = 25                    # cap history length shown to the judge
MAX_COT_CHARS = 2000                      # truncate the chain-of-thought
LOG_EVERY_SEC = 10

SID_RE = re.compile(r"<[^>]+>")


# --------------------------------------------------------------------------------------
# Prompt: rubric-style judge. First force three GROUNDED PROSE analyses, then anchored
# scores derived from them. Single system + user; returns one strict-JSON object.
# --------------------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a meticulous recommender-systems research analyst auditing a SID-based generative recommendation model. Keep the diagnosis minimal: every label must distinguish a concrete failure source or intervention.

SETUP. The model reads a user's chronological interaction history and predicts the next item as a semantic ID (SID, format <a_XX><b_YY><c_ZZ>). It first writes one chain-of-thought (CoT), then conditions on that fixed CoT to decode the top-10 SIDs with constrained beam search. For ONE user you receive the history, ground-truth next item (target), top-10 beams, `exact_hit_rank` (the target's 1-based beam rank, or 0 if absent), and CoT.

GROUNDING RULES.
- Judge SEMANTICS from item TITLES; SIDs are opaque codes, use them ONLY to check exact identity or shared prefixes.
- Base every judgment ONLY on the provided history and titles. NEVER invent facts about an item beyond what its title implies.
- `exact_hit_rank` is authoritative for exact identity. If it is positive, `best_beam_relation` must be `exact`; judge semantic quality independently.
- Do not infer item popularity from titles. Do not claim that CoT causally improves accuracy; `cot_value` only measures whether its text contains supported, decision-relevant reasoning.

METHOD. Work in two passes. PASS 1 - write the three concise prose analyses below, quoting specific titles and explaining WHY. PASS 2 - assign the minimal diagnostic labels, each justified by the prose and internally consistent.

PROSE FIELDS (2-3 grounded sentences each; name real items).
- target_analysis: What interest does the target represent, what history evidence supports it, and how inferable is it?
- prediction_analysis: What interests did the beams allocate capacity to, what useful target relation did the closest beam have, and was the slate too narrow, appropriate, or too broad for this history?
- cot_analysis: Did CoT add a concrete decision beyond restating history, select the right interest, and agree with the emitted beams?

RUBRIC (anchors are binding).

[A. HISTORY AND TARGET]
history_interest_structure - the demand-side breadth that a good slate should reflect:
    concentrated = one clear interest dominates; extra unrelated breadth is not useful.
    dominant_with_secondary = one primary interest plus one or more credible secondary interests.
    multi_interest = multiple comparably supported, coherent interests.
    scattered = no stable interest structure; apparent breadth is mostly noise.
target_relation - single best fit of target vs history:
  repeat = target is (near-)identical to an item already in history (replenishment / re-engagement).
  same_subcategory = same fine-grained type/genre as recent items, different specific item.
    same_brand_or_series = same franchise, brand, series, or sequel.
  complementary = different type but functionally complements history (console->game, printer->ink, microscope->slides).
  broadening = a related but NEW sub-interest within the same broad domain.
  exploration = a genuine jump to an unrelated domain/interest.
predictability (1-5): 5 = history points almost directly at this item (next in series / obvious accessory / consumable refill). 4 = same sub-genre or brand as recent items; strong natural continuation. 3 = tied to a broad interest in history but many equally likely alternatives. 2 = weak, indirect link; a stretch. 1 = essentially unpredictable, no signal in history points to it.

[B. BEAM-10 SLATE]
best_beam_relation - the SINGLE closest beam to the target: exact = a beam equals the target SID. substitute = a near-interchangeable item that satisfies the SAME need (e.g. same title on another platform, same product different pack size). same_category = in the target's category but not a true substitute. complementary = complements the target but isn't it. unrelated = nothing close.
beam_interest_coverage (1-10): number of semantically distinct interests represented across the 10 beams, including off-profile interests.
beam_relevance_count (0-10): how many of the 10 beams are plausible next items given the history.
beam_redundancy (1-5): 1 = 10 clearly distinct items. 3 = a few near-duplicates (same title different platform, etc.). 5 = heavily redundant, most beams are minor variants of one item.
diversity_calibration - compare slate breadth against `history_interest_structure`, not against a universal preference for diversity:
    under_diversified = the slate collapses onto too few interests and misses a target/history-supported interest.
    calibrated = the slate's breadth and allocation match the supported interest structure.
    over_diversified = the slate spends capacity on weak or unsupported interests despite concentrated demand, reducing relevance.

[C. CoT DECISION VALUE]
cot_value - textual decision value, NOT a causal performance claim:
    useful = supported, specific reasoning selects an appropriate interest and informs the recommendation.
    partly_useful = identifies a relevant theme but remains generic, incomplete, or weakly discriminative.
    no_added_value = mostly paraphrases history or gives generic boilerplate without making a useful decision.
    harmful = selects the wrong interest, relies on unsupported claims, or materially misleads the recommendation.
cot_identified_target_interest (bool): did the reasoning name/derive the interest the target belongs to?
cot_answer_consistency (1-5): 5 = the reasoning's conclusion matches the emitted beams. 3 = partial alignment. 1 = concludes one thing, predicts another.
cot_failure_mode - single dominant defect: none, generic_restatement, no_decision, wrong_interest, unsupported_claim, or answer_mismatch.

[D. DIAGNOSIS]
pipeline_bottleneck - the SINGLE dominant bottleneck: target_noise = target is not fairly inferable. reasoning = CoT selects/motivates the wrong interest. beam_retrieval = CoT finds the right interest but beams fail to include it. beam_ranking = a strong candidate exists but is ranked poorly. slate_calibration = under/over-diversity is the main defect. exact_match_objective = semantically satisfactory substitutes exist but exact-match evaluation/reward treats them as total failures. none = no material defect.
key_insight: ONE sentence stating the most useful, evidence-backed takeaway from this example.
primary_intervention - the SINGLE best next action: downweight_noise, improve_reasoning, improve_beam_search, semantic_reward, increase_relevant_diversity, reduce_irrelevant_diversity, or keep_as_is.

OUTPUT. Return ONLY one JSON object (no markdown, no code fences, no text before/after), with EXACTLY these keys in this order:
{
  "target_analysis": string,
  "prediction_analysis": string,
  "cot_analysis": string,
    "history_interest_structure": string,
  "target_relation": string,
  "predictability": integer,
  "best_beam_relation": string,
  "beam_interest_coverage": integer,
  "beam_relevance_count": integer,
  "beam_redundancy": integer,
    "diversity_calibration": string,
    "cot_value": string,
  "cot_identified_target_interest": boolean,
  "cot_answer_consistency": integer,
    "cot_failure_mode": string,
    "pipeline_bottleneck": string,
  "key_insight": string,
    "primary_intervention": string
}"""

USER_TEMPLATE = """DOMAIN: {domain}

USER INTERACTION HISTORY (chronological; title [sid]):
{history_block}

GROUND-TRUTH NEXT ITEM (target):
{target_line}

MODEL TOP-10 BEAM PREDICTIONS (rank. title [sid]):
{beam_block}

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
    rank = exact_hit_rank(row["target_sid"], pred_sids)

    user = USER_TEMPLATE.format(
        domain=domain,
        history_block=history_block,
        target_line=target_line,
        beam_block=beam_block,
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


def row_key(row):
    """Content-derived id used only for resume/dedup (config/domain are implied by the file)."""
    return json.dumps([row["target_sid"], as_list(row["history_sid"])], ensure_ascii=False)


def load_done_keys(path):
    done = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(row_key(json.loads(line)))
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


def append_jsonl(path, obj):
    line = json.dumps(obj, ensure_ascii=False) + "\n"
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
# Concurrency engine (spawned client-bound processes over shared queues)
# --------------------------------------------------------------------------------------
def process_row(row, domain, reasoning_effort, client):
    user, rank = build_context(row, domain)
    labels = chat_json(client, SYSTEM_PROMPT, user, reasoning_effort)
    return {
        "history_sid": as_list(row["history_sid"]),
        "history_title": as_list(row["history_title"]),
        "target_sid": row["target_sid"],
        "target_title": row["target_title"],
        "predict_sid": as_list(row["predict_sid"]),
        "predict_title": as_list(row["predict_title"]),
        "exact_hit_rank": rank,
        "n_history": len(as_list(row["history_sid"])),
        **labels,
    }


def process_worker(task_queue, result_queue, endpoint, domain, reasoning_effort):
    try:
        client = get_GPT5_client(endpoint)
    except Exception as err:
        result_queue.put(("worker_error", endpoint, str(err)[:500]))
        return

    while True:
        task = task_queue.get()
        if task is None:
            return
        try:
            result_queue.put(("ok", process_row(task, domain, reasoning_effort, client)))
        except Exception as err:
            result_queue.put(("fail", endpoint, str(err)[:500]))


def run_pool(tasks, out_path, endpoints, per_endpoint, label, domain, reasoning_effort):
    total = len(tasks)
    if total == 0:
        print(f"  [{label}] nothing to do")
        return

    ctx = mp.get_context("spawn")
    task_queue = ctx.Queue()
    result_queue = ctx.Queue()
    worker_specs = [endpoint for endpoint in endpoints for _ in range(per_endpoint)]
    workers = [
        ctx.Process(
            target=process_worker,
            args=(task_queue, result_queue, endpoint, domain, reasoning_effort),
            daemon=True,
        )
        for endpoint in worker_specs
    ]
    for worker in workers:
        worker.start()
    for task in tasks:
        task_queue.put(task)
    for _ in workers:
        task_queue.put(None)

    t0 = time.time()
    last_log = 0.0
    done = 0
    failed = 0

    def emit(force=False):
        nonlocal last_log
        now = time.time()
        if not force and now - last_log < LOG_EVERY_SEC:
            return
        last_log = now
        finished = done + failed
        elapsed = now - t0
        rate = finished / elapsed if elapsed > 0 else 0.0
        eta = (total - finished) / rate if rate > 0 else 0.0
        print(f"  [{label}] {finished}/{total} ({finished / total * 100:.1f}%) | "
              f"{rate:.2f} rows/s | elapsed {_fmt(elapsed)} | ETA {_fmt(eta)} | "
              f"{failed} failed", flush=True)

    print(f"  [{label}] {total} tasks / {len(endpoints)} endpoints x {per_endpoint} "
          f"= {len(workers)} processes")
    try:
        while done + failed < total:
            try:
                result = result_queue.get(timeout=1)
            except queue.Empty:
                if not any(worker.is_alive() for worker in workers):
                    raise RuntimeError(
                        f"all worker processes exited with {total - done - failed} tasks unfinished"
                    )
                continue

            kind = result[0]
            if kind == "ok":
                append_jsonl(out_path, result[1])
                done += 1
            elif kind == "fail":
                failed += 1
                print(f"  [{label}] FAIL on {result[1]}: {result[2][:150]}", flush=True)
            else:
                print(f"  [{label}] WORKER FAIL on {result[1]}: {result[2][:150]}", flush=True)
            emit(force=(done + failed == total))
    finally:
        for worker in workers:
            worker.join(timeout=5)
            if worker.is_alive():
                worker.terminate()
        task_queue.close()
        result_queue.close()

    print(f"  [{label}] finished: {done} ok, {failed} failed "
          f"in {_fmt(time.time() - t0)}")


# --------------------------------------------------------------------------------------
# Per-domain analysis and entry point
# --------------------------------------------------------------------------------------
def analyze_domain(args, endpoints, domain):
    ds = load_dataset(HF_REPO, args.config, split=domain)
    idx = list(range(len(ds)))
    if args.shuffle:
        import random
        random.Random(args.seed).shuffle(idx)
    if args.limit > 0:
        idx = idx[:args.limit]

    out_path = os.path.join(args.out_dir, f"{args.config}.{domain}.analysis.jsonl")
    done = load_done_keys(out_path)

    tasks = []
    for i in idx:
        row = ds[i]
        if row_key(row) not in done:
            tasks.append(row)
    print(f"[{args.config}/{domain}] {len(tasks)} to analyze "
          f"({len(done)} already done, {len(idx)} selected of {len(ds)})")

    run_pool(
        tasks,
        out_path,
        endpoints,
        args.per_endpoint,
        f"{args.config}/{domain}",
        domain,
        args.reasoning_effort,
    )
    jsonl_to_csv(out_path, out_path.replace(".jsonl", ".csv"))


def main():
    ap = argparse.ArgumentParser(description="LLM-analyze rec inference results with GPT-5.6-sol.")
    ap.add_argument("--config", default="baseline", choices=CONFIGS)
    ap.add_argument(
        "--domain",
        dest="domains",
        nargs="+",
        default=list(DOMAINS),
        choices=DOMAINS,
        help="one or more domains (default: all three)",
    )
    ap.add_argument("--out-dir", default="./inference_analysis")
    ap.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT,
                    help="worker processes PER endpoint (total concurrency = #endpoints * this)")
    ap.add_argument("--endpoints", nargs="*", default=None,
                    help=f"subset of endpoints (default: {DEFAULT_ENDPOINTS})")
    ap.add_argument("--reasoning-effort", default=DEFAULT_REASONING_EFFORT,
                    choices=["minimal", "low", "medium", "high"])
    ap.add_argument("--limit", type=int, default=-1, help="cap #rows per domain (pilot); <=0 = all")
    ap.add_argument("--shuffle", action="store_true", help="shuffle each domain before applying --limit")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    endpoints = args.endpoints or list(DEFAULT_ENDPOINTS)
    bad = [e for e in endpoints if e not in ENDPOINTS]
    if bad:
        ap.error(f"unknown endpoint(s): {bad}")
    os.makedirs(args.out_dir, exist_ok=True)

    for domain in args.domains:
        analyze_domain(args, endpoints, domain)


if __name__ == "__main__":
    main()
