from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any, Iterable, Optional

from huggingface_hub import hf_hub_download

from .client import InterestRetrieverClient


DEFAULT_REPO_ID = "yufan/rec_rl_checkpoints"
DEFAULT_FILENAME = "results_analysis/yufan_diverisity_process.jsonl"
DEFAULT_REVISION = "main"
DEFAULT_TOP_KS = (1, 5, 10, 20, 50, 100)

_FUTURE_INTERESTS_PATTERN = re.compile(
    r"<future_interests>\s*(?P<body>.*?)\s*</future_interests>",
    re.DOTALL,
)
_INTEREST_LINE_PATTERN = re.compile(
    r"^-\s+\[(?P<label>exploit|explore)\]\s+"
    r"(?P<citations><a_\d+><b_\d+><c_\d+>"
    r"(?:\s*,\s*<a_\d+><b_\d+><c_\d+>)*)\s*=>\s*(?P<text>\S.*)$",
    re.IGNORECASE,
)


def extract_interest_lines(reasoning: str) -> list[dict[str, str]]:
    match = _FUTURE_INTERESTS_PATTERN.search(str(reasoning))
    if match is None:
        raise ValueError("missing <future_interests> block")
    lines = [line.strip() for line in match.group("body").splitlines() if line.strip()]
    interests = []
    for line in lines:
        line_match = _INTEREST_LINE_PATTERN.fullmatch(line)
        if line_match is None:
            raise ValueError(f"invalid future-interest line: {line[:200]}")
        interests.append(
            {
                "label": line_match.group("label").casefold(),
                "query": line,
                "text": line_match.group("text"),
            }
        )
    if not interests:
        raise ValueError("future-interest block is empty")
    return interests


