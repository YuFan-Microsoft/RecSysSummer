"""
Regenerate SIDReasoner Phase-1 enrichment data with GPT-5.4 (Azure OpenAI).

WHAT IT DOES
  Two enrichment tracks, each a two-stage GPT-5.4 pipeline whose prompts are copied
  verbatim from `cases of data and prompts.md` (Part 2):

    item : <Cat>_catalog   -> detailed_description        (Stage 1)
                              sid_interleaved_narrative    (Stage 2)
    user : <Cat>_reasoning -> reasoning_path              (Stage 1)
                              integrated_narrative         (Stage 2)

HOW TO RUN
  Prereq: `gpt5_endpoint_test.py` (same folder) supplies ENDPOINTS + get_GPT5_client,
  which authenticate to Azure via DefaultAzureCredential. Run `az login` first, then:

    # one category, both tracks, ALL endpoints, 8 workers/endpoint
    python gpt5_regenerate_phase1_data.py --category Video_Games --track both

    # smoke test on 20 rows
    python gpt5_regenerate_phase1_data.py --category Video_Games --track item --limit 20

    # push throughput higher / restrict endpoints
    python gpt5_regenerate_phase1_data.py --category Office_Products --track user \
        --per-endpoint 16 \
        --endpoints feedscopilot-azureopenai-eastus2 feedscopilot-azureopenai-sweden

  Run all three categories by launching it three times (--category ...).

THROUGHPUT
  Every GPT-5.4 endpoint runs in parallel; each endpoint drives --per-endpoint
  client-bound worker threads, so total concurrency = #endpoints * per-endpoint,
  auto load-balanced through one shared task queue.

RESUME (crash-safe)
  Each finished row is streamed to  <out-dir>/<Category>.{catalog,reasoning}_regen.jsonl
  right away. To resume after a crash/Ctrl-C, just re-run the SAME command: rows already
  written (keyed by item_id / row_key) are skipped and any failed rows are retried.

OUTPUT
  <out-dir>/<Category>.catalog_regen.{jsonl,csv}       (item track)
  <out-dir>/<Category>.reasoning_regen.{jsonl,csv}     (user track)
  <out-dir>/<Category>.integrated_narrative.csv        (user track, training-ready)
"""

import argparse
import ast
import json
import os
import queue
import threading
import time

import pandas as pd
from datasets import load_dataset

from gpt5_endpoint_test import ENDPOINTS, get_GPT5_client

# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------
HF_REPO = "yufan/recsys-genrec-dataset"
CATEGORIES = ["Video_Games", "Office_Products", "Industrial_and_Scientific"]
MODEL = "gpt-5.4"                 # the only model we use; available on every endpoint

DEFAULT_PER_ENDPOINT = 8          # worker threads per endpoint (total = #endpoints * this)

# Long completions (10+ sentence narratives) -> generous cap.
MAX_COMPLETION_TOKENS = 1600
REASONING_EFFORT = "low"          # minimal|low|medium|high
MAX_DESC_CHARS = 4000             # truncate very long raw descriptions to bound cost
LOG_EVERY_SEC = 10                # throttle the speed/ETA progress line to <= once per N s

_write_lock = threading.Lock()


# --------------------------------------------------------------------------------------
# Prompts (verbatim from `cases of data and prompts.md`, Part 2). The doc presents each
# prompt as a SINGLE block with no separate system role, so each is sent as one user
# message; persona lines that appear in the doc body are kept inline. Item-centric fields
# are limited to title/brand/description (the HF catalog has no category/features columns).
# --------------------------------------------------------------------------------------
ITEM_STAGE1_PROMPT = """Based on the following product information, generate a comprehensive analysis:

{meta_block}

Please provide:

1. A detailed 2-3 sentence description
2. 2-3 main use cases
3. Target audience
4. 3-5 key features summary
5. 5-8 related keywords"""

