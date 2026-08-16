"""Audit target-interest hits and SID grounding in sampled reasoning traces.

The audit is intentionally stricter than broad category overlap. A predicted
interest is a strict semantic hit only when it captures the target's defining
fine-grained need, subcategory, franchise continuation, or use case.

Prerequisites:
  * ``az login`` for the Azure OpenAI endpoints.
  * Access to ``yufan/recsys-genrec-dataset`` for Video_Games catalog evidence.

Example:
    python gpt5_analyze_reasoning_interest_hits.py --limit 500 --per-endpoint 2
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import multiprocessing as mp
import os
import queue
import random
import re
import time
from typing import Any
from urllib.request import urlretrieve

from datasets import load_dataset

from gpt5_endpoint_test import ENDPOINTS, get_GPT5_client


MODEL = "gpt-5.4"
DEFAULT_INPUT = (
    "https://huggingface.co/datasets/yufan/rec_rl_checkpoints/resolve/main/"
    "results_analysis/yufan_constrained_sampling_process.jsonl"
)
DEFAULT_CATALOG_REPO = "yufan/recsys-genrec-dataset"
DEFAULT_CATALOG_CONFIG = "Video_Games_catalog"
MAX_API_ATTEMPTS = 4
MAX_COMPLETION_TOKENS = 7000
MAX_DESCRIPTION_CHARS = 500
MAX_REASONING_CHARS = 7000
LOG_EVERY_SECONDS = 10

TARGET_MATCH_VALUES = {"exact_or_near", "specific", "broad", "adjacent", "none"}
ALIGNMENT_VALUES = {"aligned", "partially_aligned", "misaligned", "unverifiable"}
RELATION_VALUES = {
    "repeat",
    "same_subcategory",
    "same_brand_or_series",
    "complementary",
    "broadening",
    "exploration",
}
MODE_VALUES = {"exploit", "explore", "other"}

SYSTEM_PROMPT = """You are a meticulous evaluator of recommendation reasoning traces.
The model saw only opaque history SIDs and generated a history summary plus predicted future
interests. You receive catalog titles/descriptions solely to audit the generated semantics.

Evaluate two independent questions:
1. TARGET INTEREST HIT: Does each predicted future interest capture the held-out target's
   actual semantic need? Do not count generic domain overlap as a useful hit.
2. HISTORY SID GROUNDING: For every distinct history SID, are all attributes attached to that
   SID in the reasoning supported by its catalog title, brand, or description?

TARGET MATCH LABELS:
- exact_or_near: identifies the target itself, its explicit franchise/series continuation, or
  an almost interchangeable need. This is a strict hit.
- specific: captures the target's defining fine-grained subcategory, genre, function, or use
  case without identifying the exact item. This is also a strict hit.
- broad: shares only a broad category or coarse theme; it would retrieve many irrelevant items.
- adjacent: a plausible complement or one-step transfer, but not the target's own interest.
- none: unrelated or contradictory.

HISTORY ALIGNMENT LABELS:
- aligned: every material semantic claim attached to the SID is supported by catalog evidence.
- partially_aligned: the core identity/function is right, but at least one secondary detail is
  weak, overstated, or unsupported.
- misaligned: the core item characterization is wrong or contradicted.
- unverifiable: the reasoning is too vague, the SID is not semantically explained, or supplied
  catalog text is insufficient to verify it.

HALLUCINATION RULES:
- material_hallucination=true only for a concrete unsupported or contradicted item attribute
  that changes the inferred preference/direction. Generic preference inference belongs in the
  interest audit, not automatically in the SID audit.
- Missing catalog evidence is not proof of hallucination; use unverifiable unless the title or
  other evidence contradicts the claim.
- SIDs and shared SID prefixes are opaque and provide no semantic evidence.
- Audit all claims attached to a SID anywhere in the trace, including grouped summary claims
  and evidence cited in future-interest lines.
- Repeated occurrences of one SID receive one combined audit.

Assess the history-supported target relation and target predictability independently. A trace
can hit an unpredictable target due to chance or hindsight; do not inflate predictability merely
because the generated interest matches.

