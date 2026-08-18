"""Blind GPT-5.4 relevance audit for interest-to-item ANN retrieval results.

Each input row contains one inferred future interest and its recalled products.
The judge sees product titles, brands, and original catalog descriptions, but it
does not see cosine scores or which candidate is the held-out target. This keeps
semantic relevance judgments independent of ANN confidence and target identity.

Example:

    python data_curation/gpt5_judge_interest_ann_recall.py \
        --input ~/Downloads/interest_ann_recall_100x20.jsonl \
        --output ~/Downloads/interest_ann_recall_100x20_gpt54_judged.jsonl

Use ``--limit 1`` for a live smoke test and rerun without it to resume the rest.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

if __package__:
    from . import _phase2_process_common as common
else:
    import _phase2_process_common as common


MODEL = "gpt-5.4"
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MAX_COMPLETION_TOKENS = 5000
DEFAULT_INPUT = "~/Downloads/interest_ann_recall_100x20.jsonl"
DEFAULT_OUTPUT = "~/Downloads/interest_ann_recall_100x20_gpt54_judged.jsonl"
DEFAULT_SOURCE_REPO = "yufan/rec_rl_checkpoints"
DEFAULT_SOURCE_FILE = "results_analysis/yufan_reasoning_with_user_interest.jsonl"
DEFAULT_SOURCE_REVISION = "dcddfb418fdb57d92f1142400974bfe695a75f62"
MAX_DESCRIPTION_CHARS = 700
MAX_API_ATTEMPTS = 4

RELEVANCE_LABELS = {"relevant", "partial", "irrelevant"}
SPECIFICITY_LABELS = {"specific", "moderate", "broad"}

SYSTEM_PROMPT = """You are a strict product-retrieval relevance judge for a recommender-systems experiment.

TASK
Given ONE inferred future user interest and 20 retrieved Video Games catalog products, judge whether EACH product satisfies that interest. Evaluate product semantics only from the provided title, brand, and original catalog description.

BLIND-JUDGING RULES
- The candidate order is an ANN ranking that may be wrong. Do not assume earlier candidates are better.
- You are intentionally not shown cosine scores or the held-out target identity. Do not speculate about them.
- Judge every product independently. Do not lower a product's label merely because another candidate is better.
- Use only supplied metadata and ordinary knowledge directly implied by recognizable product titles. Do not invent product features.

RELEVANCE LABELS
- relevant: The product directly satisfies the core interest and all explicit hard constraints that matter, such as platform, product type, genre/mechanic, franchise/theme, compatibility, or use case. Minor wording differences are acceptable.
- partial: The product is plausibly adjacent and satisfies some important facets, but misses or leaves uncertain ONE major facet. Examples: right genre but wrong explicit platform; right platform and broad category but wrong requested mechanic; a useful complement when the query asks for the primary product; same franchise but wrong product type. Mere platform overlap alone is not partial.
- irrelevant: The product fails the core intent, conflicts with multiple major constraints, or matches only generic words such as gaming, player, experience, action, accessory, or a platform name.

IMPORTANT DISTINCTIONS
- Treat explicit platform/compatibility as a hard constraint unless the interest clearly allows cross-platform alternatives.
- Distinguish games, consoles, controllers, cameras, mounts, chargers, guides, cases, and other accessories. A shared platform does not make these interchangeable.
- Distinguish genres and use cases. For example, a PS4 controller or shooter is not relevant to a query about PS4 camera streaming or motion tracking merely because all are PS4 products.
- For broad interests, a product can be relevant if it genuinely instantiates the stated category. Do not demand an exact item prediction.
- Interest text may contain a history bridge after phrases such as "continuing" or "bridged from". Judge the FUTURE destination being requested, not whether the product merely matches the historical bridge.

OUTPUT
Return ONLY one JSON object, with no markdown or prose outside it:
{
  "query": {
    "core_intent": "concise normalized description",
    "hard_constraints": ["constraint", "..."],
    "specificity": "specific|moderate|broad",
    "ambiguity": "none or one concise ambiguity"
  },
  "items": [
    {"rank": 1, "label": "relevant|partial|irrelevant", "reason": "one concise evidence-based sentence"}
  ],
  "overall_comment": "one concise sentence describing the dominant retrieval strength or failure"
}

The items array must contain exactly 20 objects, exactly once for each rank 1 through 20 in ascending order. Keep each reason concise."""

USER_TEMPLATE = """INFERRED FUTURE INTEREST
Mode: {label}
Interest: {interest}