ITEM_STAGE2_PROMPT = """You are a senior copywriter preparing an in-depth narrative for a product dossier.

- Source Meta Information:
{meta_block}
- Product Semantic Identifier (use this exact string whenever you mention the product): {sid}
- Enrichment from Stage 1:
{stage1}

Task:

1. Combine ALL of the information above into a single rich and coherent narrative of at least 10 sentences. Include every important fact, Detailed Description, scenario, Target Audience, audience insight, feature highlight, and keyword context that appears in the sources.
2. Every reference to the product must use the identifier {sid}. Do NOT use the title or any other alias.
3. Ensure the result reads like a rich, flowing paragraph (no bullet points, headings, or enumerations). Maintain a professional and descriptive tone suitable for a product catalog.
4. Highlight how {sid} fits different use cases, why its features matter, and draw from both original data and first-stage enhancements without omitting details."""

USER_STAGE1_PROMPT = """You are an expert recommendation system analyst analyzing user behavior patterns.

Your goal is to reason through the user's history and predict what the item the user would be interested in, explaining your reasoning process from your analytical perspective in first person.

Given user interaction history, item descriptions, and reference next item, produce a concise first-person reasoning from an analyst's perspective to predict what kind of item the user may like in the next interactions. The reference item is only for internal guidance — reason entirely based on interaction history and item descriptions. Never mention or discuss the reference item in your reasoning. Write as a genuine real-time prediction analyzing user behavior patterns.

- User Interaction history: {history_titles}
- Reference next item: {target_title}
- Item Descriptions:
{item_descriptions}

OUTPUT REQUIREMENTS:

1. Output ONLY reasoning monologue in first person (I) as an analyst. Keep concise but detailed. Vary sentence structures to avoid repetition.
2. Analyze general user preferences (genres, themes, attributes, motivations) and engagement patterns based on history.
3. Express potential interests or tendencies rather than deterministic conclusions or single outcomes.
4. Adapt depth to history length: brief key observations for short histories; step-by-step tracing of interest shifts for longer ones. Base predictions on observed patterns.
5. CRITICAL: Always use ONLY the SID format when referring to items. Never use titles, names, or `Item SID:` prefixes.
6. Never mention 'reference item' or imply knowledge of the target. Reason as if predicting blindly.
7. Start directly with reasoning. Do NOT predict a specific next item. End with a non-deterministic summary of likely interests (e.g., `may enjoy`, `tends to prefer`).

Your Reasoning:"""

USER_STAGE2_PROMPT = """Integrate the following information into a single, coherent, natural narrative paragraph:

- User interaction history (chronological item titles & SIDs):
{history_pairs}
- Reference next item (Title & SID): {target_title} — {target_sid}
- Reasoning path from Stage 1:
{stage1}

OUTPUT REQUIREMENTS:

1. Start your narrative by explicitly reciting the full 'User Interaction history (chronological item SIDs)' sequence EXACTLY as provided, but use varied and natural opening phrases. Ensure the full sequence is included to establish context.
2. Write in a natural, flowing style — avoid mechanical or formulaic language in the subsequent analysis. Make it read like a genuine narrative.
3. Preserve the essential reasoning insights from the reasoning path — don't just summarize, but naturally incorporate the key analytical points and logic.
4. When mentioning any item, ALWAYS use its SID (format: `<a_XXX><b_YYY><c_ZZZ>`) — never use item titles or names.
5. Keep the narrative natural and engaging.

Integrated Narrative:"""


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def _fmt(seconds):
    """Format a duration as H:MM:SS."""
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _maybe_literal(value):
    """Parse a stringified python list/scalar; return as-is on failure."""
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str) and value.strip().startswith(("[", "(")):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value
    return value


def process_description(description, title):
    """Mirror data_Qwen3._process_description: pick the longest non-empty entry, else title."""
    if not description:
        return title
    desc = _maybe_literal(description)
    if isinstance(desc, list):
        non_empty = [d for d in desc if isinstance(d, str) and d.strip()]
        return max(non_empty, key=len) if non_empty else title
    if isinstance(desc, str):
        return desc if desc.strip() else title
    return title


