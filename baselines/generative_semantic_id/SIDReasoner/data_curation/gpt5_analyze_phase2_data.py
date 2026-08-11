"""
Audit SIDReasoner Phase-2 reasoning-activation training data with GPT-5.6-sol.

WHAT IT DOES
  Loads Video_Games_reasoning from yufan/recsys-genrec-dataset together with the
  matching catalog. For every training row it evaluates:

    * how predictable the target is from the user history;
        * whether the reasoning hallucinates unsupported preferences or attributes;
        * whether it is logically consistent and aligned with the target interest;
        * whether low-predictability targets cause strained target-overfit reasoning;
        * aggregate failure insights and guidance for rewriting the full dataset.

    Deterministic checks run before the LLM judge for exact SID/title leakage,
    missing reasoning, and encoding corruption.
  The judge receives those checks as evidence but independently audits semantics.

HOW TO RUN
  Prereq: run `az login`; gpt5_endpoint_test.py supplies Azure clients.

    # Pilot a sample before paying for the full audit.
    python gpt5_analyze_phase2_data.py --limit 200 --shuffle

    # Audit the full Video_Games domain, 8 processes per endpoint.
    python gpt5_analyze_phase2_data.py

    # Use selected endpoints.
    python gpt5_analyze_phase2_data.py --per-endpoint 12 \
        --endpoints feedscopilot-azureopenai-au feedscopilot-azureopenai-sweden

RESUME
  Results are appended immediately. Re-running the same command skips rows whose
  category, user/history, target, and reasoning content have already been audited.
  Failed rows are not written and are retried on the next run.

OUTPUT
  <out-dir>/Video_Games.phase2_reasoning.analysis.jsonl
  <out-dir>/Video_Games.phase2_reasoning.analysis.csv
  <out-dir>/Video_Games.phase2_reasoning.summary.json
"""

import argparse
import ast
from collections import Counter
import hashlib
import json
import multiprocessing as mp
import os
import queue
import re
import time

import pandas as pd
from datasets import load_dataset


# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------
HF_REPO = "yufan/recsys-genrec-dataset"
CATEGORIES = ["Video_Games"]

MODEL = "gpt-5.6-sol"
DEFAULT_ENDPOINTS = [
    "feedscopilot-azureopenai-au",
    "feedscopilot-azureopenai-eastus",
    "feedscopilot-azureopenai-jp",
    "feedscopilot-azureopenai-sweden",
]
DEFAULT_PER_ENDPOINT = 8
DEFAULT_REASONING_EFFORT = "high"
MAX_COMPLETION_TOKENS = 8000
MAX_API_ATTEMPTS = 3

MAX_HISTORY_ITEMS = 25
MAX_HISTORY_DESCRIPTION_CHARS = 500
MAX_TARGET_DESCRIPTION_CHARS = 800
MAX_REASONING_CHARS = 6000
MAX_TITLE_CHARS = 140
LOG_EVERY_SEC = 10

SID_RE = re.compile(r"<[^<>\s]+>")


# --------------------------------------------------------------------------------------
# Judge prompt and strict output contract
# --------------------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a meticulous recommender-systems data auditor. You are judging ONE training row for a SID-based model's Phase-2 reasoning-activation SFT.

TRAINING TASK. At inference time the model sees only chronological history SIDs. It must produce a target-blind reasoning trace inside <think>...</think>, followed by the next-item SID. The audited `reasoning_path` was generated offline with the target available only as hidden guidance. It was required to reason from history, refer to items only by SID, avoid naming or predicting a specific next item, avoid mentioning the reference/target, and end with calibrated likely interests.

YOUR CENTRAL JOB. Separate these two questions:
1. TARGET PREDICTABILITY: How strongly does history alone support the held-out target?
2. REASONING QUALITY: Would the reasoning still be justified if the target were hidden?

Do not reward a trace merely because it resembles the target. A trace that precisely selects an unpredictable target interest may exhibit hindsight bias or privileged-target leakage. Conversely, a target can be noisy while a broad, honest trace remains useful supervision.

