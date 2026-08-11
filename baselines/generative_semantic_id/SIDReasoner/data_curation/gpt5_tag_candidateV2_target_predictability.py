"""Tag candidateV2 rows by how predictable the held-out target is from history.

This script deliberately does not show ``reasoning_path`` to the judge. It asks
whether the observed history contains enough semantic evidence for the target,
which is the quantity needed to decide whether a row is suitable for Phase-2
reasoning SFT. The tags are sidecar outputs; the Hugging Face source is unchanged.

Examples:

    # Inspect one real prompt without calling Azure OpenAI.
    python gpt5_tag_candidateV2_target_predictability.py --limit 1 --dry-run

    # Random 1,000-row pilot.
    python gpt5_tag_candidateV2_target_predictability.py \
        --limit 1000 --random-sample --seed 42

    # Full run across every configured GPT-5.4 endpoint.
    python gpt5_tag_candidateV2_target_predictability.py \
        --out-dir ./candidateV2_target_predictability

Outputs:

    Video_Games.target_predictability.tags.jsonl
    Video_Games.target_predictability.tags.csv
    Video_Games.target_predictability.summary.json
    Video_Games.target_predictability.indices.json
    Video_Games.target_predictability.failures.jsonl
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
import multiprocessing as mp
import os
import queue
import random
import re
import time
from typing import Any

import pandas as pd
from datasets import load_dataset


HF_REPO = "yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV2"
CATEGORY = "Video_Games"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_PER_ENDPOINT = 8
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MIN_KEEP_SCORE = 3
MAX_COMPLETION_TOKENS = 600
MAX_API_ATTEMPTS = 4
MAX_HISTORY_DESCRIPTION_CHARS = 320
MAX_TARGET_DESCRIPTION_CHARS = 420
MAX_TITLE_CHARS = 120
LOG_EVERY_SEC = 10
TAG_SCHEMA_VERSION = "target_predictability_v2_support_mode"

SID_RE = re.compile(r"<a_[^<>\s]+><b_[^<>\s]+><c_[^<>\s]+>")
TARGET_RELATIONS = {
    "repeat",
    "same_brand_or_series",
    "same_subcategory_or_use_case",
    "complementary",
    "broadening",
    "unrelated",
}
TARGET_SUPPORT_MODES = {"exploit", "explore", "neither"}
REQUIRED_KEYS = [
    "target_support_mode",
    "target_relation",
    "target_predictability",
    "supporting_history_sids",
    "rationale",
    "confidence",
]


SYSTEM_PROMPT = """Judge whether HISTORY alone supports the held-out next click. This is
observational, not causal. Use only titles, brands, and descriptions; SID prefixes are opaque.

target_support_mode:
- exploit: the same specific interest/use case is directly present in HISTORY (repeat, sequel,
    same fine-grained type or mechanic).
- explore: not directly present, but ONE explicit semantic or functional bridge connects HISTORY
    to target; the bridge must be supported on both sides. Direct complementarity may qualify.
- neither: no exploit and no valid one-step explore. Platform/brand-only overlap, "both are games",
    weak/multi-hop guesses, unrelated clicks, and post-hoc rationalization are neither.
Weak exploration is neither; when uncertain, choose neither.

target_relation is one of: repeat, same_brand_or_series, same_subcategory_or_use_case,
complementary, broadening, unrelated. Map them respectively to exploit, exploit, exploit,
explore, explore, neither.

target_predictability: 5=nearly determined; 4=strong continuation; 3=plausible but many
alternatives; 2=weak/indirect; 1=unpredictable. exploit/explore requires score 3..5 and 1-3
supporting HISTORY SIDs. neither requires score 1..2 and no supporting SID. repeat is exploit/5.

Return ONLY:
{"target_support_mode":string,"target_relation":string,"target_predictability":integer,
"supporting_history_sids":array,"rationale":string,"confidence":integer}

