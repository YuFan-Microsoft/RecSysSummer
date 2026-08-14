"""Check V4 reasoning traces in a JSONL file using only the Python standard library.

The checker accepts common field-name variants used by SIDReasoner inference
outputs. Explicit field names can be supplied when a file uses another schema.

Example:

    python3 check_reasoning_jsonl_format.py inference.jsonl

This writes ``inference.reasoning_check.jsonl`` and prints a JSON summary. The
process exits with status 1 when any row is invalid, and status 2 for a fatal
input/output error. Per-row stats include the live strict process-reward
components and beam-10 distinct SID0 count. The summary reports the mean SID0
count and its normalized rate across rows with complete valid beam-10 outputs.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any


SID_PATTERN = r"<a_\d+><b_\d+><c_\d+>"
SID_RE = re.compile(SID_PATTERN)
SID0_RE = re.compile(r"<a_\d+>")
CITATIONS_PATTERN = rf"{SID_PATTERN}(?:\s*,\s*{SID_PATTERN})*"
SUMMARY_LINE_RE = re.compile(
    rf"^-\s+(?P<citations>{CITATIONS_PATTERN})\s*=>\s*(?P<text>\S.*)$"
)
FUTURE_LINE_RE = re.compile(
    rf"^-\s+\[(?P<mode>exploit|explore)\]\s+"
    rf"(?P<citations>{CITATIONS_PATTERN})\s*=>\s*(?P<text>\S.*)$",
    re.IGNORECASE,
)
SECTION_PATTERNS = {
    tag: re.compile(fr"<{tag}>\s*(.*?)\s*</{tag}>", re.DOTALL)
    for tag in ("history_summary", "future_interests")
}


def _normalize_history_sids(history_sids: Any) -> set[str]:
    if history_sids is None:
        return set()
    if isinstance(history_sids, str):
        return set(SID_RE.findall(history_sids))

    normalized = set()
    for value in history_sids:
        matches = SID_RE.findall(str(value))
        if matches:
            normalized.add(matches[0])
    return normalized


def _nonempty_lines(block: str) -> list[str]:
    return [line.strip() for line in block.splitlines() if line.strip()]


def _citation_set(line_match: re.Match[str]) -> set[str]:
    return set(SID_RE.findall(line_match.group("citations")))


def _grounding_fraction(
    line_matches: list[re.Match[str] | None],
    history_sid_set: set[str],
) -> float:
    if not line_matches:
        return 0.0
    grounded_count = sum(
        line_match is not None and _citation_set(line_match) <= history_sid_set
        for line_match in line_matches
    )
    return grounded_count / len(line_matches)


def _history_reference_coverage(
    line_matches: list[re.Match[str] | None],
    history_sid_set: set[str],
) -> float:
    if not history_sid_set:
        return 0.0
    referenced_sids = set().union(
        *(
            _citation_set(line_match)
            for line_match in line_matches
            if line_match is not None
        )
    )
    return len(referenced_sids & history_sid_set) / len(history_sid_set)


def _latest_history_sid(history_sids: Any) -> str | None:
    if history_sids is None:
        return None
    if isinstance(history_sids, str):
        matches = SID_RE.findall(history_sids)
        return matches[-1] if matches else None

    latest_sid = None
    for value in history_sids:
        matches = SID_RE.findall(str(value))
        if matches:
            latest_sid = matches[0]
    return latest_sid


def calculate_process_rewards(
    solution_str: str,
    history_sids: Any,
) -> dict[str, float]:
    """Apply the current strict V4 format and grounding hard gate."""
    zero_scores = {
        "history_summary_grounding_reward": 0.0,
        "future_interests_grounding_reward": 0.0,
        "format_reward": 0.0,
        "history_reference_coverage": 0.0,
        "latest_history_summary_reference_reward": 0.0,
        "process_reward": 0.0,
    }
    if not isinstance(solution_str, str) or solution_str.count("</think>") != 1:
        return zero_scores

    reasoning, _ = solution_str.split("</think>", maxsplit=1)
    sections = {}
    positions = []
    remainder = reasoning.strip()
    for tag, pattern in SECTION_PATTERNS.items():
        matches = list(pattern.finditer(reasoning))
        if len(matches) != 1:
            return zero_scores
        match = matches[0]
        sections[tag] = match.group(1).strip()
        positions.append((tag, match.start()))
        remainder = pattern.sub("", remainder, count=1)

    actual_order = [tag for tag, _ in sorted(positions, key=lambda item: item[1])]
    if actual_order != ["history_summary", "future_interests"]:
        return zero_scores
    if remainder.removeprefix("<think>").strip():
        return zero_scores

    summary_lines = _nonempty_lines(sections["history_summary"])
    future_lines = _nonempty_lines(sections["future_interests"])
    parsed_summary = [SUMMARY_LINE_RE.fullmatch(line) for line in summary_lines]
    parsed_future = [FUTURE_LINE_RE.fullmatch(line) for line in future_lines]
    modes = {
        line_match.group("mode").casefold()
        for line_match in parsed_future
        if line_match is not None
    }
    format_reward = float(
        1 <= len(summary_lines) <= 3
        and 2 <= len(future_lines) <= 4
        and all(line_match is not None for line_match in parsed_summary)
        and all(line_match is not None for line_match in parsed_future)
        and modes == {"exploit", "explore"}
    )

    history_sid_set = _normalize_history_sids(history_sids)
    history_grounding = _grounding_fraction(parsed_summary, history_sid_set)
    future_grounding = _grounding_fraction(parsed_future, history_sid_set)
    history_coverage = _history_reference_coverage(
        parsed_summary + parsed_future,
        history_sid_set,
    )
    latest_sid = _latest_history_sid(history_sids)
    summary_citations = set().union(
        *(
            _citation_set(line_match)
            for line_match in parsed_summary
            if line_match is not None
        )
    )
    latest_reference = float(latest_sid is not None and latest_sid in summary_citations)
    process_reward = float(
        format_reward == 1.0
        and history_grounding == 1.0
        and future_grounding == 1.0
        and latest_reference == 1.0
    )
    return {
        "history_summary_grounding_reward": history_grounding,
        "future_interests_grounding_reward": future_grounding,
        "format_reward": format_reward,
        "history_reference_coverage": history_coverage,
        "latest_history_summary_reference_reward": latest_reference,
        "process_reward": process_reward,
    }

FIELD_ALIASES = {
    "history_sids": (
        "history_sid_list",
        "history_item_sid",
        "history_sids",
        "history_sid",
    ),
    "history_titles": (
        "history_title_list",
        "history_item_title",
        "history_titles",
        "history_title",
    ),
    "target_sid": ("item_sid", "target_sid", "ground_truth_sid"),
    "target_title": ("item_title", "target_title", "ground_truth_title"),
    "reasoning": (
        "generated_reasoning_path",
        "reasoning_path",
        "reasoning",
        "cot",
        "raw_reasoning_output",
    ),
    "beams": (
        "prediction_beam_10",
        "sid_beams",
        "beam_predictions",
        "sid_beam_predictions",
        "predict_sid",
        "predicted_sids",
        "beam_10",
    ),
}


class RowChecker:
    def __init__(self, args: argparse.Namespace):
        self.args = args

    @staticmethod
    def _issue(code: str, message: str) -> dict[str, str]:
        return {"code": code, "message": message}

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            text = value.strip()
            if text.startswith(("[", "(")):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    try:
                        parsed = ast.literal_eval(text)
                    except (SyntaxError, ValueError):
                        return [value]
                if isinstance(parsed, (list, tuple)):
                    return list(parsed)
            return [value]
        return [value]

    def _find_field(
        self,
        row: dict[str, Any],
        logical_name: str,
    ) -> tuple[str | None, Any]:
        explicit = getattr(self.args, f"{logical_name}_field")
        candidates = (explicit,) if explicit else FIELD_ALIASES[logical_name]
        for field_name in candidates:
            if field_name in row:
                return field_name, row[field_name]
        return None, None

    def _history(
        self,
        row: dict[str, Any],
        errors: list[dict[str, str]],
    ) -> tuple[list[str], list[str], dict[str, str]]:
        detected = {}
        sid_field, sid_value = self._find_field(row, "history_sids")
        title_field, title_value = self._find_field(row, "history_titles")

        if sid_field is None and isinstance(row.get("history"), list):
            history = row["history"]
            if all(isinstance(item, dict) for item in history):
                detected["history_sids"] = "history[].sid"
                detected["history_titles"] = "history[].title"
                return (
                    [str(item.get("sid") or "") for item in history],
                    [str(item.get("title") or "") for item in history],
                    detected,
                )

        if sid_field is None:
            errors.append(
                self._issue("missing_history_sids", "history SID field is missing")
            )
            return [], [], detected

        detected["history_sids"] = sid_field
        history_sids = [str(value) for value in self._as_list(sid_value)]
        if title_field is not None:
            detected["history_titles"] = title_field
            history_titles = [str(value) for value in self._as_list(title_value)]
        else:
            history_titles = []

        if not history_sids:
            errors.append(
                self._issue("empty_history_sids", "history SID list is empty")
            )
        for index, sid in enumerate(history_sids):
            if SID_RE.fullmatch(sid) is None:
                errors.append(
                    self._issue(
                        "malformed_history_sid",
                        f"history_sids[{index}] is malformed: {sid!r}",
                    )
                )
        if title_field is None:
            errors.append(
                self._issue("missing_history_titles", "history title field is missing")
            )
        elif len(history_titles) != len(history_sids):
            errors.append(
                self._issue(
                    "history_length_mismatch",
                    "history SID and title lists have different lengths: "
                    f"{len(history_sids)} != {len(history_titles)}",
                )
            )
        return history_sids, history_titles, detected

    def _target(
        self,
        row: dict[str, Any],
        errors: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, str]]:
        detected = {}
        sid_field, sid_value = self._find_field(row, "target_sid")
        title_field, title_value = self._find_field(row, "target_title")

        target_object = row.get("target")
        if isinstance(target_object, dict):
            if sid_field is None and "sid" in target_object:
                sid_field, sid_value = "target.sid", target_object["sid"]
            if title_field is None and "title" in target_object:
                title_field, title_value = "target.title", target_object["title"]

        if sid_field is None:
            errors.append(self._issue("missing_target_sid", "target SID is missing"))
            target_sid = ""
        else:
            detected["target_sid"] = sid_field
            target_sid = str(sid_value or "")
            if SID_RE.fullmatch(target_sid) is None:
                errors.append(
                    self._issue(
                        "malformed_target_sid",
                        f"target SID is malformed: {target_sid!r}",
                    )
                )

        if title_field is None:
            errors.append(
                self._issue("missing_target_title", "target title is missing")
            )
            target_title = ""
        else:
            detected["target_title"] = title_field
            target_title = str(title_value or "")
            if not target_title.strip():
                errors.append(
                    self._issue("empty_target_title", "target title is empty")
                )
        return target_sid, target_title, detected

    @staticmethod
    def _extract_reasoning_text(
        raw: str,
        errors: list[dict[str, str]],
    ) -> tuple[str, str]:
        text = raw.strip()
        closing_count = text.count("</think>")
        opening_count = text.count("<think>")
        if closing_count == 0 and opening_count == 0:
            return text, "reasoning_path"
        if closing_count == 0 and opening_count == 1 and text.startswith("<think>"):
            return text[len("<think>") :].strip(), "open_think_reasoning_path"
        if closing_count != 1 or opening_count not in (0, 1):
            errors.append(
                RowChecker._issue(
                    "invalid_think_wrapper",
                    "expected either no think wrapper or exactly one optional "
                    f"<think> and one </think>; found {opening_count}/{closing_count}",
                )
            )
            return text, "invalid_wrapper"

        reasoning, suffix = text.split("</think>", 1)
        reasoning = reasoning.strip()
        if opening_count == 1:
            if not reasoning.startswith("<think>"):
                errors.append(
                    RowChecker._issue(
                        "misplaced_think_open",
                        "<think> must appear before the reasoning blocks",
                    )
                )
            else:
                reasoning = reasoning[len("<think>") :].strip()
        suffix = suffix.strip()
        if suffix and SID_RE.fullmatch(suffix) is None:
            errors.append(
                RowChecker._issue(
                    "invalid_response_suffix",
                    "text after </think> must be empty or one full SID",
                )
            )
        return reasoning, "full_response"

    @staticmethod
    def _extract_sections(
        reasoning: str,
        errors: list[dict[str, str]],
    ) -> dict[str, str]:
        sections = {}
        positions = []
        remainder = reasoning
        for tag, pattern in SECTION_PATTERNS.items():
            matches = list(pattern.finditer(reasoning))
            if len(matches) != 1:
                errors.append(
                    RowChecker._issue(
                        "section_count",
                        f"expected exactly one <{tag}>...</{tag}> block; "
                        f"found {len(matches)}",
                    )
                )
                continue
            match = matches[0]
            sections[tag] = match.group(1).strip()
            positions.append((tag, match.start()))
            remainder = pattern.sub("", remainder, count=1)

        if len(positions) == 2:
            actual_order = [
                tag for tag, _ in sorted(positions, key=lambda item: item[1])
            ]
            if actual_order != ["history_summary", "future_interests"]:
                errors.append(
                    RowChecker._issue(
                        "section_order",
                        "blocks must appear in history_summary, future_interests order",
                    )
                )
        if len(sections) == 2 and remainder.strip():
            errors.append(
                RowChecker._issue(
                    "outside_text",
                    "text exists outside the two required reasoning blocks",
                )
            )
        return sections

    @staticmethod
    def _citation_sids(match: re.Match[str]) -> list[str]:
        return SID_RE.findall(match.group("citations"))

    def _validate_reasoning(
        self,
        reasoning: str,
        history_sids: list[str],
        history_titles: list[str],
        target_sid: str,
        target_title: str,
        errors: list[dict[str, str]],
        warnings: list[dict[str, str]],
    ) -> dict[str, Any]:
        sections = self._extract_sections(reasoning, errors)
        stats: dict[str, Any] = {
            "history_summary_lines": 0,
            "future_interest_lines": 0,
            "future_modes": [],
        }
        history_sid_set = set(history_sids)

        summary_lines = [
            line.strip()
            for line in sections.get("history_summary", "").splitlines()
            if line.strip()
        ]
        stats["history_summary_lines"] = len(summary_lines)
        if not 1 <= len(summary_lines) <= 3:
            errors.append(
                self._issue(
                    "history_summary_count",
                    f"history_summary must contain 1-3 lines; found {len(summary_lines)}",
                )
            )
        normalized_summary_texts = []
        summary_cited_sids = set()
        for index, line in enumerate(summary_lines):
            match = SUMMARY_LINE_RE.fullmatch(line)
            if match is None:
                errors.append(
                    self._issue(
                        "history_summary_syntax",
                        f"history_summary[{index}] must use '- SID[, SID...] => text'",
                    )
                )
                continue
            citations = self._citation_sids(match)
            summary_cited_sids.update(citations)
            invalid = sorted(set(citations) - history_sid_set)
            if invalid:
                errors.append(
                    self._issue(
                        "non_history_summary_sid",
                        f"history_summary[{index}] cites non-history SIDs: {invalid}",
                    )
                )
            normalized_summary_texts.append(" ".join(match.group("text").casefold().split()))

        if len(normalized_summary_texts) != len(set(normalized_summary_texts)):
            errors.append(
                self._issue(
                    "duplicate_history_summary",
                    "history_summary contains duplicate normalized claims",
                )
            )

        if history_sids and history_sids[-1] not in summary_cited_sids:
            errors.append(
                self._issue(
                    "latest_history_sid_missing_from_summary",
                    "the latest history SID must be cited in history_summary",
                )
            )

        interest_lines = [
            line.strip()
            for line in sections.get("future_interests", "").splitlines()
            if line.strip()
        ]
        stats["future_interest_lines"] = len(interest_lines)
        if not 2 <= len(interest_lines) <= 4:
            errors.append(
                self._issue(
                    "future_interest_count",
                    f"future_interests must contain 2-4 lines; found {len(interest_lines)}",
                )
            )
        modes = []
        normalized_interest_texts = []
        for index, line in enumerate(interest_lines):
            match = FUTURE_LINE_RE.fullmatch(line)
            if match is None:
                errors.append(
                    self._issue(
                        "future_interest_syntax",
                        "future_interests["
                        f"{index}] must use '- [exploit|explore] SID[, SID...] => text'",
                    )
                )
                continue
            mode = match.group("mode").casefold()
            modes.append(mode)
            citations = self._citation_sids(match)
            invalid = sorted(set(citations) - history_sid_set)
            if invalid:
                errors.append(
                    self._issue(
                        "non_history_future_sid",
                        f"future_interests[{index}] cites non-history SIDs: {invalid}",
                    )
                )
            normalized_interest_texts.append(" ".join(match.group("text").casefold().split()))

        stats["future_modes"] = modes
        if set(modes) != {"exploit", "explore"}:
            errors.append(
                self._issue(
                    "missing_future_mode",
                    "future_interests must contain at least one exploit and one explore",
                )
            )
        if len(normalized_interest_texts) != len(set(normalized_interest_texts)):
            errors.append(
                self._issue(
                    "duplicate_future_interest",
                    "future_interests contains duplicate normalized claims",
                )
            )

        if target_sid and target_sid not in history_sid_set and target_sid in reasoning:
            errors.append(
                self._issue(
                    "target_sid_leakage",
                    "reasoning contains the non-history target SID",
                )
            )
        normalized_reasoning = " ".join(reasoning.casefold().split())
        normalized_target_title = " ".join(target_title.casefold().split())
        if normalized_target_title and normalized_target_title in normalized_reasoning:
            errors.append(
                self._issue(
                    "target_title_leakage",
                    "reasoning contains the exact target title",
                )
            )

        for title in history_titles:
            normalized_title = " ".join(title.casefold().split())
            if len(normalized_title) >= 8 and normalized_title in normalized_reasoning:
                warnings.append(
                    self._issue(
                        "history_title_mentioned",
                        f"reasoning may reveal a history item title: {title!r}",
                    )
                )
        return stats

    def _validate_beams(
        self,
        row: dict[str, Any],
        target_sid: str,
        errors: list[dict[str, str]],
        warnings: list[dict[str, str]],
    ) -> tuple[dict[str, Any], dict[str, str]]:
        detected = {}
        beam_field, beam_value = self._find_field(row, "beams")
        if beam_field is None:
            errors.append(self._issue("missing_beams", "beam prediction field is missing"))
            return {
                "beam_count": 0,
                "target_rank": None,
                "beam_distinct_sid0": None,
            }, detected
        detected["beams"] = beam_field
        raw_beams = self._as_list(beam_value)
        beams = []
        sid0_tokens = []
        beams_are_valid = True
        for index, value in enumerate(raw_beams):
            if isinstance(value, dict):
                value = value.get("sid", value.get("predicted_sid", ""))
            sid = str(value)
            beams.append(sid)
            if SID_RE.fullmatch(sid) is None:
                beams_are_valid = False
                errors.append(
                    self._issue(
                        "malformed_beam_sid",
                        f"beams[{index}] is malformed: {sid!r}",
                    )
                )
            else:
                sid0_match = SID0_RE.match(sid)
                if sid0_match is None:
                    raise RuntimeError(f"Unable to extract SID0 from valid SID {sid!r}")
                sid0_tokens.append(sid0_match.group(0))
        if len(beams) != self.args.expected_beams:
            beams_are_valid = False
            errors.append(
                self._issue(
                    "beam_count",
                    f"expected {self.args.expected_beams} beams; found {len(beams)}",
                )
            )
        if len(beams) != len(set(beams)):
            warnings.append(
                self._issue("duplicate_beams", "beam predictions contain duplicate SIDs")
            )
        target_rank = None
        if target_sid in beams:
            target_rank = beams.index(target_sid) + 1
        distinct_sid0 = len(set(sid0_tokens)) if beams_are_valid else None
        return {
            "beam_count": len(beams),
            "target_rank": target_rank,
            "beam_distinct_sid0": distinct_sid0,
        }, detected

    def check(self, row: Any, line_number: int) -> dict[str, Any]:
        errors: list[dict[str, str]] = []
        warnings: list[dict[str, str]] = []
        if not isinstance(row, dict):
            errors.append(self._issue("row_not_object", "JSONL row must be an object"))
            return {
                "line_number": line_number,
                "valid": False,
                "errors": errors,
                "warnings": warnings,
            }

        history_sids, history_titles, detected_history = self._history(row, errors)
        target_sid, target_title, detected_target = self._target(row, errors)
        reasoning_field, reasoning_value = self._find_field(row, "reasoning")
        detected = {**detected_history, **detected_target}
        stats: dict[str, Any] = {
            "history_count": len(history_sids),
            "history_summary_lines": 0,
            "future_interest_lines": 0,
            "future_modes": [],
            "beam_count": 0,
            "target_rank": None,
            "beam_distinct_sid0": None,
        }

        if reasoning_field is None:
            errors.append(
                self._issue("missing_reasoning", "reasoning field is missing")
            )
        elif not isinstance(reasoning_value, str) or not reasoning_value.strip():
            errors.append(
                self._issue("invalid_reasoning", "reasoning must be a nonempty string")
            )
        else:
            detected["reasoning"] = reasoning_field
            reasoning, container = self._extract_reasoning_text(
                reasoning_value,
                errors,
            )
            stats["reasoning_container"] = container
            process_input = (
                reasoning_value
                if container in {"full_response", "invalid_wrapper"}
                else f"{reasoning}</think>"
            )
            process_rewards = calculate_process_rewards(process_input, history_sids)
            stats.update(process_rewards)
            stats["format_valid"] = process_rewards["format_reward"] == 1.0
            stats["process_valid"] = process_rewards["process_reward"] == 1.0
            if process_rewards["process_reward"] != 1.0:
                errors.append(
                    self._issue(
                        "process_reward_hard_gate",
                        "reasoning fails the current strict process-reward definition",
                    )
                )
            stats.update(
                self._validate_reasoning(
                    reasoning,
                    history_sids,
                    history_titles,
                    target_sid,
                    target_title,
                    errors,
                    warnings,
                )
            )

        beam_stats, detected_beams = self._validate_beams(
            row,
            target_sid,
            errors,
            warnings,
        )
        stats.update(beam_stats)
        detected.update(detected_beams)
        return {
            "line_number": line_number,
            "source_index": row.get("source_index"),
            "user_id": row.get("user_id"),
            "valid": not errors and (not self.args.warnings_as_errors or not warnings),
            "errors": errors,
            "warnings": warnings,
            "stats": stats,
            "detected_fields": detected,
        }


def default_output_path(input_path: Path) -> Path:
    if input_path.suffix == ".jsonl":
        return input_path.with_name(input_path.stem + ".reasoning_check.jsonl")
    return input_path.with_name(input_path.name + ".reasoning_check.jsonl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check V4 reasoning format and beam-10 fields in a JSONL file."
    )
    parser.add_argument("input_jsonl", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--expected-beams", type=int, default=10)
    parser.add_argument("--invalid-only", action="store_true")
    parser.add_argument("--warnings-as-errors", action="store_true")
    for logical_name in FIELD_ALIASES:
        parser.add_argument(
            f"--{logical_name.replace('_', '-')}-field",
            default=None,
            help=f"Override the field used for {logical_name}.",
        )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.expected_beams < 1:
        parser.error("--expected-beams must be at least 1")

    input_path = args.input_jsonl
    output_path = args.output or default_output_path(input_path)
    try:
        if input_path.resolve() == output_path.resolve():
            raise ValueError("input and output paths must be different")
        input_handle = input_path.open("r", encoding="utf-8")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_handle = output_path.open("w", encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"fatal: {error}", file=sys.stderr)
        return 2

    checker = RowChecker(args)
    total = 0
    valid = 0
    invalid = 0
    warning_rows = 0
    beam_diversity_counts = []
    error_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()
    with input_handle, output_handle:
        for line_number, raw_line in enumerate(input_handle, start=1):
            if not raw_line.strip():
                continue
            total += 1
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as error:
                result = {
                    "line_number": line_number,
                    "valid": False,
                    "errors": [
                        checker._issue(
                            "invalid_json",
                            f"JSON decode error at column {error.colno}: {error.msg}",
                        )
                    ],
                    "warnings": [],
                }
            else:
                try:
                    result = checker.check(row, line_number)
                except Exception as error:
                    result = {
                        "line_number": line_number,
                        "valid": False,
                        "errors": [
                            checker._issue(
                                "checker_internal_error",
                                f"{type(error).__name__}: {error}",
                            )
                        ],
                        "warnings": [],
                    }

            if result["valid"]:
                valid += 1
            else:
                invalid += 1
            if result.get("warnings"):
                warning_rows += 1
            distinct_sid0 = result.get("stats", {}).get("beam_distinct_sid0")
            if distinct_sid0 is not None:
                beam_diversity_counts.append(distinct_sid0)
            error_counts.update(issue["code"] for issue in result["errors"])
            warning_counts.update(issue["code"] for issue in result.get("warnings", []))
            if not args.invalid_only or not result["valid"]:
                output_handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    summary = {
        "input": str(input_path),
        "output": str(output_path),
        "total_rows": total,
        "valid_rows": valid,
        "invalid_rows": invalid,
        "rows_with_warnings": warning_rows,
        "error_counts": dict(error_counts.most_common()),
        "warning_counts": dict(warning_counts.most_common()),
        "beam10_diversity_rows": len(beam_diversity_counts),
        "beam10_distinct_sid0_mean": (
            sum(beam_diversity_counts) / len(beam_diversity_counts)
            if beam_diversity_counts
            else None
        ),
        "beam10_distinct_sid0_rate_mean": (
            sum(beam_diversity_counts)
            / (len(beam_diversity_counts) * args.expected_beams)
            if beam_diversity_counts
            else None
        ),
        "semantic_limitation": (
            "This standard-library checker validates structure and citations, not "
            "semantic alignment with catalog detailed_description."
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())