RETRIEVED PRODUCTS
{items}

Judge all 20 products under the system rubric. Return only the required JSON object."""


def _clip(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[:limit] + "..."


def original_description(value: Any) -> str:
    if value is None:
        return ""
    parsed = value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("[", "(")):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = value
    if isinstance(parsed, (list, tuple)):
        candidates = [str(item).strip() for item in parsed if str(item).strip()]
        return max(candidates, key=len) if candidates else ""
    return str(parsed).strip()


def build_user_prompt(row: dict[str, Any]) -> str:
    recalled = row.get("recalled_items")
    if not isinstance(recalled, list) or len(recalled) != 20:
        raise ValueError("each input row must contain exactly 20 recalled_items")
    item_blocks = []
    for expected_rank, item in enumerate(recalled, start=1):
        rank = item.get("rank")
        if rank != expected_rank:
            raise ValueError(f"expected recalled rank {expected_rank}, got {rank!r}")
        metadata = item.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"rank {rank} has no metadata object")
        item_blocks.append(
            "\n".join(
                [
                    f"{rank}. Title: {_clip(metadata.get('title'), 240)}",
                    f"   Brand: {_clip(metadata.get('brand'), 120) or '(unknown)'}",
                    "   Description: "
                    + (
                        _clip(original_description(metadata.get("description")), MAX_DESCRIPTION_CHARS)
                        or "(not provided)"
                    ),
                ]
            )
        )
    return USER_TEMPLATE.format(
        label=row.get("label", "unknown"),
        interest=_clip(row.get("interest"), 2000),
        items="\n".join(item_blocks),
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
        raise ValueError("judge response is not a JSON object")
    return value


def validate_judgment(value: dict[str, Any]) -> dict[str, Any]:
    if set(value) != {"query", "items", "overall_comment"}:
        raise ValueError("judge response has incorrect top-level keys")
    query = value["query"]
    if not isinstance(query, dict) or set(query) != {
        "core_intent",
        "hard_constraints",
        "specificity",
        "ambiguity",
    }:
        raise ValueError("query assessment has incorrect keys")
    if query["specificity"] not in SPECIFICITY_LABELS:
        raise ValueError(f"invalid query specificity: {query['specificity']!r}")
    if not isinstance(query["hard_constraints"], list) or not all(
        isinstance(item, str) and item.strip() for item in query["hard_constraints"]
    ):
        raise ValueError("hard_constraints must be a list of nonempty strings")
    for key in ("core_intent", "ambiguity"):
        if not isinstance(query[key], str) or not query[key].strip():
            raise ValueError(f"query.{key} must be a nonempty string")

    items = value["items"]
    if not isinstance(items, list) or len(items) != 20:
        raise ValueError("items must contain exactly 20 judgments")
    for expected_rank, item in enumerate(items, start=1):
        if not isinstance(item, dict) or set(item) != {"rank", "label", "reason"}:
            raise ValueError(f"rank {expected_rank} judgment has incorrect keys")
        if item["rank"] != expected_rank:
            raise ValueError(f"expected judgment rank {expected_rank}, got {item['rank']!r}")
        if item["label"] not in RELEVANCE_LABELS:
            raise ValueError(f"invalid relevance label at rank {expected_rank}")
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise ValueError(f"rank {expected_rank} reason must be nonempty")
    if not isinstance(value["overall_comment"], str) or not value["overall_comment"].strip():
        raise ValueError("overall_comment must be nonempty")
    return value


def judge(
    client: Any,
    user_prompt: str,
    model: str,
    reasoning_effort: str,
    max_completion_tokens: int,
) -> dict[str, Any]:
    last_error: Exception | None = None
    validation_feedback = ""
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": user_prompt + validation_feedback,
                    },
                ],
                max_completion_tokens=max_completion_tokens,
                reasoning_effort=reasoning_effort,
            )
            return validate_judgment(
                parse_json_object(response.choices[0].message.content or "")
            )
        except Exception as error:
            last_error = error
            validation_feedback = (
                "\n\nYour previous response failed validation: "
                f"{type(error).__name__}: {str(error)[:300]}. "
                "Return a corrected JSON object matching the exact schema."
            )
            if attempt < MAX_API_ATTEMPTS:
                time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(
        f"GPT judge failed after {MAX_API_ATTEMPTS} attempts: {last_error}"
    ) from last_error


def prompt_signature(model: str, reasoning_effort: str) -> str:
    payload = {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "system_prompt": SYSTEM_PROMPT,
        "user_template": USER_TEMPLATE,
        "max_description_chars": MAX_DESCRIPTION_CHARS,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_source_rows(path: str | None) -> dict[int, dict[str, Any]]:
    if path is None:
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(
            repo_id=DEFAULT_SOURCE_REPO,
            filename=DEFAULT_SOURCE_FILE,
            repo_type="dataset",
            revision=DEFAULT_SOURCE_REVISION,
        )
    return {int(row["source_index"]): row for row in load_jsonl(os.path.expanduser(path))}


def target_info(
    row: dict[str, Any],
    source_rows: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    source = source_rows.get(int(row["source_index"]))
    if source is None:
        raise ValueError(f"source_index {row['source_index']} is absent from source inference")
    target_sid = source["item_sid"]
    recalled = row["recalled_items"]
    target_rank = next(
        (
            item["rank"]
            for item in recalled
            if item.get("metadata", {}).get("sid") == target_sid
        ),
        None,
    )
    return {
        "target_sid": target_sid,
        "target_title": source["item_title"],
        "target_rank": target_rank,
    }


def build_tasks(
    rows: list[dict[str, Any]],
    source_rows: dict[int, dict[str, Any]],
    signature: str,
) -> list[tuple[str, int, dict[str, Any]]]:
    tasks = []
    seen = set()
    for row in rows:
        selection_index = int(row["selection_index"])
        if selection_index in seen:
            raise ValueError(f"duplicate selection_index: {selection_index}")
        seen.add(selection_index)
        task = dict(row)
        task.update(target_info(row, source_rows))
        task["prompt_signature"] = signature
        task["judge_prompt"] = build_user_prompt(row)
        tasks.append((f"selection::{selection_index}", selection_index, task))
    return tasks


def load_done(path: str, signature: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    done = set()
    for row in load_jsonl(path):
        if row.get("prompt_signature") != signature:
            raise RuntimeError(
                f"{path} uses a different prompt/model; choose a new output path"
            )
        done.add(str(row["row_key"]))
    return done


def canonical_result(
    task: dict[str, Any],
    judgment: dict[str, Any],
    endpoint: str,
    model: str,
) -> dict[str, Any]:
    item_judgments = judgment["items"]
    labels = [item["label"] for item in item_judgments]
    recalled = task["recalled_items"]
    audited_items = []
    for source_item, item_judgment in zip(recalled, item_judgments):
        metadata = source_item["metadata"]
        audited_items.append(
            {
                "rank": source_item["rank"],
                "ann_index_row": source_item.get("ann_index_row"),
                "cosine_similarity": source_item["cosine_similarity"],
                "item_id": metadata.get("item_id"),
                "sid": metadata.get("sid"),
                "title": metadata.get("title"),
                "label": item_judgment["label"],
                "reason": item_judgment["reason"],
                "is_target": metadata.get("sid") == task["target_sid"],
            }
        )
    target_judgment = next(
        (item for item in audited_items if item["is_target"]),
        None,
    )
    return {
        "row_key": f"selection::{task['selection_index']}",
        "selection_index": task["selection_index"],
        "source_index": task["source_index"],
        "user_id": task.get("user_id"),
        "interest_in_record": task.get("interest_in_record"),
        "interest_label": task.get("label"),
        "interest": task["interest"],
        "query_assessment": judgment["query"],
        "audited_items": audited_items,
        "relevant_count_at_20": labels.count("relevant"),
        "partial_count_at_20": labels.count("partial"),
        "irrelevant_count_at_20": labels.count("irrelevant"),
        "target_sid": task["target_sid"],
        "target_title": task["target_title"],
        "target_rank": task["target_rank"],
        "target_relevance": (
            target_judgment["label"] if target_judgment is not None else "not_retrieved"
        ),
        "overall_comment": judgment["overall_comment"],
        "judge_model": model,
        "judge_endpoint": endpoint,
        "prompt_signature": task["prompt_signature"],
    }


def summarize(path: str, summary_path: str) -> dict[str, Any]:
    records_by_key = {}
    for row in load_jsonl(path):
        records_by_key[row["row_key"]] = row
    records = list(records_by_key.values())
    if not records:
        raise ValueError("no completed judgments to summarize")

    def strict_precision_at(cutoff: int, subset: list[dict[str, Any]]) -> float:
        labels = [
            item["label"]
            for row in subset
            for item in row["audited_items"][:cutoff]
        ]
        return labels.count("relevant") / len(labels)

    def soft_precision_at(cutoff: int, subset: list[dict[str, Any]]) -> float:
        labels = [
            item["label"]
            for row in subset
            for item in row["audited_items"][:cutoff]
        ]
        return (
            labels.count("relevant") + 0.5 * labels.count("partial")
        ) / len(labels)

    metrics: dict[str, Any] = {
        "completed_queries": len(records),
        "unique_source_records": len({row["source_index"] for row in records}),
        "interest_label_counts": dict(Counter(row["interest_label"] for row in records)),
        "query_specificity_counts": dict(
            Counter(row["query_assessment"]["specificity"] for row in records)
        ),
        "target_relevance_counts": dict(Counter(row["target_relevance"] for row in records)),
    }
    for cutoff in (1, 5, 10, 20):
        metrics[f"strict_precision_at_{cutoff}"] = strict_precision_at(cutoff, records)
        metrics[f"soft_precision_at_{cutoff}"] = soft_precision_at(cutoff, records)
    for label in ("exploit", "explore"):
        subset = [row for row in records if row["interest_label"] == label]
        if subset:
            metrics[f"{label}_strict_precision_at_5"] = strict_precision_at(5, subset)
            metrics[f"{label}_strict_precision_at_20"] = strict_precision_at(20, subset)

    target_hits = [row for row in records if row["target_rank"] is not None]
    metrics["target_hits_at_20"] = len(target_hits)
    metrics["target_true_positive_at_20"] = sum(
        row["target_relevance"] == "relevant" for row in target_hits
    )
    metrics["target_partial_at_20"] = sum(
        row["target_relevance"] == "partial" for row in target_hits
    )
    metrics["target_false_positive_at_20"] = sum(
        row["target_relevance"] == "irrelevant" for row in target_hits
    )
    Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(summary_path).open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Blind GPT-5.4 semantic audit of interest ANN recall results."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--source-inference", default=None)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument(
        "--reasoning-effort",
        choices=("minimal", "low", "medium", "high"),
        default=DEFAULT_REASONING_EFFORT,
    )
    parser.add_argument("--max-completion-tokens", type=int, default=DEFAULT_MAX_COMPLETION_TOKENS)
    parser.add_argument("--per-endpoint", type=int, default=1)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.per_endpoint < 1:
        parser.error("--per-endpoint must be positive")
    if args.max_completion_tokens < 1000:
        parser.error("--max-completion-tokens must be at least 1000")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    input_path = os.path.expanduser(args.input)
    output_path = os.path.expanduser(args.output)
    summary_path = os.path.expanduser(
        args.summary or output_path.replace(".jsonl", ".summary.json")
    )
    source_path = os.path.expanduser(args.source_inference) if args.source_inference else None
    rows = load_jsonl(input_path)
    if args.limit is not None:
        rows = rows[: args.limit]
    signature = prompt_signature(args.model, args.reasoning_effort)
    source_rows = load_source_rows(source_path)
    tasks = build_tasks(rows, source_rows, signature)

    if args.dry_run:
        print(tasks[0][2]["judge_prompt"])
        print(f"\nPROMPT_SIGNATURE={signature}")
        return

    configured_endpoints, get_client = common.load_endpoint_helpers()
    endpoints = args.endpoints or configured_endpoints
    unknown = sorted(set(endpoints) - set(configured_endpoints))
    if unknown:
        parser.error(f"unknown endpoint(s): {unknown}")
    done = load_done(output_path, signature)
    pending = [task for task in tasks if task[0] not in done]

    def process(
        client: Any,
        _: str,
        __: int,
        task: dict[str, Any],
    ) -> dict[str, Any]:
        judgment = judge(
            client,
            task["judge_prompt"],
            args.model,
            args.reasoning_effort,
            args.max_completion_tokens,
        )
        endpoint = str(getattr(client, "base_url", "unknown"))
        return canonical_result(task, judgment, endpoint, args.model)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    common.run_pool(
        pending,
        process,
        output_path,
        [],
        endpoints,
        args.per_endpoint,
        get_client,
    )
    if not os.path.exists(output_path):
        raise RuntimeError(
            "no judgments completed; inspect "
            + output_path.replace(".jsonl", ".failures.jsonl")
        )
    metrics = summarize(output_path, summary_path)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Wrote {output_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()