import re
from typing import Any


PROCESS_ADVANTAGE_WEIGHT = 0.1

_SID_PATTERN = r"<a_\d+><b_\d+><c_\d+>"
_CITATION_SEPARATOR = r"(?:\s*,\s*|\s+)"
_CITATIONS_PATTERN = rf"{_SID_PATTERN}(?:{_CITATION_SEPARATOR}{_SID_PATTERN})*"
_EVIDENCE_LINE_PATTERN = re.compile(
    rf"^-\s*(?P<citations>{_CITATIONS_PATTERN})\s*=>\s*(?P<text>\S.*)$"
)
_INTEREST_LINE_PATTERN = re.compile(
    rf"^-\s*\[(?P<label>exploit|explore)\]\s*"
    rf"(?P<citations>{_CITATIONS_PATTERN})\s*=>\s*(?P<text>\S.*)$",
    re.IGNORECASE,
)
_OUTER_PATTERN = re.compile(
    r"""
    \s*(?:<think>\s*)?
    <history_evidence>\s*(?P<history>.*?)\s*</history_evidence>\s*
    <next_interest>\s*(?P<interest>.*?)\s*</next_interest>\s*
    \Z
    """,
    re.DOTALL | re.VERBOSE,
)
_REQUIRED_TAGS = (
    "<history_evidence>",
    "</history_evidence>",
    "<next_interest>",
    "</next_interest>",
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


def calculate_process_rewards(solution_str: str, history_sids: Any) -> dict[str, float]:
    """Score the two-block reasoning schema and its citations to the real history."""
    zero_scores = {
        "format_reward": 0.0,
        "grounding_reward": 0.0,
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

    evidence_lines = _nonempty_lines(match.group("history"))
    interest_lines = _nonempty_lines(match.group("interest"))
    parsed_evidence = [_EVIDENCE_LINE_PATTERN.fullmatch(line) for line in evidence_lines]
    parsed_interest = [_INTEREST_LINE_PATTERN.fullmatch(line) for line in interest_lines]

    labels = {line.group("label").casefold() for line in parsed_interest if line is not None}
    format_reward = float(
        bool(evidence_lines)
        and bool(interest_lines)
        and all(line is not None for line in parsed_evidence)
        and all(line is not None for line in parsed_interest)
        and labels == {"exploit", "explore"}
    )

    history_sid_set = _normalize_history_sids(history_sids)
    grounded_lines = sum(
        line is not None and _citation_sids(line) <= history_sid_set for line in parsed_evidence
    )
    grounded_lines += sum(
        line is not None
        and _citation_sids(line) <= history_sid_set
        for line in parsed_interest
    )
    total_lines = len(evidence_lines) + len(interest_lines)
    grounding_reward = grounded_lines / total_lines if total_lines else 0.0
    process_reward = (format_reward + grounding_reward) / 2.0

    return {
        "format_reward": format_reward,
        "grounding_reward": grounding_reward,
        "process_reward": process_reward,
    }