GROUNDING RULES.
- Judge item semantics from titles and descriptions. SIDs are opaque identity codes; shared SID prefixes are not semantic evidence.
- Use only the supplied history and catalog text. Never invent product attributes, user demographics, sentiment, purchases, or motivations.
- Distinguish an observed interaction from inferred preference. One interaction is weak evidence unless its semantics are unusually specific.
- Recency, repetition, coherent transitions, series/brand continuity, and functional complementarity are valid evidence when explicitly present.
- A statement is unsupported if no supplied history item supports it, even if it happens to match the target.
- Exact target title/SID/reference mention is explicit leakage. Semantic overfitting to a weakly predictable target can be strong leakage even without a literal mention.
- The deterministic checks are evidence, not authoritative semantic labels. Correct them when context proves them misleading.

METHOD. Work internally in four passes, then return only JSON.
PASS 1: Infer the history-supported interests without using the target.
PASS 2: Reveal the target; identify its interest, supporting/contradicting history evidence, plausible alternatives, and predictability.
PASS 3: Audit every reasoning claim for hallucination and audit the full trace for logical consistency and target-interest alignment.
PASS 4: Especially when target_predictability <= 2, decide whether the trace honestly reflects uncertainty or strains/backfits the history toward the target, then extract lessons for rewriting the data.

RUBRIC.

[A. TARGET INSIGHT]
target_relation (single closest relation):
  repeat = target is identical or nearly identical to history.
  same_subcategory = same fine-grained type/genre/use case.
  same_brand_or_series = explicit brand, franchise, series, sequel, or edition continuity.
  complementary = a different item with a direct functional relationship.
  broadening = a new sub-interest inside a supported broad domain.
  exploration = no meaningful history-supported relation.
target_predictability (1-5):
  5 = history nearly determines this target (repeat, obvious next installment/refill/accessory).
  4 = strong natural continuation with specific recent or repeated evidence.
  3 = supported broad interest, but many alternatives are equally plausible.
  2 = weak or indirect connection; substantial guesswork is required.
  1 = essentially unpredictable from history.

[B. PROCESS-REWARD SIGNALS]
hallucination_severity (1-5, HIGHER IS WORSE):
    1 = every material item/user-preference claim is supported by supplied history.
    2 = one minor extrapolation that does not drive the conclusion.
    3 = several weak inferences or one unsupported claim that affects the conclusion.
    4 = major unsupported preferences/attributes drive the recommendation direction.
    5 = the trace is largely fabricated, contradicts evidence, or appears derived from privileged target information.
target_interest_alignment (1-5, descriptive rather than automatically good):
    1 = reasoning interest is unrelated to the target.
    2 = only a weak broad-domain overlap.
    3 = same broad interest but not the target's meaningful sub-interest.
    4 = identifies the correct target sub-interest/use case.
    5 = closely matches the target's specific interest/continuation.
logical_consistency (1-5, HIGHER IS BETTER):
    1 = central claims/conclusion contradict each other or the chronology.
    2 = major logical jump or contradiction.
    3 = understandable but contains a weak transition or unsupported leap.
    4 = coherent with only a minor gap.
    5 = each conclusion follows consistently from stated history evidence.
target_overfit_risk (1-5, HIGHER IS WORSE):
    1 = reasoning direction follows from history independently of the target.
    2 = mostly history-driven with mild target-compatible selectivity.
    3 = suspiciously selects one weakly supported direction among many alternatives.
    4 = strains/cherry-picks history to match a low-predictability target.
    5 = explicit target leakage or clear backward construction from the target.
training_harm_risk (1-5, HIGHER IS WORSE):
    1 = safe process supervision.
    2 = minor noise unlikely to teach a bad reasoning pattern.
    3 = mixed supervision requiring revision before use.
    4 = likely teaches hallucination, inconsistency, or target-overfit shortcuts.
    5 = strongly harmful supervision or an essentially unlearnable target/history pair.

