from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_RECORD_INDICES = (1, 2, 4, 51, 52, 63)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON at {path}:{line_number}: {error}") from error
            if not isinstance(row, dict):
                raise ValueError(f"expected an object at {path}:{line_number}")
            rows.append(row)
    return rows


def build_title_lookup(rows: list[dict[str, Any]]) -> dict[str, str]:
    lookup = {}
    for row in rows:
        history_sids = row.get("history_sid_list") or []
        history_titles = row.get("history_title_list") or []
        if len(history_sids) != len(history_titles):
            raise ValueError("history SID/title lengths differ")
        for sid, title in zip(history_sids, history_titles):
            lookup.setdefault(str(sid), str(title))
        lookup.setdefault(str(row["target_sid"]), str(row["target_title"]))
    return lookup


def convert_row(
    row: dict[str, Any],
    record_index: int,
    title_lookup: dict[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    beam_sids = [str(sid) for sid in row["prediction_beam_10"]]
    missing_sids = [sid for sid in beam_sids if sid not in title_lookup]
    if missing_sids:
        raise ValueError(
            f"record {record_index} has beam SIDs without titles: {missing_sids}"
        )
    target_sid = str(row["target_sid"])
    target_rank = beam_sids.index(target_sid) + 1 if target_sid in beam_sids else None
    request = {
        "request_id": f"checkpoint-record-{record_index:04d}",
        "history": [
            {"sid": str(sid), "title": str(title)}
            for sid, title in zip(row["history_sid_list"], row["history_title_list"])
        ],
        "target": {"sid": target_sid, "title": str(row["target_title"])},
        "candidates": [
            {
                "candidate_id": f"beam-{rank:02d}",
                "reasoning": str(row["reasoning"]),
                "predicted_item": {"sid": sid, "title": title_lookup[sid]},
                "hard_valid": True,
            }
            for rank, sid in enumerate(beam_sids, start=1)
        ],
    }
    suffix = f"hit_rank_{target_rank}" if target_rank else "all_wrong"
    manifest_entry = {
        "record_index": record_index,
        "request_file": f"record_{record_index:04d}_{suffix}.json",
        "history_titles": list(row["history_title_list"]),
        "target_title": row["target_title"],
        "target_rank": target_rank,
        "candidate_count": len(beam_sids),
        "simulation_note": "All beam candidates share the record's single reasoning trace.",
    }
    return request, manifest_entry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create title-only Qwen judge requests from checkpoint JSONL.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).with_name("test_data"),
    )
    parser.add_argument(
        "--record-indices",
        type=int,
        nargs="+",
        default=list(DEFAULT_RECORD_INDICES),
        help="One-based JSONL record indices.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_jsonl(args.input)
    title_lookup = build_title_lookup(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": str(args.input),
        "title_source": "history_title_list and target_title fields from the same JSONL",
        "requests": [],
    }
    for record_index in args.record_indices:
        if not 1 <= record_index <= len(rows):
            raise ValueError(f"record index {record_index} is outside [1, {len(rows)}]")
        request, entry = convert_row(rows[record_index - 1], record_index, title_lookup)
        output_path = args.output_dir / entry["request_file"]
        output_path.write_text(
            json.dumps(request, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest["requests"].append(entry)
        print(f"wrote {output_path}")
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()