def iter_jsonl(path: str | Path, limit: Optional[int] = None) -> Iterable[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as file:
        for row_index, line in enumerate(file):
            if limit is not None and row_index >= limit:
                break
            if line.strip():
                yield json.loads(line)


def target_rank_for_label(
    response: dict[str, Any],
    interests: list[dict[str, str]],
    label: Optional[str] = None,
) -> Optional[int]:
    ranks = []
    for interest, result in zip(interests, response["results"]):
        if label is not None and interest["label"] != label:
            continue
        rank = result.get("target_rank")
        if rank is not None:
            ranks.append(int(rank))
    return min(ranks) if ranks else None


def summarize(records: list[dict[str, Any]], top_ks: tuple[int, ...]) -> dict[str, Any]:
    evaluated = [record for record in records if record.get("status") == "ok"]
    total_count = len(records)
    evaluated_count = len(evaluated)
    summary: dict[str, Any] = {
        "total_records": total_count,
        "evaluated_records": evaluated_count,
        "parse_failures": sum(record.get("status") == "parse_error" for record in records),
        "request_failures": sum(record.get("status") == "request_error" for record in records),
        "mean_interests_per_record": (
            sum(record["interest_count"] for record in evaluated) / len(evaluated)
            if evaluated
            else 0.0
        ),
    }
    for scope in ("all", "exploit", "explore"):
        key = f"{scope}_target_rank"
        strict_recall = {}
        conditional_recall = {}
        for top_k in top_ks:
            hit_count = sum(
                record[key] is not None and record[key] <= top_k
                for record in evaluated
            )
            strict_recall[f"recall_at_{top_k}"] = (
                hit_count / total_count if total_count else 0.0
            )
            conditional_recall[f"recall_at_{top_k}"] = (
                hit_count / evaluated_count if evaluated_count else 0.0
            )
        summary[f"{scope}_recall"] = strict_recall
        summary[f"{scope}_conditional_recall"] = conditional_recall
    summary["prediction_beam_recall_at_10"] = (
        sum(record.get("prediction_beam_hit_at_10", False) for record in records) / total_count
        if total_count
        else 0.0
    )
    return summary


def _batched(values: list[Any], batch_size: int) -> Iterable[list[Any]]:
    for start in range(0, len(values), batch_size):
        yield values[start : start + batch_size]


def evaluate(args: argparse.Namespace) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    top_ks = tuple(sorted(set(args.top_k)))
    source_path = args.input or hf_hub_download(
        repo_id=args.repo_id,
        filename=args.filename,
        repo_type="dataset",
        revision=args.revision,
    )
    source_rows = list(iter_jsonl(source_path, args.limit))
    details: list[dict[str, Any]] = []
    pending = []

    for row_index, row in enumerate(source_rows):
        detail = {
            "row_index": row_index,
            "source_index": row.get("source_index"),
            "user_id": row.get("user_id"),
            "target_sid": row.get("item_sid"),
            "target_title": row.get("item_title"),
            "prediction_beam_hit_at_10": row.get("item_sid")
            in row.get("prediction_beam_10", [])[:10],
        }
        try:
            interests = extract_interest_lines(row.get("generated_reasoning_path", ""))
            if not detail["target_sid"]:
                raise ValueError("missing item_sid")
        except ValueError as error:
            detail.update({"status": "parse_error", "error": str(error)})
            details.append(detail)
            continue

        request_id = f"row-{row_index}-source-{row.get('source_index', 'unknown')}"
        payload = {
            "request_id": request_id,
            "target_sid": detail["target_sid"],
            "interests": [interest["query"] for interest in interests],
            "top_k": max(top_ks),
        }
        detail.update(
            {
                "status": "pending",
                "request_id": request_id,
                "interest_count": len(interests),
                "interests": interests,
            }
        )
        details.append(detail)
        pending.append((detail, payload, interests))

    client = InterestRetrieverClient(
        args.endpoint,
        timeout=args.timeout,
        max_attempts=args.max_attempts,
    )
    for batch in _batched(pending, args.batch_size):
        payloads = [payload for _, payload, _ in batch]
        try:
            responses = client.retrieve_batch(payloads)
            responses_by_id = {response["request_id"]: response for response in responses}
            if len(responses_by_id) != len(payloads):
                raise RuntimeError("batch response contains missing or duplicate request IDs")
            for detail, payload, interests in batch:
                response = responses_by_id[payload["request_id"]]
                if len(response["results"]) != len(interests):
                    raise RuntimeError("response interest count does not match the request")
                detail.update(
                    {
                        "status": "ok",
                        "all_target_rank": target_rank_for_label(response, interests),
                        "exploit_target_rank": target_rank_for_label(response, interests, "exploit"),
                        "explore_target_rank": target_rank_for_label(response, interests, "explore"),
                        "retrieval_results": response["results"],
                    }
                )
        except (KeyError, RuntimeError, ValueError) as error:
            for detail, _, _ in batch:
                detail.update({"status": "request_error", "error": str(error)})

    summary = summarize(details, top_ks)
    summary.update(
        {
            "source": str(source_path),
            "repo_id": args.repo_id,
            "filename": args.filename,
            "revision": args.revision,
            "endpoint": args.endpoint,
            "top_ks": list(top_ks),
            "query_mode": "full_interest_line",
        }
    )
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            for detail in details:
                file.write(json.dumps(detail, ensure_ascii=False) + "\n")
    return summary, details


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure target recall from generated future-interest blocks."
    )
    parser.add_argument("--endpoint", default="http://localhost:8092")
    parser.add_argument("--input", default=None, help="Optional local JSONL instead of Hugging Face.")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--filename", default=DEFAULT_FILENAME)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--top-k", nargs="+", type=int, default=list(DEFAULT_TOP_KS))
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--output", default=None, help="Optional detailed JSONL output path.")
    args = parser.parse_args()
    if not args.top_k or any(top_k < 1 or top_k > 1000 for top_k in args.top_k):
        parser.error("--top-k values must be between 1 and 1000")
    if args.batch_size < 1 or args.batch_size > 256:
        parser.error("--batch-size must be between 1 and 256")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    return args


def main() -> None:
    summary, _ = evaluate(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()