Return ONLY one JSON object with exactly these top-level keys:
{
  "target_interest": "concise target need grounded in target catalog evidence",
  "target_relation": "repeat|same_subcategory|same_brand_or_series|complementary|broadening|exploration",
  "target_predictability": 1,
  "interest_audits": [
    {
      "interest_index": 1,
      "mode": "exploit|explore|other",
      "target_match": "exact_or_near|specific|broad|adjacent|none",
      "matched_target_attributes": ["concise attribute"],
      "rationale": "concise evidence-based comparison"
    }
  ],
  "history_sid_audits": [
    {
      "history_index": 1,
      "sid": "exact supplied SID",
      "explanation_present": true,
      "alignment": "aligned|partially_aligned|misaligned|unverifiable",
      "material_hallucination": false,
      "unsupported_or_wrong_claims": [],
      "rationale": "concise catalog-grounded assessment"
    }
  ],
  "history_grounding_summary": "concise overall assessment"
}

target_predictability is an integer from 1 (no meaningful history support) to 5 (nearly
determined by repeat/series/very specific continuity). Return exactly one interest audit per
supplied interest and exactly one history audit per supplied distinct history SID, preserving
their indices."""

USER_TEMPLATE = """HISTORY CATALOG GROUND TRUTH (chronological distinct SIDs):
{history}

HELD-OUT TARGET CATALOG GROUND TRUTH:
{target}

PARSED PREDICTED INTERESTS:
{interests}

FULL GENERATED REASONING TRACE:
{reasoning}