def build_item_meta_block(title, brand, description):
    """Assemble the metadata block for item-centric prompts (title/brand/description only)."""
    lines = [f"Title: {title}"]
    if brand and str(brand).strip():
        lines.append(f"Brand: {brand}")
    lines.append(f"Description: {description[:MAX_DESC_CHARS]}")
    return "\n".join(lines)


def chat(client, prompt):
    """Single GPT-5.4 chat completion. Returns stripped assistant text.

    The corpus-enrichment prompts in `cases of data and prompts.md` are documented
    as a single block with no separate system role, so we send one user message.
    """
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        reasoning_effort=REASONING_EFFORT,
    )
    return (resp.choices[0].message.content or "").strip()


def load_done_keys(path, key):
    """Read an existing JSONL output and collect already-generated keys (for resuming)."""
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
            os.fsync(fh.fileno())   # land every finished row on disk (crash-safe resume)


# --------------------------------------------------------------------------------------
# Item-centric track
# --------------------------------------------------------------------------------------
def _item_process(row, client):
    sid = row["sid"]
    title = row["title"]
    brand = row.get("brand", "")
    description = process_description(row.get("description", ""), title)
    meta_block = build_item_meta_block(title, brand, description)

    stage1 = chat(client, ITEM_STAGE1_PROMPT.format(meta_block=meta_block))
    stage2 = chat(client, ITEM_STAGE2_PROMPT.format(meta_block=meta_block, sid=sid, stage1=stage1))

    return {
        "item_id": row["item_id"],
        "sid": sid,
        "title": title,
        "brand": brand,
        "description": row.get("description", ""),
        "detailed_description": stage1,          # Stage 1 output
        "sid_interleaved_narrative": stage2,     # Stage 2 output
    }


def regen_item(category, out_path, endpoints, per_endpoint, limit):
    ds = load_dataset(HF_REPO, f"{category}_catalog", split="train")
    if limit > 0:
        ds = ds.select(range(min(limit, len(ds))))

    done = load_done_keys(out_path, "item_id")
    tasks = [r for r in ds if r["item_id"] not in done]
    print(f"[item] {category}: {len(tasks)} to generate ({len(done)} already done)")
    run_pool(tasks, _item_process, out_path, endpoints, per_endpoint, "item")


# --------------------------------------------------------------------------------------
# User-centric track
# --------------------------------------------------------------------------------------
def _build_sid2desc(category):
    """Map combined-SID -> processed description from the catalog (for Stage-1 descriptions)."""
    cat = load_dataset(HF_REPO, f"{category}_catalog", split="train")
    sid2title, sid2desc = {}, {}
    for r in cat:
        sid2title[r["sid"]] = r["title"]
        sid2desc[r["sid"]] = process_description(r.get("description", ""), r["title"])
    return sid2title, sid2desc


def regen_user(category, out_path, endpoints, per_endpoint, limit):
    src = load_dataset(HF_REPO, f"{category}_reasoning", split="train")
    if limit > 0:
        src = src.select(range(min(limit, len(src))))
    sid2title, sid2desc = _build_sid2desc(category)

    done = load_done_keys(out_path, "row_key")
    tasks = []
    for i, r in enumerate(src):
        key = f"{r['user_id']}::{i}"
        if key not in done:
            tasks.append((key, r))
    print(f"[user] {category}: {len(tasks)} to generate ({len(done)} already done)")

    def process(task, client):
        row_key, row = task

        history_sids = _maybe_literal(row["history_item_sid"])
        history_titles = _maybe_literal(row["history_item_title"])
        if not isinstance(history_sids, list):
            history_sids = [history_sids]
        if not isinstance(history_titles, list):
            history_titles = [history_titles]

        target_sid = row["item_sid"]
        target_title = row["item_title"]

        history_titles_str = ", ".join(history_titles)
        desc_lines, pair_lines = [], []
        for sid, ttl in zip(history_sids, history_titles):
            desc = sid2desc.get(sid, sid2title.get(sid, ttl))
            desc_lines.append(f"{sid} -> {ttl}: {desc[:MAX_DESC_CHARS]}")
            pair_lines.append(f"{ttl} ({sid})")
        item_descriptions = "\n".join(desc_lines)
        history_pairs = "\n".join(pair_lines)

        stage1 = chat(client, USER_STAGE1_PROMPT.format(
            history_titles=history_titles_str,
            target_title=target_title,
            item_descriptions=item_descriptions,
        ))
        stage2 = chat(client, USER_STAGE2_PROMPT.format(
            history_pairs=history_pairs,
            target_title=target_title,
            target_sid=target_sid,
            stage1=stage1,
        ))

        return {
            "row_key": row_key,
            "user_id": row["user_id"],
            "history_item_title": row["history_item_title"],
            "item_title": target_title,
            "history_item_sid": row["history_item_sid"],
            "item_sid": target_sid,
            "reasoning_path": stage1,            # Stage 1 output
            "integrated_narrative": stage2,      # Stage 2 output
        }

    run_pool(tasks, process, out_path, endpoints, per_endpoint, "user")


