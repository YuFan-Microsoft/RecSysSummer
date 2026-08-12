"""Rewrite candidateV2 Phase-2 traces using predictability tags as constraints.

The source dataset already contains target-predictability tags. This pipeline
rewrites only rows whose target has an ``exploit`` or ``explore`` bridge with a
predictability score at or above the configured threshold. Rows tagged
``neither`` are deliberately excluded: forcing their target interest into the
trace would teach privileged-target backfitting.

For each eligible row, GPT-5.4 first refines the old V4 trace against history
metadata without receiving the held-out target field. A second GPT-5.4 call
selects the best refinement, inserts one tag-matched target interest, and
returns a strict audit.
The result is accepted only when:

* the history summary is judged factual and target-blind;
* one identified future-interest line covers the target interest through the
  tagged support mode and all tagged supporting history SIDs;
* the trace contains no target SID or exact target-title leakage; and
* the reviewed trace reaches the configured overall-quality threshold.

Examples:

    # Inspect the prompt for the linked HF viewer row without calling GPT.
    python gpt5_rewrite_candidateV2_reasoning.py \
        --source-indices 80 --dry-run

    # Rewrite a random 100-row pilot with two candidates per row.
    python gpt5_rewrite_candidateV2_reasoning.py \
        --limit 100 --random-sample --seed 42

    # Full eligible-set rewrite.
    python gpt5_rewrite_candidateV2_reasoning.py \
        --out-dir ./candidateV2_reasoning_rewrite
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
from typing import Any

if __package__:
    from . import _phase2_process_common as common
    from . import gpt5_regenerate_phase2_process_data_V4 as phase2_v4
else:
    import _phase2_process_common as common
    import gpt5_regenerate_phase2_process_data_V4 as phase2_v4


HF_REPO = "yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV2"
CATEGORY = "Video_Games"
DEFAULT_MODEL = common.DEFAULT_MODEL
DEFAULT_PER_ENDPOINT = common.DEFAULT_PER_ENDPOINT
DEFAULT_MIN_PREDICTABILITY = 3
DEFAULT_MIN_QUALITY = 4
DEFAULT_NUM_CANDIDATES = 1
REFINE_MAX_COMPLETION_TOKENS = 2200
MAX_CANDIDATE_REPAIR_ATTEMPTS = 2
MAX_REVIEW_REPAIR_ATTEMPTS = 2
REWRITE_SCHEMA_VERSION = "candidateV2_flexible_reasoning_refine_v4"
REWRITE_OUTPUT_FORMAT = """<history_summary>
- HISTORY_SID[, HISTORY_SID...] => factual description shared by every cited SID
</history_summary>
<future_interests>
- [MODE] HISTORY_SID[, HISTORY_SID...] => possible interest and explicit history bridge
</future_interests>"""

REVIEW_KEYS = [
    "reasoning_path",
    "history_summary_factual",
    "history_summary_alignment",
    "target_interest_covered",
    "target_bridge_supported",
    "target_mode_correct",
    "target_identity_leakage",
    "overall_quality",
    "target_coverage_line_index",
    "audit",
]


GENERATOR_SYSTEM_PROMPT = """Improve OLD TRACE using HISTORY. Make small or large edits as needed.
The result must be more factual, coherent, concise, and useful. Every history-summary claim must be
explicit in every cited SID's metadata. Future interests must have valid history bridges: exploit is
directly observed; explore is one adjacent step. Never infer ownership or reveal item names. Output
only the two V4 blocks."""


GENERATOR_PROMPT = """HISTORY (chronological):
{history_block}

OLD TRACE:
{old_reasoning}

Refine candidate {candidate_number} of {num_candidates}:
{output_format}