Audit every supplied interest and every distinct history SID. Return only strict JSON."""


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def catalog_description(row: dict[str, Any]) -> str:
    descriptions = [str(value).strip() for value in as_list(row.get("description"))]
    descriptions = [value for value in descriptions if value]
    if descriptions:
        return max(descriptions, key=len)
    return str(row.get("detailed_description") or "").strip()


def load_catalog(repo: str, config: str) -> dict[str, dict[str, str]]:
    dataset = load_dataset(repo, config, split="train")
    catalog = {}
    for row in dataset:
        sid = str(row["sid"])
        catalog[sid] = {
            "title": str(row.get("title") or "").strip(),
            "brand": str(row.get("brand") or "").strip(),
            "description": catalog_description(row),
        }
    return catalog


def resolve_input(source: str, cache_path: str) -> str:
    if not source.startswith(("http://", "https://")):
        return source
    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
    if not os.path.exists(cache_path):
        print(f"Downloading {source} -> {cache_path}", flush=True)
        urlretrieve(source, cache_path)
    return cache_path


def load_jsonl(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def extract_interests(reasoning: str) -> list[dict[str, Any]]:
    match = re.search(
        r"<future_interests>(.*?)(?:</future_interests>|</think>|$)",
        reasoning,
        flags=re.DOTALL | re.IGNORECASE,
    )
    section = match.group(1) if match else reasoning
    lines = [line.strip()[2:].strip() for line in section.splitlines() if line.strip().startswith("- ")]
    if not lines:
        collapsed = re.sub(r"\s+", " ", section).strip()
        lines = [collapsed] if collapsed else []
    interests = []
    for index, text in enumerate(lines, start=1):
        mode_match = re.match(r"\[(exploit|explore)\]", text, flags=re.IGNORECASE)
        mode = mode_match.group(1).lower() if mode_match else "other"
        interests.append({"interest_index": index, "mode": mode, "text": text})
    return interests


def distinct_history(row: dict[str, Any]) -> list[dict[str, Any]]:
    sids = [str(value) for value in as_list(row.get("history_sid_list"))]
    titles = [str(value) for value in as_list(row.get("history_title_list"))]
    seen = set()
    history = []
    for position, sid in enumerate(sids):
        if sid in seen:
            continue
        seen.add(sid)
        positions = [index + 1 for index, value in enumerate(sids) if value == sid]
        title = titles[position] if position < len(titles) else ""
        history.append(
            {
                "history_index": len(history) + 1,
                "sid": sid,
                "positions": positions,
                "row_title": title,
            }
        )
    return history


def clipped(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "..."


def format_catalog_item(
    sid: str,
    fallback_title: str,
    catalog: dict[str, dict[str, str]],
) -> str:
    item = catalog.get(sid, {})
    title = item.get("title") or fallback_title or "(missing title)"
    brand = item.get("brand") or "(missing brand)"
    description = clipped(item.get("description") or "", MAX_DESCRIPTION_CHARS)
    description = description or "(missing description; do not infer unsupported details)"
    return f"title={title} | SID={sid} | brand={brand} | description={description}"


def build_task(row: dict[str, Any], seed: int) -> dict[str, Any]:
    source_index = int(row["source_index"])
    task_id = hashlib.sha256(
        f"interest-sid-audit-v1:{seed}:{source_index}:{row['item_sid']}".encode("utf-8")
    ).hexdigest()[:20]
    interests = extract_interests(str(row.get("generated_reasoning_path") or ""))
    history = distinct_history(row)
    return {
        "task_id": task_id,
        "source_index": source_index,
        "user_id": row.get("user_id"),
        "history": history,
        "target_sid": str(row["item_sid"]),
        "target_title": str(row.get("item_title") or ""),
        "target_type": (
            "repeat" if row["item_sid"] in as_list(row.get("history_sid_list")) else "novel"
        ),
        "reasoning": str(row.get("generated_reasoning_path") or ""),
        "interests": interests,
        "prediction_beam_10": [str(value) for value in as_list(row.get("prediction_beam_10"))],
    }


def sample_tasks(rows: list[dict[str, Any]], limit: int, seed: int) -> list[dict[str, Any]]:
    if limit > len(rows):
        raise ValueError(f"Requested {limit} rows from a dataset containing {len(rows)}")
    selected = random.Random(seed).sample(rows, limit)
    return [build_task(row, seed) for row in selected]


def paired_tasks(
    rows: list[dict[str, Any]],
    source_indices_path: str,
    seed: int,
) -> list[dict[str, Any]]:
    source_indices = [
        int(row["source_index"])
        for row in load_jsonl(source_indices_path)
    ]
    if len(source_indices) != len(set(source_indices)):
        raise ValueError(f"Duplicate source_index values in {source_indices_path}")
    rows_by_source = {int(row["source_index"]): row for row in rows}
    missing = [source_index for source_index in source_indices if source_index not in rows_by_source]
    if missing:
        raise ValueError(f"Missing source_index values in input: {missing[:10]}")
    return [build_task(rows_by_source[source_index], seed) for source_index in source_indices]


def build_prompt(task: dict[str, Any], catalog: dict[str, dict[str, str]]) -> str:
    history_lines = []
    for item in task["history"]:
        evidence = format_catalog_item(item["sid"], item["row_title"], catalog)
        history_lines.append(
            f"{item['history_index']}. positions={item['positions']} | {evidence}"
        )
    target = format_catalog_item(task["target_sid"], task["target_title"], catalog)
    interests = "\n".join(
        f"{item['interest_index']}. mode={item['mode']} | {item['text']}"
        for item in task["interests"]
    ) or "(no parseable predicted interests)"
    return USER_TEMPLATE.format(
        history="\n".join(history_lines) or "(empty history)",
        target=target,
        interests=interests,
        reasoning=clipped(task["reasoning"], MAX_REASONING_CHARS),
    )


def parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match is None:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("Judge response is not a JSON object")
    return value


def validate_judgment(value: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    required = {
        "target_interest",
        "target_relation",
        "target_predictability",
        "interest_audits",
        "history_sid_audits",
        "history_grounding_summary",
    }
    if set(value) != required:
        raise ValueError(f"Top-level schema mismatch: expected={required}, actual={set(value)}")
    if value["target_relation"] not in RELATION_VALUES:
        raise ValueError(f"Invalid target_relation: {value['target_relation']!r}")
    if not isinstance(value["target_predictability"], int) or not 1 <= value["target_predictability"] <= 5:
        raise ValueError("target_predictability must be an integer in [1, 5]")
    for key in ("target_interest", "history_grounding_summary"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"{key} must be a nonempty string")

    interest_audits = value["interest_audits"]
    expected_interest_indices = [item["interest_index"] for item in task["interests"]]
    if not isinstance(interest_audits, list) or [item.get("interest_index") for item in interest_audits] != expected_interest_indices:
        raise ValueError("interest_audits must preserve every supplied interest index")
    for audit in interest_audits:
        if set(audit) != {
            "interest_index", "mode", "target_match", "matched_target_attributes", "rationale"
        }:
            raise ValueError("Interest audit keys do not match schema")
        if audit["mode"] not in MODE_VALUES or audit["target_match"] not in TARGET_MATCH_VALUES:
            raise ValueError(f"Invalid interest audit enum: {audit!r}")
        if not isinstance(audit["matched_target_attributes"], list):
            raise ValueError("matched_target_attributes must be a list")
        if not isinstance(audit["rationale"], str) or not audit["rationale"].strip():
            raise ValueError("Interest rationale must be nonempty")

    history_audits = value["history_sid_audits"]
    expected_history_indices = [item["history_index"] for item in task["history"]]
    if not isinstance(history_audits, list) or [item.get("history_index") for item in history_audits] != expected_history_indices:
        raise ValueError("history_sid_audits must preserve every supplied history index")
    expected_sids = {item["history_index"]: item["sid"] for item in task["history"]}
    for audit in history_audits:
        if set(audit) != {
            "history_index", "sid", "explanation_present", "alignment",
            "material_hallucination", "unsupported_or_wrong_claims", "rationale",
        }:
            raise ValueError("History SID audit keys do not match schema")
        if audit["sid"] != expected_sids[audit["history_index"]]:
            raise ValueError("History SID audit changed the supplied SID")
        if audit["alignment"] not in ALIGNMENT_VALUES:
            raise ValueError(f"Invalid history alignment: {audit['alignment']!r}")
        if not isinstance(audit["explanation_present"], bool) or not isinstance(audit["material_hallucination"], bool):
            raise ValueError("History audit flags must be booleans")
        if not isinstance(audit["unsupported_or_wrong_claims"], list):
            raise ValueError("unsupported_or_wrong_claims must be a list")
        if not isinstance(audit["rationale"], str) or not audit["rationale"].strip():
            raise ValueError("History rationale must be nonempty")
    return value


def judge(
    client: Any,
    task: dict[str, Any],
    catalog: dict[str, dict[str, str]],
    reasoning_effort: str,
) -> dict[str, Any]:
    prompt = build_prompt(task, catalog)
    last_error = None
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort=reasoning_effort,
            )
            parsed = parse_json_object(response.choices[0].message.content or "")
            return validate_judgment(parsed, task)
        except Exception as error:
            last_error = error
            if attempt < MAX_API_ATTEMPTS:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"GPT judge failed after {MAX_API_ATTEMPTS} attempts: {last_error}")


def worker(
    task_queue: Any,
    result_queue: Any,
    endpoint: str,
    catalog: dict[str, dict[str, str]],
    reasoning_effort: str,
) -> None:
    try:
        client = get_GPT5_client(endpoint)
    except Exception as error:
        result_queue.put(("worker_error", endpoint, str(error)[:1000]))
        return
    while True:
        task = task_queue.get()
        if task is None:
            return
        try:
            judgment = judge(client, task, catalog, reasoning_effort)
            result_queue.put(("ok", task, judgment, endpoint))
        except Exception as error:
            result_queue.put(("fail", task["task_id"], endpoint, str(error)[:1000]))


def load_done(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    done = set()
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                done.add(json.loads(line)["task_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def append_jsonl(path: str, value: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def output_record(
    task: dict[str, Any],
    judgment: dict[str, Any],
    endpoint: str,
) -> dict[str, Any]:
    strict_matches = {"exact_or_near", "specific"}
    broad_matches = strict_matches | {"broad"}
    interest_audits = judgment["interest_audits"]
    history_audits = judgment["history_sid_audits"]
    return {
        "task_id": task["task_id"],
        "source_index": task["source_index"],
        "user_id": task["user_id"],
        "target_sid": task["target_sid"],
        "target_title": task["target_title"],
        "target_type": task["target_type"],
        "prediction_beam_10": task["prediction_beam_10"],
        "beam_exact_hit": task["target_sid"] in task["prediction_beam_10"],
        "reasoning": task["reasoning"],
        "parsed_interests": task["interests"],
        "distinct_history": task["history"],
        **judgment,
        "any_strict_interest_hit": any(
            item["target_match"] in strict_matches for item in interest_audits
        ),
        "any_broad_interest_hit": any(
            item["target_match"] in broad_matches for item in interest_audits
        ),
        "any_history_material_hallucination": any(
            item["material_hallucination"] for item in history_audits
        ),
        "endpoint": endpoint,
        "model": MODEL,
    }


def run_pool(
    tasks: list[dict[str, Any]],
    output: str,
    endpoints: list[str],
    per_endpoint: int,
    catalog: dict[str, dict[str, str]],
    reasoning_effort: str,
) -> None:
    done_ids = load_done(output)
    pending = [task for task in tasks if task["task_id"] not in done_ids]
    if not pending:
        print("Nothing to do", flush=True)
        return

    context = mp.get_context("spawn")
    task_queue = context.Queue()
    result_queue = context.Queue()
    worker_endpoints = [endpoint for endpoint in endpoints for _ in range(per_endpoint)]
    workers = [
        context.Process(
            target=worker,
            args=(task_queue, result_queue, endpoint, catalog, reasoning_effort),
            daemon=True,
        )
        for endpoint in worker_endpoints
    ]
    for process in workers:
        process.start()
    for task in pending:
        task_queue.put(task)
    for _ in workers:
        task_queue.put(None)

    started = time.time()
    last_log = 0.0
    completed = 0
    failed = 0
    print(
        f"{len(pending)} tasks / {len(endpoints)} endpoints x {per_endpoint} "
        f"= {len(workers)} processes",
        flush=True,
    )
    try:
        while completed + failed < len(pending):
            try:
                message = result_queue.get(timeout=1)
            except queue.Empty:
                if not any(process.is_alive() for process in workers):
                    raise RuntimeError("All workers exited before completing the task queue")
                continue
            if message[0] == "ok":
                append_jsonl(output, output_record(message[1], message[2], message[3]))
                completed += 1
            elif message[0] == "fail":
                failed += 1
                print(f"FAIL {message[1]} on {message[2]}: {message[3]}", flush=True)
            else:
                print(f"WORKER ERROR {message[1]}: {message[2]}", flush=True)

            now = time.time()
            finished = completed + failed
            if now - last_log >= LOG_EVERY_SECONDS or finished == len(pending):
                last_log = now
                elapsed = now - started
                rate = finished / elapsed if elapsed else 0.0
                eta = (len(pending) - finished) / rate if rate else math.inf
                print(
                    f"{finished}/{len(pending)} | {rate:.2f} rows/s | "
                    f"ETA {eta / 60:.1f} min | failed={failed}",
                    flush=True,
                )
    finally:
        for process in workers:
            process.join(timeout=5)
        for process in workers:
            if process.is_alive():
                process.terminate()


def rate_summary(numerator: int, denominator: int) -> dict[str, Any]:
    if denominator == 0:
        return {"numerator": numerator, "denominator": denominator, "rate": None, "wilson_95": None}
    rate = numerator / denominator
    z = 1.959963984540054
    scale = 1 + z * z / denominator
    center = (rate + z * z / (2 * denominator)) / scale
    half = z * math.sqrt(rate * (1 - rate) / denominator + z * z / (4 * denominator * denominator)) / scale
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": round(rate, 6),
        "wilson_95": [round(max(0.0, center - half), 6), round(min(1.0, center + half), 6)],
    }


def metric(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [bool(row[key]) for row in rows if key in row]
    return rate_summary(sum(values), len(values))


def stratum_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    interest_audits = [audit for row in rows for audit in row["interest_audits"]]
    history_audits = [audit for row in rows for audit in row["history_sid_audits"]]
    strict = {"exact_or_near", "specific"}
    broad = strict | {"broad"}
    explained = [audit for audit in history_audits if audit["explanation_present"]]
    return {
        "rows": len(rows),
        "row_any_strict_interest_hit": metric(rows, "any_strict_interest_hit"),
        "row_any_broad_interest_hit": metric(rows, "any_broad_interest_hit"),
        "beam_exact_hit": metric(rows, "beam_exact_hit"),
        "row_any_history_material_hallucination": metric(
            rows, "any_history_material_hallucination"
        ),
        "interest_level_strict_hit": rate_summary(
            sum(audit["target_match"] in strict for audit in interest_audits), len(interest_audits)
        ),
        "interest_level_broad_hit": rate_summary(
            sum(audit["target_match"] in broad for audit in interest_audits), len(interest_audits)
        ),
        "interest_target_match_distribution": dict(
            Counter(audit["target_match"] for audit in interest_audits)
        ),
        "exploit_strict_hit": rate_summary(
            sum(audit["target_match"] in strict for audit in interest_audits if audit["mode"] == "exploit"),
            sum(audit["mode"] == "exploit" for audit in interest_audits),
        ),
        "explore_strict_hit": rate_summary(
            sum(audit["target_match"] in strict for audit in interest_audits if audit["mode"] == "explore"),
            sum(audit["mode"] == "explore" for audit in interest_audits),
        ),
        "history_explanation_coverage": rate_summary(len(explained), len(history_audits)),
        "history_sid_material_hallucination": rate_summary(
            sum(audit["material_hallucination"] for audit in explained), len(explained)
        ),
        "history_alignment_distribution": dict(
            Counter(audit["alignment"] for audit in history_audits)
        ),
        "target_relation_distribution": dict(Counter(row["target_relation"] for row in rows)),
        "target_predictability_mean": round(
            sum(row["target_predictability"] for row in rows) / len(rows), 6
        ) if rows else None,
    }


def summarize(output: str, summary_path: str, seed: int, requested_limit: int) -> dict[str, Any]:
    rows = load_jsonl(output)
    strata = {
        "all": rows,
        "repeat_target": [row for row in rows if row["target_type"] == "repeat"],
        "novel_target": [row for row in rows if row["target_type"] == "novel"],
        "beam_hit": [row for row in rows if row["beam_exact_hit"]],
        "beam_miss": [row for row in rows if not row["beam_exact_hit"]],
        "predictability_1_2": [row for row in rows if row["target_predictability"] <= 2],
        "predictability_3": [row for row in rows if row["target_predictability"] == 3],
        "predictability_4_5": [row for row in rows if row["target_predictability"] >= 4],
    }
    summary = {
        "model": MODEL,
        "seed": seed,
        "requested_sample_rows": requested_limit,
        "completed_rows": len(rows),
        "definitions": {
            "strict_interest_hit": "target_match in {exact_or_near, specific}",
            "broad_interest_hit": "strict hit or broad category/theme overlap",
            "history_sid_hallucination_denominator": "distinct explained history SIDs",
        },
        "strata": {
            name: stratum_summary(selected)
            for name, selected in strata.items()
            if selected
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(summary_path)), exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--input-cache", default="/tmp/yufan_constrained_sampling_process.jsonl")
    parser.add_argument("--catalog-repo", default=DEFAULT_CATALOG_REPO)
    parser.add_argument("--catalog-config", default=DEFAULT_CATALOG_CONFIG)
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--source-indices-from",
        help="JSONL whose source_index values define an exact paired sample; overrides --limit",
    )
    parser.add_argument("--per-endpoint", type=int, default=2)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="low")
    args = parser.parse_args()

    endpoints = args.endpoints or list(ENDPOINTS)
    unknown = [endpoint for endpoint in endpoints if endpoint not in ENDPOINTS]
    if unknown:
        parser.error(f"Unknown endpoints: {unknown}")
    if args.limit < 1 or args.per_endpoint < 1:
        parser.error("--limit and --per-endpoint must be positive")

    input_path = resolve_input(args.input, args.input_cache)
    rows = load_jsonl(input_path)
    tasks = (
        paired_tasks(rows, args.source_indices_from, args.seed)
        if args.source_indices_from
        else sample_tasks(rows, args.limit, args.seed)
    )
    print(f"Loading catalog {args.catalog_repo}/{args.catalog_config}", flush=True)
    catalog = load_catalog(args.catalog_repo, args.catalog_config)
    print(f"Loaded {len(catalog)} catalog items", flush=True)
    run_pool(
        tasks,
        args.output,
        endpoints,
        args.per_endpoint,
        catalog,
        args.reasoning_effort,
    )
    summary = summarize(args.output, args.summary, args.seed, len(tasks))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()