Copy at most 3 decisive SIDs exactly from HISTORY. Rationale: at most 50 words, state the direct
interest or one-step bridge and main missing evidence. Confidence is 1..5. Invent nothing."""

USER_TEMPLATE = """CATEGORY: {category}

USER HISTORY (chronological, oldest to newest):
{history_block}

HELD-OUT NEXT-CLICK TARGET:
{target_block}

DETERMINISTIC FACTS:
- history_length: {history_length}
- target_sid_already_in_history: {exact_repeat}

Judge target predictability from history alone and return only the strict JSON object."""


def as_list(value: Any) -> list[Any]:
    """Normalize HF arrays and legacy stringified Python lists."""
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("[", "(")):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                return [value]
            if isinstance(parsed, (list, tuple)):
                return list(parsed)
    return [value]


def _clip(value: Any, limit: int) -> str:
    text = "" if value is None else str(value).strip()
    return text if len(text) <= limit else text[:limit] + "..."


def _processed_description(value: Any, fallback: str) -> str:
    candidates = [str(item).strip() for item in as_list(value) if str(item).strip()]
    return max(candidates, key=len) if candidates else fallback


def load_catalog(repo: str, category: str) -> dict[str, dict[str, str]]:
    dataset = load_dataset(repo, f"{category}_catalog", split="train")
    catalog = {}
    for row in dataset:
        sid = str(row["sid"])
        title = str(row.get("title") or "")
        detailed = _processed_description(row.get("detailed_description"), "")
        description = detailed or _processed_description(row.get("description"), title)
        catalog[sid] = {
            "title": title,
            "brand": str(row.get("brand") or ""),
            "description": description,
        }
    return catalog


def normalize_row(row: dict[str, Any], catalog: dict[str, dict[str, str]]) -> dict[str, Any]:
    history_sids = [str(value) for value in as_list(row.get("history_item_sid"))]
    history_titles = [str(value) for value in as_list(row.get("history_item_title"))]
    if not history_sids:
        raise ValueError("history_item_sid is empty")

    history = []
    for index, sid in enumerate(history_sids):
        if SID_RE.fullmatch(sid) is None:
            raise ValueError(f"malformed history SID: {sid}")
        meta = catalog.get(sid, {})
        row_title = history_titles[index] if index < len(history_titles) else ""
        history.append(
            {
                "sid": sid,
                "title": str(meta.get("title") or row_title or "(missing title)"),
                "brand": str(meta.get("brand") or ""),
                "description": str(meta.get("description") or row_title or ""),
            }
        )

    target_sid = str(row.get("item_sid") or "")
    if SID_RE.fullmatch(target_sid) is None:
        raise ValueError(f"malformed target SID: {target_sid}")
    target_meta = catalog.get(target_sid, {})
    target_title = str(row.get("item_title") or target_meta.get("title") or "(missing title)")
    target = {
        "sid": target_sid,
        "title": target_title,
        "brand": str(target_meta.get("brand") or ""),
        "description": str(target_meta.get("description") or target_title),
    }
    return {
        "user_id": row.get("user_id"),
        "history": history,
        "target": target,
    }


def _item_line(
    item: dict[str, str],
    index: int | None = None,
    description_limit: int = MAX_HISTORY_DESCRIPTION_CHARS,
) -> str:
    prefix = f"{index}. " if index is not None else ""
    parts = [f"{prefix}{_clip(item['title'], MAX_TITLE_CHARS)} [{item['sid']}]" ]
    if item.get("brand"):
        parts.append(f"brand={_clip(item['brand'], 100)}")
    if item.get("description"):
        parts.append(f"description={_clip(item['description'], description_limit)}")
    return " | ".join(parts)


def build_prompt(normalized: dict[str, Any], category: str) -> str:
    history = normalized["history"]
    history_block = "\n".join(
        _item_line(item, index)
        for index, item in enumerate(history, start=1)
    )
    target_block = _item_line(
        normalized["target"],
        description_limit=MAX_TARGET_DESCRIPTION_CHARS,
    )
    history_sids = {item["sid"] for item in history}
    return USER_TEMPLATE.format(
        category=category,
        history_block=history_block,
        target_block=target_block,
        history_length=len(history),
        exact_repeat=normalized["target"]["sid"] in history_sids,
    )


def generation_signature(
    repo: str,
    model: str,
    reasoning_effort: str,
    auto_label_exact_repeat: bool,
) -> str:
    payload = {
        "schema": TAG_SCHEMA_VERSION,
        "repo": repo,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
        "auto_label_exact_repeat": auto_label_exact_repeat,
        "system_prompt": SYSTEM_PROMPT,
        "user_template": USER_TEMPLATE,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]


def row_tag_id(
    normalized: dict[str, Any],
    source_index: int,
    signature: str,
) -> str:
    payload = {
        "signature": signature,
        "source_index": source_index,
        "user_id": normalized["user_id"],
        "history_sids": [item["sid"] for item in normalized["history"]],
        "target_sid": normalized["target"]["sid"],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def parse_json_object(text: str) -> dict[str, Any]:
    if not text:
        raise ValueError("empty judge response")
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped).strip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"no JSON object in judge response: {text[:160]!r}")
    return json.loads(stripped[start : end + 1])


def validate_labels(
    labels: dict[str, Any],
    history_sids: list[str],
    target_sid: str | None = None,
) -> dict[str, Any]:
    if not isinstance(labels, dict):
        raise ValueError("judge response is not a JSON object")
    missing = [key for key in REQUIRED_KEYS if key not in labels]
    extra = [key for key in labels if key not in REQUIRED_KEYS]
    if missing or extra:
        raise ValueError(f"schema mismatch; missing={missing}, extra={extra}")
    support_mode = labels["target_support_mode"]
    if support_mode not in TARGET_SUPPORT_MODES:
        raise ValueError(f"invalid target_support_mode: {support_mode!r}")
    if labels["target_relation"] not in TARGET_RELATIONS:
        raise ValueError(f"invalid target_relation: {labels['target_relation']!r}")
    for key in ("target_predictability", "confidence"):
        value = labels[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"{key} must be an integer in [1, 5]")
    supporting = labels["supporting_history_sids"]
    if not isinstance(supporting, list) or any(not isinstance(value, str) for value in supporting):
        raise ValueError("supporting_history_sids must be an array of strings")
    invalid_sids = sorted(set(supporting) - set(history_sids))
    if invalid_sids:
        raise ValueError(f"supporting_history_sids contains non-history SIDs: {invalid_sids}")
    if len(supporting) > 3:
        raise ValueError("supporting_history_sids must contain at most 3 SIDs")
    if not isinstance(labels["rationale"], str) or not labels["rationale"].strip():
        raise ValueError("rationale must be a non-empty string")
    if len(labels["rationale"].split()) > 50:
        raise ValueError("rationale must contain at most 50 words")
    if labels["target_predictability"] >= 3 and not supporting:
        raise ValueError("predictability >= 3 requires at least one supporting history SID")
    if support_mode in {"exploit", "explore"} and labels["target_predictability"] < 3:
        raise ValueError("exploit/explore requires predictability >= 3")
    if support_mode == "neither":
        if labels["target_predictability"] > 2:
            raise ValueError("neither requires predictability <= 2")
        if supporting:
            raise ValueError("neither requires an empty supporting_history_sids array")
    if labels["target_relation"] == "unrelated" and labels["target_predictability"] > 2:
        raise ValueError("unrelated targets must have predictability <= 2")
    relation_to_mode = {
        "repeat": "exploit",
        "same_brand_or_series": "exploit",
        "same_subcategory_or_use_case": "exploit",
        "complementary": "explore",
        "broadening": "explore",
        "unrelated": "neither",
    }
    expected_mode = relation_to_mode[labels["target_relation"]]
    if support_mode != expected_mode:
        raise ValueError(
            f"target_relation={labels['target_relation']} requires target_support_mode={expected_mode}"
        )
    if labels["target_relation"] == "repeat" and target_sid not in set(history_sids):
        raise ValueError("repeat relation requires the target SID in history")
    if target_sid in set(history_sids) and (
        support_mode != "exploit"
        or labels["target_relation"] != "repeat"
        or labels["target_predictability"] != 5
    ):
        raise ValueError("an exact target repeat must use relation=repeat and predictability=5")
    return labels


def predictability_tag(score: int) -> str:
    return {
        1: "unpredictable",
        2: "weak",
        3: "plausible",
        4: "strong",
        5: "near_deterministic",
    }[score]


def build_result(
    task: dict[str, Any],
    labels: dict[str, Any],
    label_source: str,
    model: str,
) -> dict[str, Any]:
    score = labels["target_predictability"]
    return {
        "tag_id": task["tag_id"],
        "source_index": task["source_index"],
        "user_id": task["user_id"],
        "history_item_sid": task["history_sids"],
        "history_item_title": task["history_titles"],
        "item_sid": task["target_sid"],
        "item_title": task["target_title"],
        "history_length": len(task["history_sids"]),
        **labels,
        "target_predictability_tag": predictability_tag(score),
        "label_source": label_source,
        "generation_model": model,
        "tag_schema_version": TAG_SCHEMA_VERSION,
        "generation_signature": task["signature"],
    }


def with_filter_decision(record: dict[str, Any], min_keep_score: int) -> dict[str, Any]:
    result = dict(record)
    support_mode = result["target_support_mode"]
    keep = support_mode != "neither" and result["target_predictability"] >= min_keep_score
    if support_mode == "neither":
        filter_reason = "drop_neither_exploit_nor_explore"
    elif not keep:
        filter_reason = "drop_below_predictability_threshold"
    else:
        filter_reason = f"keep_{support_mode}"
    result.update(
        {
            "keep_for_phase2_reasoning": keep,
            "filter_reason": filter_reason,
            "min_keep_score": min_keep_score,
        }
    )
    return result


def exact_repeat_labels(target_sid: str) -> dict[str, Any]:
    return {
        "target_support_mode": "exploit",
        "target_relation": "repeat",
        "target_predictability": 5,
        "supporting_history_sids": [target_sid],
        "rationale": "The target SID already appears in the observed history.",
        "confidence": 5,
    }


def chat_labels(
    client: Any,
    task: dict[str, Any],
    model: str,
    reasoning_effort: str,
) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": task["prompt"]},
                ],
                max_completion_tokens=MAX_COMPLETION_TOKENS,
                reasoning_effort=reasoning_effort,
            )
            labels = parse_json_object(response.choices[0].message.content or "")
            return validate_labels(labels, task["history_sids"], task["target_sid"])
        except Exception as error:
            last_error = error
            if attempt < MAX_API_ATTEMPTS:
                time.sleep(min(2 ** (attempt - 1), 4))
    raise RuntimeError(f"judge failed after {MAX_API_ATTEMPTS} attempts: {last_error}")


def process_worker(
    task_queue: Any,
    result_queue: Any,
    endpoint: str,
    model: str,
    reasoning_effort: str,
) -> None:
    try:
        from gpt5_endpoint_test import get_GPT5_client

        client = get_GPT5_client(endpoint)
    except Exception as error:
        result_queue.put(("worker_error", endpoint, type(error).__name__, str(error)[:1000]))
        return

    while True:
        task = task_queue.get()
        if task is None:
            return
        try:
            labels = chat_labels(client, task, model, reasoning_effort)
            result = build_result(task, labels, "gpt-5.4", model)
            result_queue.put(("ok", result))
        except Exception as error:
            result_queue.put(
                (
                    "fail",
                    endpoint,
                    task["source_index"],
                    task["tag_id"],
                    type(error).__name__,
                    str(error)[:1000],
                )
            )


def load_done_ids(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    done = set()
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                done.add(json.loads(line)["tag_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def append_jsonl(path: str, value: dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")
        handle.flush()


def load_tag_records(path: str, signature: str) -> list[dict[str, Any]]:
    records_by_source_index = {}
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
                if record.get("generation_signature") == signature:
                    records_by_source_index[record["source_index"]] = record
            except (json.JSONDecodeError, KeyError):
                continue
    return sorted(records_by_source_index.values(), key=lambda row: row["source_index"])


def write_outputs(
    records: list[dict[str, Any]],
    jsonl_path: str,
    source: Any,
    min_keep_score: int,
) -> None:
    if not records:
        return
    decorated_records = [with_filter_decision(row, min_keep_score) for row in records]
    csv_path = jsonl_path.replace(".tags.jsonl", ".tags.csv")
    pd.json_normalize(decorated_records).to_csv(csv_path, index=False)

    kept = [row["source_index"] for row in decorated_records if row["keep_for_phase2_reasoning"]]
    dropped = [row["source_index"] for row in decorated_records if not row["keep_for_phase2_reasoning"]]
    indices_path = jsonl_path.replace(".tags.jsonl", ".indices.json")
    with open(indices_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "tagged_rows": len(decorated_records),
                "dataset_rows": len(source),
                "min_keep_score": min_keep_score,
                "keep_source_indices": kept,
                "drop_source_indices": dropped,
            },
            handle,
            indent=2,
        )
        handle.write("\n")

    source_indices = [row["source_index"] for row in decorated_records]
    source_frame = source.select(source_indices).to_pandas()
    source_frame.insert(0, "source_index", source_indices)
    source_columns = set(source_frame.columns)
    tag_frame = pd.DataFrame(
        [
            {key: value for key, value in row.items() if key not in source_columns or key == "source_index"}
            for row in decorated_records
        ]
    )
    tagged_frame = source_frame.merge(
        tag_frame,
        on="source_index",
        how="inner",
        validate="one_to_one",
    ).sort_values("source_index")
    tagged_path = jsonl_path.replace(".tags.jsonl", ".tagged.parquet")
    kept_path = jsonl_path.replace(".tags.jsonl", ".kept.parquet")
    dropped_path = jsonl_path.replace(".tags.jsonl", ".dropped.parquet")
    tagged_frame.to_parquet(tagged_path, index=False)
    tagged_frame[tagged_frame["keep_for_phase2_reasoning"]].to_parquet(kept_path, index=False)
    tagged_frame[~tagged_frame["keep_for_phase2_reasoning"]].to_parquet(dropped_path, index=False)

    history_buckets: dict[int, list[dict[str, Any]]] = {}
    for row in decorated_records:
        history_buckets.setdefault(row["history_length"], []).append(row)
    summary = {
        "tagged_rows": len(decorated_records),
        "dataset_rows": len(source),
        "min_keep_score": min_keep_score,
        "keep_rows": len(kept),
        "drop_rows": len(dropped),
        "keep_rate": len(kept) / len(decorated_records),
        "target_predictability_distribution": dict(
            sorted(Counter(row["target_predictability"] for row in decorated_records).items())
        ),
        "target_predictability_tag_distribution": dict(
            Counter(row["target_predictability_tag"] for row in decorated_records)
        ),
        "target_relation_distribution": dict(
            Counter(row["target_relation"] for row in decorated_records)
        ),
        "target_support_mode_distribution": dict(
            Counter(row["target_support_mode"] for row in decorated_records)
        ),
        "label_source_distribution": dict(
            Counter(row["label_source"] for row in decorated_records)
        ),
        "retention_by_min_score": {
            str(threshold): {
                "keep_rows": sum(
                    row["target_support_mode"] != "neither"
                    and row["target_predictability"] >= threshold
                    for row in decorated_records
                ),
                "drop_rows": sum(
                    row["target_support_mode"] == "neither"
                    or row["target_predictability"] < threshold
                    for row in decorated_records
                ),
                "keep_rate": sum(
                    row["target_support_mode"] != "neither"
                    and row["target_predictability"] >= threshold
                    for row in decorated_records
                ) / len(decorated_records),
            }
            for threshold in range(1, 6)
        },
        "by_history_length": {
            str(length): {
                "rows": len(rows),
                "keep_rows": sum(row["keep_for_phase2_reasoning"] for row in rows),
                "keep_rate": sum(row["keep_for_phase2_reasoning"] for row in rows) / len(rows),
            }
            for length, rows in sorted(history_buckets.items())
        },
    }
    summary_path = jsonl_path.replace(".tags.jsonl", ".summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"wrote {csv_path} ({len(decorated_records)} rows)")
    print(f"wrote {tagged_path}, {kept_path}, and {dropped_path}")
    print(f"wrote {indices_path}: keep={len(kept)}, drop={len(dropped)}")
    print(f"wrote {summary_path}")


def _fmt(seconds: float) -> str:
    seconds = int(max(0, seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def run_pool(
    tasks: list[dict[str, Any]],
    output_path: str,
    failure_path: str,
    endpoints: list[str],
    per_endpoint: int,
    model: str,
    reasoning_effort: str,
) -> None:
    if not tasks:
        return
    context = mp.get_context("spawn")
    task_queue = context.Queue()
    result_queue = context.Queue()
    worker_specs = [endpoint for endpoint in endpoints for _ in range(per_endpoint)]
    worker_specs = worker_specs[: min(len(worker_specs), len(tasks))]
    workers = [
        context.Process(
            target=process_worker,
            args=(
                task_queue,
                result_queue,
                endpoint,
                model,
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
    worker_errors = 0
    total = len(tasks)
    print(
        f"{total} GPT tasks / {len(endpoints)} endpoints x {per_endpoint} "
        f"= {len(workers)} processes"
    )
    try:
        while done + failed < total:
            try:
                message = result_queue.get(timeout=1.0)
            except queue.Empty:
                if not any(worker.is_alive() for worker in workers):
                    raise RuntimeError(
                        f"all workers exited with {total - done - failed} tasks unfinished"
                    )
                continue

            kind = message[0]
            if kind == "ok":
                append_jsonl(output_path, message[1])
                done += 1
            elif kind == "fail":
                append_jsonl(
                    failure_path,
                    {
                        "endpoint": message[1],
                        "source_index": message[2],
                        "tag_id": message[3],
                        "error_type": message[4],
                        "error": message[5],
                    },
                )
                failed += 1
            elif kind == "worker_error":
                worker_errors += 1
                print(f"WORKER ERROR {message[1]}: {message[2]}: {message[3]}")

            now = time.time()
            if now - last_log >= LOG_EVERY_SEC or done + failed == total:
                last_log = now
                finished = done + failed
                elapsed = now - started
                rate = finished / elapsed if elapsed else 0.0
                eta = (total - finished) / rate if rate else 0.0
                print(
                    f"{finished}/{total} ({finished / total:.1%}) | "
                    f"{rate:.2f} rows/s | elapsed {_fmt(elapsed)} | ETA {_fmt(eta)} | "
                    f"failed={failed} worker_errors={worker_errors}",
                    flush=True,
                )
    finally:
        for worker in workers:
            worker.join(timeout=5)
            if worker.is_alive():
                worker.terminate()
        task_queue.close()
        result_queue.close()


def selected_indices(total: int, limit: int, random_sample: bool, seed: int) -> list[int]:
    if limit <= 0 or limit >= total:
        return list(range(total))
    if random_sample:
        return sorted(random.Random(seed).sample(range(total), limit))
    return list(range(limit))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tag candidateV2 history-target predictability with GPT-5.4."
    )
    parser.add_argument("--hf-repo", default=HF_REPO)
    parser.add_argument("--category", default=CATEGORY, choices=[CATEGORY])
    parser.add_argument("--split", default="train")
    parser.add_argument("--out-dir", default="./candidateV2_target_predictability")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        choices=["minimal", "low", "medium", "high"],
    )
    parser.add_argument("--min-keep-score", type=int, default=DEFAULT_MIN_KEEP_SCORE)
    parser.add_argument("--limit", type=int, default=-1)
    parser.add_argument("--random-sample", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--auto-label-exact-repeat",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Tag exact target repeats deterministically instead of calling GPT.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.per_endpoint < 1:
        parser.error("--per-endpoint must be at least 1")
    if not 1 <= args.min_keep_score <= 5:
        parser.error("--min-keep-score must be in [1, 5]")

    source = load_dataset(
        args.hf_repo,
        f"{args.category}_reasoning",
        split=args.split,
    )
    catalog = load_catalog(args.hf_repo, args.category)
    indices = selected_indices(len(source), args.limit, args.random_sample, args.seed)
    signature = generation_signature(
        args.hf_repo,
        args.model,
        args.reasoning_effort,
        args.auto_label_exact_repeat,
    )

    if args.dry_run:
        normalized = normalize_row(dict(source[indices[0]]), catalog)
        print("=== SYSTEM PROMPT ===")
        print(SYSTEM_PROMPT)
        print("\n=== USER PROMPT ===")
        print(build_prompt(normalized, args.category))
        return

    os.makedirs(args.out_dir, exist_ok=True)
    output_path = os.path.join(
        args.out_dir,
        f"{args.category}.target_predictability.tags.jsonl",
    )
    failure_path = output_path.replace(".tags.jsonl", ".failures.jsonl")
    done_ids = load_done_ids(output_path)
    tasks = []
    deterministic_count = 0
    for source_index in indices:
        normalized = normalize_row(dict(source[source_index]), catalog)
        tag_id = row_tag_id(normalized, source_index, signature)
        if tag_id in done_ids:
            continue
        history_sids = [item["sid"] for item in normalized["history"]]
        task = {
            "tag_id": tag_id,
            "signature": signature,
            "source_index": source_index,
            "user_id": normalized["user_id"],
            "history_sids": history_sids,
            "history_titles": [item["title"] for item in normalized["history"]],
            "target_sid": normalized["target"]["sid"],
            "target_title": normalized["target"]["title"],
            "prompt": build_prompt(normalized, args.category),
        }
        if args.auto_label_exact_repeat and task["target_sid"] in set(history_sids):
            result = build_result(
                task,
                exact_repeat_labels(task["target_sid"]),
                "deterministic_exact_repeat",
                args.model,
            )
            append_jsonl(output_path, result)
            deterministic_count += 1
        else:
            tasks.append(task)

    print(
        f"selected={len(indices)}/{len(source)} already_done={len(done_ids)} "
        f"deterministic={deterministic_count} GPT_pending={len(tasks)}"
    )
    if tasks:
        from gpt5_endpoint_test import ENDPOINTS

        endpoints = args.endpoints or list(ENDPOINTS)
        unknown = [endpoint for endpoint in endpoints if endpoint not in ENDPOINTS]
        if unknown:
            parser.error(f"unknown endpoint(s): {unknown}")
        run_pool(
            tasks,
            output_path,
            failure_path,
            endpoints,
            args.per_endpoint,
            args.model,
            args.reasoning_effort,
        )
    records = load_tag_records(output_path, signature)
    write_outputs(records, output_path, source, args.min_keep_score)


if __name__ == "__main__":
    main()