Rules: Use only exact history SIDs. Use 1-3 summary lines; a line may group multiple SIDs when its
complete claim is true for each one. Use 2-4 future lines with at least one [exploit] and one [explore].
[exploit] is directly present in history. [explore] is one new interest reached through one explicit
shared attribute. Platform or brand alone is not a bridge. Use OLD TRACE as the draft, not as a
structural constraint."""


CANDIDATE_REPAIR_PROMPT = """Repair this refined candidate. Return only the two V4 blocks.
Use at most three summary lines and copy every SID verbatim from HISTORY. Multiple SIDs may share a
summary line only when the complete claim is explicit in every cited item's metadata.

HISTORY:
{history_block}

INVALID CANDIDATE:
{candidate}

VALIDATION ISSUE:
{validation_issue}

Required format:
{output_format}"""


REVIEWER_SYSTEM_PROMPT = """Finalize an improved V4 reasoning trace. You may revise any candidate
line. Every history-summary claim must be explicit in every cited SID's metadata. Keep distinct,
well-bridged exploit and explore interests. Ensure exactly one abstract target interest uses the tagged
mode and every tagged support SID. Do not leak target identity. Return strict JSON only. Quality 4
means factual, coherent, concise, and supported; 5 means exceptional."""


REVIEWER_PROMPT = """HISTORY:
{history_block}

PRIVATE HELD-OUT TARGET:
{target_block}

TARGET-SUPPORT TAG:
{tag_block}

CANDIDATES:
{candidates_block}

PREVIOUS INVALID REVIEW (empty on first pass):
{previous_review}

VALIDATION ISSUE (empty on first pass):
{validation_issue}

Return exactly these keys in this order:
{{
  "reasoning_path": "<history_summary>...escaped newlines...</future_interests>",
  "history_summary_factual": true,
    "history_summary_alignment": [true],
  "target_interest_covered": true,
  "target_bridge_supported": true,
  "target_mode_correct": true,
  "target_identity_leakage": false,
  "overall_quality": 1,
  "target_coverage_line_index": 1,
  "audit": "brief evidence-based audit"
}}