[C. DIAGNOSTIC SYNTHESIS]
dominant_failure_mode: one of none, target_noise, insufficient_history, hallucination, logical_inconsistency, target_misalignment, target_overfit, or malformed_reasoning.
rewrite_guidance: a concrete lesson for regenerating this kind of reasoning without hallucination, inconsistency, or target backfitting. Focus on the new data-generation policy, not whether to retain this row.

CONSISTENCY RULES.
- High target_interest_alignment is not inherently good. When target_predictability <= 2, alignment >= 4 requires explicit history evidence; otherwise target_overfit_risk must be >= 4.
- Any material unsupported claim must raise hallucination_severity. Unsupported target-specific claims must also raise target_overfit_risk.
- hallucination_severity >= 4 or logical_consistency <= 2 implies training_harm_risk >= 4.
- When the history/target pair itself is weak, use target_noise or insufficient_history as dominant_failure_mode; otherwise diagnose the reasoning defect.

Return ONLY one JSON object, no markdown or text outside it, with EXACTLY these keys in this order:
{
    "target_insight": string,
    "reasoning_audit": string,
    "low_predictability_risk_analysis": string,
  "target_relation": string,
  "target_predictability": integer,
    "hallucination_severity": integer,
    "target_interest_alignment": integer,
    "logical_consistency": integer,
    "target_overfit_risk": integer,
    "training_harm_risk": integer,
        "dominant_failure_mode": string,
  "key_insight": string,
        "rewrite_guidance": string
}"""

USER_TEMPLATE = """CATEGORY: {category}

USER INTERACTION HISTORY (chronological; title [SID]; catalog evidence):
{history_block}

HELD-OUT TARGET (use only after independently characterizing history):
{target_block}

PHASE-2 REASONING_PATH TO AUDIT:
{reasoning}

DETERMINISTIC PRE-CHECKS:
{rule_checks}

