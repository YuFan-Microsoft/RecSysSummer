import re


FORMAT_REWARD_WEIGHT = 0.05

_FORMAT_PATTERN = re.compile(
    r"""
    \s*(?:<think>\s*)?
    <behavior>\s*(?P<behavior>.*?)\s*</behavior>\s*
    <interest>\s*(?P<interest>.*?)\s*</interest>\s*
    <intent>\s*(?P<intent>.*?)\s*</intent>\s*
    \Z
    """,
    re.DOTALL | re.VERBOSE,
)
_REQUIRED_TAGS = (
    "<behavior>",
    "</behavior>",
    "<interest>",
    "</interest>",
    "<intent>",
    "</intent>",
)


def calculate_format_reward(solution_str: str) -> float:
    """Return one when the reasoning has exactly three ordered, non-empty blocks."""
    if not isinstance(solution_str, str) or solution_str.count("</think>") != 1:
        return 0.0

    reasoning, _ = solution_str.split("</think>", maxsplit=1)
    if any(reasoning.count(tag) != 1 for tag in _REQUIRED_TAGS):
        return 0.0

    match = _FORMAT_PATTERN.fullmatch(reasoning)
    if match is None:
        return 0.0
    return float(all(match.group(name).strip() for name in ("behavior", "interest", "intent")))