history_summary_alignment has one boolean per summary line. The 1-based target_coverage_line_index
identifies the only target-interest line; it must use [{target_support_mode}] and all tagged support
SIDs. Improve any part of the candidate when useful. Do not mention line positions in audit. Return
JSON only."""


def build_catalog(repo: str, category: str) -> dict[str, dict[str, str]]:
    dataset = common.load_dataset(repo, f"{category}_catalog", split="train")
    catalog = {}
    for row in dataset:
        sid = str(row["sid"])
        title = str(row.get("title") or "")
        detailed_description = common.process_description(
            row.get("detailed_description"),
            "",
        )
        description = detailed_description or common.process_description(
            row.get("description"),
            title,
        )
        catalog[sid] = {
            "title": title,
            "brand": str(row.get("brand") or ""),
            "description": description,
        }
    return catalog


def normalize_tag(
    row: dict[str, Any],
    history_sids: list[str],
) -> dict[str, Any]:
    mode = str(row.get("target_support_mode") or "").casefold()
    if mode not in {"exploit", "explore", "neither"}:
        raise ValueError(f"invalid target_support_mode: {mode!r}")
    try:
        predictability = int(row.get("target_predictability"))
        confidence = int(row.get("confidence"))
    except (TypeError, ValueError) as error:
        raise ValueError("target_predictability and confidence must be integers") from error
    if not 1 <= predictability <= 5 or not 1 <= confidence <= 5:
        raise ValueError("target_predictability and confidence must be in [1, 5]")

    supporting_sids = list(
        dict.fromkeys(
            str(value)
            for value in common._maybe_list(row.get("supporting_history_sids"))
        )
    )
    invalid_sids = sorted(set(supporting_sids) - set(history_sids))
    if invalid_sids:
        raise ValueError(f"tag cites non-history SIDs: {invalid_sids}")
    if mode == "neither" and supporting_sids:
        raise ValueError("neither tag must not contain supporting history SIDs")
    if mode != "neither" and not supporting_sids:
        raise ValueError(f"{mode} tag requires supporting history SIDs")

    return {
        "target_support_mode": mode,
        "target_relation": str(row.get("target_relation") or ""),
        "target_predictability": predictability,
        "supporting_history_sids": supporting_sids,
        "rationale": str(row.get("rationale") or ""),
        "confidence": confidence,
    }


def tag_is_eligible(tag: dict[str, Any], min_predictability: int) -> bool:
    return (
        tag["target_support_mode"] in {"exploit", "explore"}
        and tag["target_predictability"] >= min_predictability
    )


def tag_block(tag: dict[str, Any]) -> str:
    return json.dumps(tag, ensure_ascii=False, indent=2)


def generator_prompt(
    history_block: str,
    old_reasoning: str,
    candidate_number: int,
    num_candidates: int,
) -> str:
    return GENERATOR_PROMPT.format(
        history_block=history_block,
        old_reasoning=old_reasoning,
        candidate_number=candidate_number,
        num_candidates=num_candidates,
        output_format=REWRITE_OUTPUT_FORMAT,
    )


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("reviewer response contains no JSON object")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("reviewer response is not a JSON object")
    return value


def _future_interest_matches(reasoning_path: str) -> list[re.Match[str]]:
    trace = phase2_v4.parse_and_validate_generation(reasoning_path)
    matches = []
    for line in trace["future_interests"].splitlines():
        if not line.strip():
            continue
        match = phase2_v4.FUTURE_INTEREST_LINE_RE.fullmatch(line.strip())
        if match is None:
            raise ValueError(f"malformed future-interest line: {line!r}")
        matches.append(match)
    return matches


def _check_target_identity_leakage(
    reasoning_path: str,
    history_sids: list[str],
    target_sid: str,
    target_title: str,
) -> None:
    if target_sid not in set(history_sids) and target_sid in reasoning_path:
        raise ValueError("reasoning_path leaks the non-history target SID")
    normalized_reasoning = " ".join(reasoning_path.casefold().split())
    normalized_title = " ".join(target_title.casefold().split())
    if normalized_title and normalized_title in normalized_reasoning:
        raise ValueError("reasoning_path leaks the exact target title")


def validate_review(
    review: dict[str, Any],
    history_sids: list[str],
    target_sid: str,
    target_title: str,
    tag: dict[str, Any],
    min_quality: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    missing = [key for key in REVIEW_KEYS if key not in review]
    extra = [key for key in review if key not in REVIEW_KEYS]
    if missing or extra:
        raise ValueError(f"review schema mismatch; missing={missing}, extra={extra}")

    boolean_expectations = {
        "history_summary_factual": True,
        "target_interest_covered": True,
        "target_bridge_supported": True,
        "target_mode_correct": True,
        "target_identity_leakage": False,
    }
    for key, expected in boolean_expectations.items():
        if type(review[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
        if review[key] is not expected:
            raise ValueError(f"review rejected {key}: expected {expected}")

    quality = review["overall_quality"]
    if isinstance(quality, bool) or not isinstance(quality, int) or not 1 <= quality <= 5:
        raise ValueError("overall_quality must be an integer in [1, 5]")
    if quality < min_quality:
        raise ValueError(
            f"overall_quality={quality} is below required {min_quality}"
        )
    if not isinstance(review["audit"], str) or not review["audit"].strip():
        raise ValueError("audit must be a nonempty string")

    reasoning_path = review["reasoning_path"]
    if not isinstance(reasoning_path, str):
        raise ValueError("reasoning_path must be a string")
    trace = phase2_v4.parse_and_validate_generation(reasoning_path, history_sids)
    reasoning_path = phase2_v4.render_trace(trace)
    summary_lines = [
        line.strip()
        for line in trace["history_summary"].splitlines()
        if line.strip()
    ]
    for index, line in enumerate(summary_lines):
        match = phase2_v4.HISTORY_SUMMARY_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"malformed history-summary line: {line!r}")
        if not phase2_v4.ITEM_SID_RE.findall(match.group("evidence")):
            raise ValueError(f"history_summary[{index}] must cite history SIDs")

    alignment = review["history_summary_alignment"]
    if (
        not isinstance(alignment, list)
        or len(alignment) != len(summary_lines)
        or any(type(value) is not bool for value in alignment)
    ):
        raise ValueError(
            "history_summary_alignment must contain one boolean per summary line"
        )
    if not all(alignment):
        raise ValueError("review rejected at least one history-summary line")
    _check_target_identity_leakage(
        reasoning_path,
        history_sids,
        target_sid,
        target_title,
    )

    coverage_index = review["target_coverage_line_index"]
    matches = _future_interest_matches(reasoning_path)
    if (
        isinstance(coverage_index, bool)
        or not isinstance(coverage_index, int)
        or not 1 <= coverage_index <= len(matches)
    ):
        raise ValueError("target_coverage_line_index is outside future-interest lines")
    coverage_match = matches[coverage_index - 1]
    actual_mode = coverage_match.group("mode").casefold()
    expected_mode = tag["target_support_mode"]
    if actual_mode != expected_mode:
        raise ValueError(
            f"target coverage line mode={actual_mode}, expected {expected_mode}"
        )
    coverage_sids = set(phase2_v4.ITEM_SID_RE.findall(coverage_match.group("evidence")))
    required_sids = set(tag["supporting_history_sids"])
    if not required_sids <= coverage_sids:
        raise ValueError(
            "target coverage line omits tagged support SIDs: "
            f"{sorted(required_sids - coverage_sids)}"
        )

    normalized_review = dict(review)
    normalized_review["reasoning_path"] = reasoning_path
    return trace, normalized_review


def shuffle_future_interests(
    trace: dict[str, str],
    review: dict[str, Any],
    shuffle_key: str,
) -> tuple[dict[str, str], dict[str, Any]]:
    lines = [
        line.strip()
        for line in trace["future_interests"].splitlines()
        if line.strip()
    ]
    target_line = lines[review["target_coverage_line_index"] - 1]
    seed = int(hashlib.sha256(shuffle_key.encode("utf-8")).hexdigest()[:16], 16)
    random.Random(seed).shuffle(lines)

    shuffled_trace = dict(trace)
    shuffled_trace["future_interests"] = "\n".join(lines)
    shuffled_review = dict(review)
    shuffled_review["target_coverage_line_index"] = lines.index(target_line) + 1
    shuffled_review["reasoning_path"] = phase2_v4.render_trace(shuffled_trace)
    return shuffled_trace, shuffled_review


def generate_candidates(
    client: Any,
    model: str,
    history_sids: list[str],
    history_block: str,
    old_reasoning: str,
    num_candidates: int,
) -> list[str]:
    candidates = []
    for candidate_number in range(1, num_candidates + 1):
        raw = common.chat(
            client,
            model,
            GENERATOR_SYSTEM_PROMPT,
            generator_prompt(
                history_block,
                old_reasoning,
                candidate_number,
                num_candidates,
            ),
            max_completion_tokens=REFINE_MAX_COMPLETION_TOKENS,
        )
        for repair_index in range(MAX_CANDIDATE_REPAIR_ATTEMPTS + 1):
            try:
                trace = phase2_v4.parse_and_validate_generation(raw, history_sids)
                candidates.append(phase2_v4.render_trace(trace))
                break
            except (phase2_v4.TraceValidationError, ValueError) as error:
                if repair_index == MAX_CANDIDATE_REPAIR_ATTEMPTS:
                    raise
                raw = common.chat(
                    client,
                    model,
                    GENERATOR_SYSTEM_PROMPT,
                    CANDIDATE_REPAIR_PROMPT.format(
                        history_block=history_block,
                        candidate=raw,
                        validation_issue=str(error),
                        output_format=REWRITE_OUTPUT_FORMAT,
                    ),
                    max_completion_tokens=REFINE_MAX_COMPLETION_TOKENS,
                )
    return candidates


def review_candidates(
    client: Any,
    model: str,
    category: str,
    history_sids: list[str],
    history_block: str,
    target_sid: str,
    target_title: str,
    target_block: str,
    tag: dict[str, Any],
    candidates: list[str],
    min_quality: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    candidates_block = "\n\n".join(
        f"CANDIDATE {index}:\n{candidate}"
        for index, candidate in enumerate(candidates, start=1)
    )
    previous_review = ""
    validation_issue = ""
    for repair_index in range(MAX_REVIEW_REPAIR_ATTEMPTS + 1):
        raw = common.chat(
            client,
            model,
            REVIEWER_SYSTEM_PROMPT,
            REVIEWER_PROMPT.format(
                category=category,
                history_block=history_block,
                target_block=target_block,
                tag_block=tag_block(tag),
                candidates_block=candidates_block,
                previous_review=previous_review,
                validation_issue=validation_issue,
                target_support_mode=tag["target_support_mode"],
            ),
            max_completion_tokens=REFINE_MAX_COMPLETION_TOKENS,
        )
        try:
            review = _parse_json_object(raw)
            trace, normalized_review = validate_review(
                review,
                history_sids,
                target_sid,
                target_title,
                tag,
                min_quality,
            )
            return trace, normalized_review
        except (ValueError, json.JSONDecodeError, phase2_v4.TraceValidationError) as error:
            if repair_index == MAX_REVIEW_REPAIR_ATTEMPTS:
                raise
            previous_review = raw
            validation_issue = str(error)
    raise AssertionError("unreachable")


def generation_signature(
    repo: str,
    model: str,
    min_predictability: int,
    min_quality: int,
    num_candidates: int,
    keep_candidates: bool,
) -> str:
    payload = {
        "schema": REWRITE_SCHEMA_VERSION,
        "repo": repo,
        "model": model,
        "reasoning_effort": common.REASONING_EFFORT,
        "max_completion_tokens": REFINE_MAX_COMPLETION_TOKENS,
        "min_predictability": min_predictability,
        "min_quality": min_quality,
        "num_candidates": num_candidates,
        "keep_candidates": keep_candidates,
        "max_candidate_repair_attempts": MAX_CANDIDATE_REPAIR_ATTEMPTS,
        "max_review_repair_attempts": MAX_REVIEW_REPAIR_ATTEMPTS,
        "future_interest_order": "sha256_generation_signature_and_row_key",
        "generator": GENERATOR_SYSTEM_PROMPT + GENERATOR_PROMPT,
        "candidate_repair": CANDIDATE_REPAIR_PROMPT,
        "reviewer": REVIEWER_SYSTEM_PROMPT + REVIEWER_PROMPT,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]


def build_output_row(
    row_key: str,
    source_index: int,
    row: dict[str, Any],
    trace: dict[str, str],
    review: dict[str, Any],
    candidates: list[str],
    model: str,
    signature: str,
    keep_candidates: bool,
) -> dict[str, Any]:
    original_reasoning = str(row.get("reasoning_path") or "")
    reasoning_path = phase2_v4.render_trace(trace)
    result = dict(row)
    result.update(
        {
            "row_key": row_key,
            "source_index": source_index,
            "original_reasoning_path": original_reasoning,
            "reasoning_path": reasoning_path,
            "history_summary_text": trace["history_summary"],
            "future_interests_text": trace["future_interests"],
            "rewrite_review_json": json.dumps(
                review,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            "rewrite_history_summary_factual": review[
                "history_summary_factual"
            ],
            "rewrite_history_summary_alignment_json": json.dumps(
                review["history_summary_alignment"],
                separators=(",", ":"),
            ),
            "rewrite_target_interest_covered": review[
                "target_interest_covered"
            ],
            "rewrite_target_bridge_supported": review[
                "target_bridge_supported"
            ],
            "rewrite_target_mode_correct": review["target_mode_correct"],
            "rewrite_target_identity_leakage": review[
                "target_identity_leakage"
            ],
            "rewrite_overall_quality": review["overall_quality"],
            "rewrite_target_coverage_line_index": review[
                "target_coverage_line_index"
            ],
            "rewrite_audit": review["audit"],
            "rewrite_schema_version": REWRITE_SCHEMA_VERSION,
            "generation_signature": signature,
            "rewrite_generation_signature": signature,
            "rewrite_generation_model": model,
            "rewrite_candidate_count": len(candidates),
        }
    )
    if row.get("integrated_narrative") == original_reasoning:
        result["integrated_narrative"] = reasoning_path
    if keep_candidates:
        result["rewrite_candidates_json"] = json.dumps(
            candidates,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return result


def selected_indices(
    total: int,
    source_indices: list[int] | None,
    limit: int,
    random_sample: bool,
    seed: int,
) -> list[int]:
    if source_indices is not None:
        invalid = [index for index in source_indices if not 0 <= index < total]
        if invalid:
            raise ValueError(f"source indices outside [0, {total}): {invalid}")
        return list(dict.fromkeys(source_indices))
    return list(
        common.select_source_indices(total, limit, random_sample, seed)
    )


def rewrite(
    repo: str,
    category: str,
    out_path: str,
    csv_paths: list[str],
    endpoints: list[str],
    per_endpoint: int,
    source_indices: list[int] | None,
    limit: int,
    random_sample: bool,
    seed: int,
    model: str,
    min_predictability: int,
    min_quality: int,
    num_candidates: int,
    keep_candidates: bool,
    dry_run: bool,
    get_client: Any = None,
) -> None:
    source = common.load_dataset(repo, f"{category}_reasoning", split="train")
    indices = selected_indices(
        len(source),
        source_indices,
        limit,
        random_sample,
        seed,
    )
    catalog = build_catalog(repo, category)
    signature = generation_signature(
        repo,
        model,
        min_predictability,
        min_quality,
        num_candidates,
        keep_candidates,
    )
    done = common.load_done_keys(out_path, signature)

    tasks = []
    completed_selected = 0
    skipped_ineligible = 0
    for source_index in indices:
        row = dict(source[source_index])
        history_sids, _, _ = common.history_from_row(row, catalog)
        tag = normalize_tag(row, history_sids)
        if not tag_is_eligible(tag, min_predictability):
            skipped_ineligible += 1
            continue
        row_key = common.row_key_for(row, source_index)
        if row_key in done:
            completed_selected += 1
        else:
            tasks.append((row_key, source_index, row))
    print(
        f"[candidateV2-rewrite] selected={len(indices)} "
        f"eligible={len(tasks) + completed_selected} pending={len(tasks)} "
        f"done={completed_selected} skipped_ineligible={skipped_ineligible}"
    )

    if dry_run:
        if not tasks:
            print("[candidateV2-rewrite] no pending eligible row available")
            return
        _, source_index, row = tasks[0]
        history_sids, _, history_block = common.history_from_row(row, catalog)
        print(f"[candidateV2-rewrite] dry-run source_index={source_index}")
        print(
            generator_prompt(
                history_block,
                str(row.get("reasoning_path") or ""),
                1,
                num_candidates,
            )
        )
        return

    def process(
        client: Any,
        row_key: str,
        source_index: int,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        history_sids, _, history_block = common.history_from_row(row, catalog)
        target_sid = str(row.get("item_sid") or "")
        target_title = str(row.get("item_title") or "")
        target_block = common.target_guidance_from_row(row, catalog)
        tag = normalize_tag(row, history_sids)
        candidates = generate_candidates(
            client,
            model,
            history_sids,
            history_block,
            str(row.get("reasoning_path") or ""),
            num_candidates,
        )
        trace, review = review_candidates(
            client,
            model,
            category,
            history_sids,
            history_block,
            target_sid,
            target_title,
            target_block,
            tag,
            candidates,
            min_quality,
        )
        trace, review = shuffle_future_interests(
            trace,
            review,
            f"{signature}:{row_key}",
        )
        trace, review = validate_review(
            review,
            history_sids,
            target_sid,
            target_title,
            tag,
            min_quality,
        )
        return build_output_row(
            row_key,
            source_index,
            row,
            trace,
            review,
            candidates,
            model,
            signature,
            keep_candidates,
        )

    if get_client is None:
        raise RuntimeError("generation requires an Azure client factory")
    common.run_pool(
        tasks,
        process,
        out_path,
        csv_paths,
        endpoints,
        per_endpoint,
        get_client,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rewrite candidateV2 reasoning with tag-guided target coverage."
    )
    parser.add_argument("--hf-repo", default=HF_REPO)
    parser.add_argument("--category", default=CATEGORY, choices=[CATEGORY])
    parser.add_argument("--out-dir", default="./candidateV2_reasoning_rewrite")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--per-endpoint", type=int, default=DEFAULT_PER_ENDPOINT)
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--min-predictability", type=int, default=DEFAULT_MIN_PREDICTABILITY)
    parser.add_argument("--min-quality", type=int, default=DEFAULT_MIN_QUALITY)
    parser.add_argument("--num-candidates", type=int, default=DEFAULT_NUM_CANDIDATES)
    parser.add_argument("--source-indices", nargs="*", type=int, default=None)
    parser.add_argument("--limit", type=int, default=-1)
    parser.add_argument("--random-sample", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--keep-candidates", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.per_endpoint < 1:
        parser.error("--per-endpoint must be at least 1")
    if not 1 <= args.min_predictability <= 5:
        parser.error("--min-predictability must be in [1, 5]")
    if not 1 <= args.min_quality <= 5:
        parser.error("--min-quality must be in [1, 5]")
    if args.num_candidates < 1:
        parser.error("--num-candidates must be at least 1")

    os.makedirs(args.out_dir, exist_ok=True)
    output_jsonl = os.path.join(
        args.out_dir,
        f"{args.category}.reasoning_rewrite.jsonl",
    )
    output_csvs = [output_jsonl.replace(".jsonl", ".csv")]
    lock_path = os.path.join(
        args.out_dir,
        f".{args.category}.reasoning_rewrite.lock",
    )
    with common.single_process_lock(lock_path):
        get_client = None
        endpoints = []
        if not args.dry_run:
            configured_endpoints, get_client = common.load_endpoint_helpers()
            endpoints = args.endpoints or configured_endpoints
            unknown = [
                endpoint
                for endpoint in endpoints
                if endpoint not in configured_endpoints
            ]
            if unknown:
                parser.error(f"unknown endpoint(s): {unknown}")
            common.reconcile_output_mirrors(output_jsonl, output_csvs, None)

        rewrite(
            repo=args.hf_repo,
            category=args.category,
            out_path=output_jsonl,
            csv_paths=output_csvs,
            endpoints=endpoints,
            per_endpoint=args.per_endpoint,
            source_indices=args.source_indices,
            limit=args.limit,
            random_sample=args.random_sample,
            seed=args.seed,
            model=args.model,
            min_predictability=args.min_predictability,
            min_quality=args.min_quality,
            num_candidates=args.num_candidates,
            keep_candidates=args.keep_candidates,
            dry_run=args.dry_run,
            get_client=get_client,
        )
        if not args.dry_run:
            for output_csv in output_csvs:
                common.jsonl_to_csv(output_jsonl, output_csv)


if __name__ == "__main__":
    main()