Audit the row with the four-pass method. In `target_insight`, identify the target interest and exact evidence for/against predictability. In `reasoning_audit`, quote supported and hallucinated claims and explain logical transitions. In `low_predictability_risk_analysis`, directly answer whether the reasoning is strained or harmful, especially when target_predictability <= 2. In `rewrite_guidance`, state what the new data-generation process should do differently. Return only the strict JSON object."""

REQUIRED_KEYS = [
    "target_insight",
    "reasoning_audit",
    "low_predictability_risk_analysis",
    "target_relation",
    "target_predictability",
    "hallucination_severity",
    "target_interest_alignment",
    "logical_consistency",
    "target_overfit_risk",
    "training_harm_risk",
    "dominant_failure_mode",
    "key_insight",
    "rewrite_guidance",
]

SCORE_KEYS = {
    "target_predictability",
    "hallucination_severity",
    "target_interest_alignment",
    "logical_consistency",
    "target_overfit_risk",
    "training_harm_risk",
}

ENUM_VALUES = {
    "target_relation": {
        "repeat", "same_subcategory", "same_brand_or_series", "complementary",
        "broadening", "exploration"
    },
    "dominant_failure_mode": {
        "none", "target_noise", "insufficient_history", "hallucination",
        "logical_inconsistency", "target_misalignment", "target_overfit",
        "malformed_reasoning"
    },
}

TEXT_KEYS = set(REQUIRED_KEYS) - SCORE_KEYS - set(ENUM_VALUES)


# --------------------------------------------------------------------------------------
# Parsing, catalog, and deterministic checks
# --------------------------------------------------------------------------------------
def _fmt(seconds):
    seconds = int(max(0, seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"


def as_list(value):
    """Normalize HF arrays and legacy stringified Python lists."""
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("[", "(")):
            try:
                parsed = ast.literal_eval(stripped)
                if isinstance(parsed, (list, tuple)):
                    return list(parsed)
            except (SyntaxError, ValueError):
                pass
    return [value]


def _clip(value, limit):
    text = "" if value is None else str(value).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _catalog_description(row):
    description = row.get("description", "")
    parsed = as_list(description)
    candidates = [str(value).strip() for value in parsed if str(value).strip()]
    if candidates:
        return max(candidates, key=len)
    detailed = row.get("detailed_description", "")
    return "" if detailed is None else str(detailed).strip()


def load_catalog(category, hf_repo):
    dataset = load_dataset(hf_repo, f"{category}_catalog", split="train")
    catalog = {}
    for row in dataset:
        sid = str(row["sid"])
        catalog[sid] = {
            "title": "" if row.get("title") is None else str(row["title"]),
            "brand": "" if row.get("brand") is None else str(row["brand"]),
            "description": _catalog_description(row),
        }
    return catalog


def normalized_row(row, catalog):
    history_sids = [str(value) for value in as_list(row.get("history_item_sid"))]
    history_titles = [str(value) for value in as_list(row.get("history_item_title"))]
    history = []
    for index in range(max(len(history_sids), len(history_titles))):
        sid = history_sids[index] if index < len(history_sids) else "(missing SID)"
        catalog_title = catalog.get(sid, {}).get("title", "")
        title = history_titles[index] if index < len(history_titles) else catalog_title
        history.append({"sid": sid, "title": title or "(missing title)"})

    target_sid = "" if row.get("item_sid") is None else str(row["item_sid"])
    target_title = "" if row.get("item_title") is None else str(row["item_title"])
    if not target_title:
        target_title = catalog.get(target_sid, {}).get("title", "")

    return {
        "history": history,
        "target_sid": target_sid,
        "target_title": target_title,
        "reasoning": "" if row.get("reasoning_path") is None else str(row["reasoning_path"]),
    }


def _literal_title_mentions(reasoning, titles):
    lowered = reasoning.casefold()
    mentions = []
    for title in titles:
        title = str(title).strip()
        if len(title) >= 5 and title.casefold() in lowered:
            mentions.append(title)
    return sorted(set(mentions))


def deterministic_checks(row, catalog):
    normalized = normalized_row(row, catalog)
    history = normalized["history"]
    history_sids = [item["sid"] for item in history]
    target_sid = normalized["target_sid"]
    target_title = normalized["target_title"]
    reasoning = normalized["reasoning"].strip()

    sid_mentions = SID_RE.findall(reasoning)
    unique_sid_mentions = list(dict.fromkeys(sid_mentions))
    history_sid_set = set(history_sids)
    target_sid_mentioned = bool(target_sid and target_sid in unique_sid_mentions)
    non_history_sids = sorted(
        sid for sid in set(unique_sid_mentions)
        if sid not in history_sid_set and sid != target_sid
    )
    target_title_mentions = _literal_title_mentions(reasoning, [target_title])

    return {
        "reasoning_empty": not bool(reasoning),
        "replacement_character_count": reasoning.count("\ufffd"),
        "history_length": len(history),
        "history_target_exact_repeat": target_sid in history_sid_set,
        "target_sid_mentioned": target_sid_mentioned,
        "non_history_sid_mentions": non_history_sids,
        "target_title_mentioned": bool(target_title_mentions),
    }


def _item_line(item, catalog, index=None, description_limit=MAX_HISTORY_DESCRIPTION_CHARS):
    sid = item["sid"]
    title = _clip(item["title"], MAX_TITLE_CHARS)
    meta = catalog.get(sid, {})
    brand = _clip(meta.get("brand", ""), 80)
    description = _clip(meta.get("description", ""), description_limit)
    prefix = f"{index}. " if index is not None else ""
    parts = [f"{prefix}{title} [{sid}]"]
    if brand:
        parts.append(f"brand={brand}")
    if description:
        parts.append(f"description={description}")
    return " | ".join(parts)


def build_context(row, category, catalog, checks):
    normalized = normalized_row(row, catalog)
    shown_history = normalized["history"][-MAX_HISTORY_ITEMS:]
    history_block = "\n".join(
        _item_line(item, catalog, index + 1)
        for index, item in enumerate(shown_history)
    ) or "(empty history)"

    target_item = {
        "sid": normalized["target_sid"],
        "title": normalized["target_title"] or "(missing title)",
    }
    target_block = _item_line(
        target_item,
        catalog,
        description_limit=MAX_TARGET_DESCRIPTION_CHARS,
    )
    reasoning = _clip(normalized["reasoning"], MAX_REASONING_CHARS) or "(empty reasoning)"
    rule_checks = json.dumps(checks, ensure_ascii=False, indent=2)
    return USER_TEMPLATE.format(
        category=category,
        history_block=history_block,
        target_block=target_block,
        reasoning=reasoning,
        rule_checks=rule_checks,
    )


# --------------------------------------------------------------------------------------
# JSON parsing and validation
# --------------------------------------------------------------------------------------
def parse_json(text):
    if not text:
        raise ValueError("empty judge reply")
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in reply: {text[:160]!r}")
    return json.loads(stripped[start:end + 1])


def validate_labels(labels):
    if not isinstance(labels, dict):
        raise ValueError("judge reply is not a JSON object")
    missing = [key for key in REQUIRED_KEYS if key not in labels]
    extra = [key for key in labels if key not in REQUIRED_KEYS]
    if missing or extra:
        raise ValueError(f"schema mismatch; missing={missing}, extra={extra}")

    for key in SCORE_KEYS:
        value = labels[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"{key} must be an integer in [1, 5], got {value!r}")
    for key, allowed in ENUM_VALUES.items():
        if labels[key] not in allowed:
            raise ValueError(f"{key} must be one of {sorted(allowed)}, got {labels[key]!r}")
    for key in TEXT_KEYS:
        if not isinstance(labels[key], str) or not labels[key].strip():
            raise ValueError(f"{key} must be a non-empty string")
    return labels


def chat_json(client, user, reasoning_effort):
    last_error = None
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user},
                ],
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort=reasoning_effort,
            )
            labels = parse_json(response.choices[0].message.content or "")
            return validate_labels(labels)
        except Exception as error:
            last_error = error
            if attempt < MAX_API_ATTEMPTS:
                time.sleep(min(2 ** (attempt - 1), 4))
    raise RuntimeError(f"judge failed after {MAX_API_ATTEMPTS} attempts: {last_error}")


# --------------------------------------------------------------------------------------
# Row processing and crash-safe output
# --------------------------------------------------------------------------------------
def row_analysis_id(row, category):
    payload = [
        category,
        row.get("user_id"),
        row.get("history_item_sid"),
        row.get("item_sid"),
        row.get("reasoning_path"),
    ]
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_done_keys(path):
    done = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    done.add(json.loads(line)["analysis_id"])
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


def append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def process_row(task, category, catalog, reasoning_effort, client):
    source_index, row = task
    normalized = normalized_row(row, catalog)
    checks = deterministic_checks(row, catalog)
    user = build_context(row, category, catalog, checks)
    labels = chat_json(client, user, reasoning_effort)

    return {
        "analysis_id": row_analysis_id(row, category),
        "source_index": source_index,
        "category": category,
        "user_id": row.get("user_id"),
        "item_id": row.get("item_id"),
        "history_item_sid": [item["sid"] for item in normalized["history"]],
        "history_item_title": [item["title"] for item in normalized["history"]],
        "item_sid": normalized["target_sid"],
        "item_title": normalized["target_title"],
        "reasoning_path": normalized["reasoning"],
        "reasoning_question": row.get("reasoning_question"),
        "reasoning_reference": row.get("reasoning_reference"),
        "rule_checks": checks,
        **labels,
    }


def process_worker(
    task_queue,
    result_queue,
    endpoint,
    category,
    catalog,
    reasoning_effort,
):
    try:
        from gpt5_endpoint_test import get_GPT5_client

        client = get_GPT5_client(endpoint)
    except Exception as error:
        result_queue.put(("worker_error", endpoint, str(error)[:500]))
        return

    while True:
        task = task_queue.get()
        if task is None:
            return
        try:
            result = process_row(task, category, catalog, reasoning_effort, client)
            result_queue.put(("ok", result))
        except Exception as error:
            result_queue.put(("fail", endpoint, task[0], str(error)[:1000]))


def run_pool(tasks, out_path, endpoints, per_endpoint, category, catalog, reasoning_effort):
    total = len(tasks)
    if total == 0:
        print(f"  [{category}] nothing to do")
        return

    context = mp.get_context("spawn")
    task_queue = context.Queue()
    result_queue = context.Queue()
    worker_specs = [endpoint for endpoint in endpoints for _ in range(per_endpoint)]
    workers = [
        context.Process(
            target=process_worker,
            args=(
                task_queue,
                result_queue,
                endpoint,
                category,
                catalog,
                reasoning_effort,
            ),
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

    started = time.time()
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
        elapsed = now - started
        rate = finished / elapsed if elapsed > 0 else 0.0
        eta = (total - finished) / rate if rate > 0 else 0.0
        print(
            f"  [{category}] {finished}/{total} ({finished / total * 100:.1f}%) | "
            f"{rate:.2f} rows/s | elapsed {_fmt(elapsed)} | ETA {_fmt(eta)} | "
            f"{failed} failed",
            flush=True,
        )

    print(
        f"  [{category}] {total} tasks / {len(endpoints)} endpoints x {per_endpoint} "
        f"= {len(workers)} processes"
    )
    try:
        while done + failed < total:
            try:
                result = result_queue.get(timeout=1)
            except queue.Empty:
                if not any(worker.is_alive() for worker in workers):
                    raise RuntimeError(
                        f"all workers exited with {total - done - failed} tasks unfinished"
                    )
                continue

            kind = result[0]
            if kind == "ok":
                append_jsonl(out_path, result[1])
                done += 1
            elif kind == "fail":
                failed += 1
                print(
                    f"  [{category}] FAIL row {result[2]} on {result[1]}: "
                    f"{result[3][:220]}",
                    flush=True,
                )
            else:
                print(
                    f"  [{category}] WORKER FAIL on {result[1]}: {result[2][:220]}",
                    flush=True,
                )
            emit(force=(done + failed == total))
    finally:
        for worker in workers:
            worker.join(timeout=5)
            if worker.is_alive():
                worker.terminate()
        task_queue.close()
        result_queue.close()

    print(
        f"  [{category}] finished: {done} ok, {failed} failed "
        f"in {_fmt(time.time() - started)}"
    )


# --------------------------------------------------------------------------------------
# CSV and aggregate diagnostics
# --------------------------------------------------------------------------------------
def load_jsonl_records(path):
    if not os.path.exists(path):
        return []
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def write_csv(records, path):
    if not records:
        return
    pd.json_normalize(records).to_csv(path, index=False)
    print(f"  wrote {path} ({len(records)} rows)")


def write_summary(records, path):
    if not records:
        return

    score_means = {}
    for key in sorted(SCORE_KEYS):
        values = [row[key] for row in records if isinstance(row.get(key), int)]
        if values:
            score_means[key] = round(sum(values) / len(values), 4)

    categorical_keys = [
        "target_relation",
        "dominant_failure_mode",
    ]
    distributions = {
        key: dict(Counter(row.get(key) for row in records if row.get(key) is not None))
        for key in categorical_keys
    }

    boolean_rule_values = {}
    rule_keys = sorted({
        key
        for row in records
        for key, value in row.get("rule_checks", {}).items()
        if isinstance(value, bool)
    })
    for key in rule_keys:
        values = [
            row["rule_checks"][key]
            for row in records
            if isinstance(row.get("rule_checks", {}).get(key), bool)
        ]
        if values:
            boolean_rule_values[key] = {
                "true_count": sum(values),
                "true_rate": round(sum(values) / len(values), 4),
            }

    low_predictability = [row for row in records if row.get("target_predictability", 5) <= 2]
    low_predictability_scores = {}
    for key in sorted(SCORE_KEYS):
        values = [row[key] for row in low_predictability if isinstance(row.get(key), int)]
        if values:
            low_predictability_scores[key] = round(sum(values) / len(values), 4)
    low_predictability_high_harm = sum(
        row.get("training_harm_risk", 0) >= 4 for row in low_predictability
    )
    low_predictability_high_overfit = sum(
        row.get("target_overfit_risk", 0) >= 4 for row in low_predictability
    )

    summary = {
        "rows": len(records),
        "score_means": score_means,
        "distributions": distributions,
        "low_predictability_subset": {
            "rows": len(low_predictability),
            "rate": round(len(low_predictability) / len(records), 4),
            "score_means": low_predictability_scores,
            "high_training_harm_count": low_predictability_high_harm,
            "high_training_harm_rate": round(
                low_predictability_high_harm / len(low_predictability), 4
            ) if low_predictability else 0.0,
            "high_target_overfit_count": low_predictability_high_overfit,
            "high_target_overfit_rate": round(
                low_predictability_high_overfit / len(low_predictability), 4
            ) if low_predictability else 0.0,
            "dominant_failure_mode": dict(Counter(
                row.get("dominant_failure_mode") for row in low_predictability
            )),
        },
        "deterministic_boolean_rates": boolean_rule_values,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(f"  wrote {path}")


# --------------------------------------------------------------------------------------
# Category runner and CLI
# --------------------------------------------------------------------------------------
def analyze_category(args, endpoints, category):
    reasoning_data = load_dataset(
        args.hf_repo,
        f"{category}_reasoning",
        split=args.split,
    )
    catalog = load_catalog(category, args.hf_repo)

    indices = list(range(len(reasoning_data)))
    if args.shuffle:
        import random
        random.Random(args.seed).shuffle(indices)
    if args.limit > 0:
        indices = indices[:args.limit]

    out_path = os.path.join(args.out_dir, f"{category}.phase2_reasoning.analysis.jsonl")
    done = load_done_keys(out_path)
    tasks = []
    for index in indices:
        row = reasoning_data[index]
        if row_analysis_id(row, category) not in done:
            tasks.append((index, row))

    print(
        f"[{category}] {len(tasks)} to audit "
        f"({len(done)} already done, {len(indices)} selected of {len(reasoning_data)})"
    )
    run_pool(
        tasks,
        out_path,
        endpoints,
        args.per_endpoint,
        category,
        catalog,
        args.reasoning_effort,
    )

    records = load_jsonl_records(out_path)
    write_csv(records, out_path.replace(".jsonl", ".csv"))
    write_summary(records, out_path.replace(".analysis.jsonl", ".summary.json"))


def main():
    parser = argparse.ArgumentParser(
        description="Audit SIDReasoner Phase-2 reasoning data with GPT-5.6-sol."
    )
    parser.add_argument(
        "--category",
        dest="categories",
        nargs="+",
        default=list(CATEGORIES),
        choices=CATEGORIES,
        help="category to audit (Video_Games only)",
    )
    parser.add_argument("--hf-repo", default=HF_REPO)
    parser.add_argument("--split", default="train")
    parser.add_argument("--out-dir", default="./phase2_data_analysis")
    parser.add_argument(
        "--per-endpoint",
        type=int,
        default=DEFAULT_PER_ENDPOINT,
        help="worker processes per endpoint",
    )
    parser.add_argument(
        "--endpoints",
        nargs="*",
        default=None,
        help=f"endpoint subset (default: {DEFAULT_ENDPOINTS})",
    )
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        choices=["minimal", "low", "medium", "high"],
    )
    parser.add_argument("--limit", type=int, default=-1, help="rows per category; <=0 = all")
    parser.add_argument("--shuffle", action="store_true", help="shuffle before applying --limit")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if args.per_endpoint <= 0:
        parser.error("--per-endpoint must be positive")
    endpoints = args.endpoints or list(DEFAULT_ENDPOINTS)
    if not endpoints:
        parser.error("at least one endpoint is required")
    try:
        from gpt5_endpoint_test import ENDPOINTS as available_endpoints
    except ModuleNotFoundError as error:
        parser.error(
            f"missing Azure client dependency ({error.name}); install `openai` and "
            "`azure-identity` from requirements.txt"
        )
    bad = [endpoint for endpoint in endpoints if endpoint not in available_endpoints]
    if bad:
        parser.error(f"unknown endpoint(s): {bad}")

    os.makedirs(args.out_dir, exist_ok=True)
    for category in args.categories:
        analyze_category(args, endpoints, category)


if __name__ == "__main__":
    main()