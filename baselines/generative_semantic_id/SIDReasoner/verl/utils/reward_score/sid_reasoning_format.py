from __future__ import annotations

import re
from typing import Any


PROCESS_REWARD_WEIGHT = 0.1

_SID_PATTERN = r"<a_\d+><b_\d+><c_\d+>"
_CITATIONS_PATTERN = rf"{_SID_PATTERN}(?:\s*,\s*{_SID_PATTERN})*"
_SUMMARY_LINE_PATTERN = re.compile(
    rf"^-\s+(?P<citations>{_CITATIONS_PATTERN})\s*=>\s*(?P<text>\S.*)$"
)
_FUTURE_INTEREST_LINE_PATTERN = re.compile(
    rf"^-\s+\[(?P<label>exploit|explore)\]\s+"
    rf"(?P<citations>{_CITATIONS_PATTERN})\s*=>\s*(?P<text>\S.*)$",
    re.IGNORECASE,
)
_OUTER_PATTERN = re.compile(
    r"""
    \s*(?:<think>\s*)?
    <history_summary>\s*(?P<history_summary>.*?)\s*</history_summary>\s*
    <future_interests>\s*(?P<future_interests>.*?)\s*</future_interests>\s*
    \Z
    """,
    re.DOTALL | re.VERBOSE,
)
_REQUIRED_TAGS = (
    "<history_summary>",
    "</history_summary>",
    "<future_interests>",
    "</future_interests>",
)


def _normalize_history_sids(history_sids: Any) -> set[str]:
    if history_sids is None:
        return set()
    if isinstance(history_sids, str):
        return set(re.findall(_SID_PATTERN, history_sids))

    normalized = set()
    for value in history_sids:
        matches = re.findall(_SID_PATTERN, str(value))
        if matches:
            normalized.add(matches[0])
    return normalized


def extract_history_sids_from_question(question: Any) -> list[str]:
    """Recover history SIDs from legacy parquet questions."""
    return list(dict.fromkeys(re.findall(_SID_PATTERN, str(question))))


def _nonempty_lines(block: str) -> list[str]:
    return [line.strip() for line in block.splitlines() if line.strip()]


def _citation_sids(line_match: re.Match[str]) -> set[str]:
    return set(re.findall(_SID_PATTERN, line_match.group("citations")))


def _grounding_fraction(
    line_matches: list[re.Match[str] | None],
    history_sid_set: set[str],
) -> float:
    if not line_matches:
        return 0.0
    grounded_count = sum(
        line_match is not None and _citation_sids(line_match) <= history_sid_set
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
            _citation_sids(line_match)
            for line_match in line_matches
            if line_match is not None
        )
    )
    return len(referenced_sids & history_sid_set) / len(history_sid_set)


def _latest_history_sid(history_sids: Any) -> str | None:
    if history_sids is None:
        return None
    if isinstance(history_sids, str):
        matches = re.findall(_SID_PATTERN, history_sids)
        return matches[-1] if matches else None

    latest_sid = None
    for value in history_sids:
        matches = re.findall(_SID_PATTERN, str(value))
        if matches:
            latest_sid = matches[0]
    return latest_sid


def _latest_history_summary_reference_reward(
    summary_matches: list[re.Match[str] | None],
    history_sids: Any,
) -> float:
    latest_sid = _latest_history_sid(history_sids)
    if latest_sid is None:
        return 0.0
    summary_citations = set().union(
        *(
            _citation_sids(line_match)
            for line_match in summary_matches
            if line_match is not None
        )
    )
    return float(latest_sid in summary_citations)


def calculate_process_rewards(solution_str: str, history_sids: Any) -> dict[str, float]:
    """Score strict V4 format and the grounding of its two reasoning stages."""
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
    if any(reasoning.count(tag) != 1 for tag in _REQUIRED_TAGS):
        return zero_scores

    match = _OUTER_PATTERN.fullmatch(reasoning)
    if match is None:
        return zero_scores

    summary_lines = _nonempty_lines(match.group("history_summary"))
    future_interest_lines = _nonempty_lines(match.group("future_interests"))
    parsed_summary = [_SUMMARY_LINE_PATTERN.fullmatch(line) for line in summary_lines]
    parsed_future_interests = [
        _FUTURE_INTEREST_LINE_PATTERN.fullmatch(line) for line in future_interest_lines
    ]

    summary_count_reward = float(1 <= len(summary_lines) <= 3)
    future_interest_count_reward = float(2 <= len(future_interest_lines) <= 4)

    labels = {
        line_match.group("label").casefold()
        for line_match in parsed_future_interests
        if line_match is not None
    }
    format_reward = float(
        summary_count_reward == 1.0
        and future_interest_count_reward == 1.0
        and all(line_match is not None for line_match in parsed_summary)
        and all(line_match is not None for line_match in parsed_future_interests)
        and labels == {"exploit", "explore"}
    )

    history_sid_set = _normalize_history_sids(history_sids)
    history_summary_grounding_reward = _grounding_fraction(
        parsed_summary,
        history_sid_set,
    )
    future_interests_grounding_reward = _grounding_fraction(
        parsed_future_interests,
        history_sid_set,
    )
    history_reference_coverage = _history_reference_coverage(
        parsed_summary + parsed_future_interests,
        history_sid_set,
    )
    latest_history_summary_reference_reward = (
        _latest_history_summary_reference_reward(
            parsed_summary,
            history_sids,
        )
    )
    hard_valid = (
        format_reward == 1.0
        and history_summary_grounding_reward == 1.0
        and future_interests_grounding_reward == 1.0
        and latest_history_summary_reference_reward == 1.0
    )
    process_reward = 1.0 if hard_valid else 0.0

    return {
        "history_summary_grounding_reward": history_summary_grounding_reward,
        "future_interests_grounding_reward": future_interests_grounding_reward,
        "format_reward": format_reward,
        "history_reference_coverage": history_reference_coverage,
        "latest_history_summary_reference_reward": (
            latest_history_summary_reference_reward
        ),
        "process_reward": process_reward,
    }