# --------------------------------------------------------------------------------------
# Concurrency engine + CSV export
# --------------------------------------------------------------------------------------
def run_pool(tasks, process_fn, out_path, endpoints, per_endpoint, label):
    """Drain `tasks` through a pool of client-bound workers for maximum throughput.

    One worker thread per (endpoint, slot); each holds its own GPT-5.4 client and
    pulls tasks from a shared queue -> total concurrency = len(endpoints) * per_endpoint,
    auto load-balanced. Every finished row is appended to `out_path` immediately, so a
    crash is resumed by simply re-running the same command (done keys skipped, failed
    rows retried).
    """
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
        rate = d / elapsed if elapsed > 0 else 0.0          # avg rows/sec so far
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
            except Exception as err:  # keep the pool alive; resume/re-run retries it
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


def jsonl_to_csv(jsonl_path, csv_path):
    if not os.path.exists(jsonl_path):
        return
    records = [json.loads(l) for l in open(jsonl_path, "r", encoding="utf-8")]
    pd.DataFrame(records).to_csv(csv_path, index=False)
    print(f"  wrote {csv_path} ({len(records)} rows)")


# --------------------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Regenerate SIDReasoner Phase-1 data with GPT-5.4.")
    ap.add_argument("--category", default="Video_Games", choices=CATEGORIES)
    ap.add_argument("--track", default="both", choices=["item", "user", "both"])
    ap.add_argument("--out-dir", default="./regen_phase1")
    ap.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT,
                    help="worker threads PER endpoint (total concurrency = #endpoints * this)")
    ap.add_argument("--endpoints", nargs="*", default=None,
                    help="subset of endpoints to use (default: all of ENDPOINTS)")
    ap.add_argument("--limit", type=int, default=-1, help="cap #rows (for a smoke test)")
    args = ap.parse_args()

    endpoints = args.endpoints or list(ENDPOINTS)
    bad = [e for e in endpoints if e not in ENDPOINTS]
    if bad:
        ap.error(f"unknown endpoint(s): {bad}")
    os.makedirs(args.out_dir, exist_ok=True)

    if args.track in ("item", "both"):
        item_jsonl = os.path.join(args.out_dir, f"{args.category}.catalog_regen.jsonl")
        regen_item(args.category, item_jsonl, endpoints, args.per_endpoint, args.limit)
        jsonl_to_csv(item_jsonl, item_jsonl.replace(".jsonl", ".csv"))

    if args.track in ("user", "both"):
        user_jsonl = os.path.join(args.out_dir, f"{args.category}.reasoning_regen.jsonl")
        regen_user(args.category, user_jsonl, endpoints, args.per_endpoint, args.limit)
        # training reads a CSV (ReasoningActivationDataset / SidTextInterleaveSequenceDataset:
        # history_item_sid, item_sid, reasoning_path, integrated_narrative).
        jsonl_to_csv(user_jsonl, user_jsonl.replace(".jsonl", ".csv"))
        jsonl_to_csv(user_jsonl,
                     os.path.join(args.out_dir, f"{args.category}.integrated_narrative.csv"))


if __name__ == "__main__":
    main()
