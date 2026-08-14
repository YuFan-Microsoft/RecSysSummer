from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class SidCandidateSelection:
    selected_index: int
    first_token_unique_count: int
    exact_match_count: int


def count_unique_first_sid_tokens(predictions: list[str], cutoff: int = 10) -> int:
    """Count unique first-level SID tokens in the leading predictions."""
    if cutoff < 1:
        raise ValueError("SID diversity cutoff must be positive")
    leading_predictions = predictions[:cutoff]
    if not leading_predictions:
        raise ValueError("At least one SID prediction is required")

    first_tokens = []
    for prediction in leading_predictions:
        sid_tokens = re.findall(r"<[^>]+>", str(prediction))
        if not sid_tokens:
            raise ValueError(f"Prediction does not contain a SID token: {prediction!r}")
        first_tokens.append(sid_tokens[0])
    return len(set(first_tokens))


def select_sid_candidate(
    candidates: list[list[int]],
    cumulative_logprobs: list[float],
    target_sid: list[int],
) -> SidCandidateSelection:
    """Prefer the highest-probability exact match and measure first-token diversity.

    The first sample is retained when no exact match exists. Equal-probability
    exact matches are resolved by their original sample order.
    """
    if not candidates:
        raise ValueError("At least one sampled SID candidate is required")
    if len(candidates) != len(cumulative_logprobs):
        raise ValueError("SID candidates and cumulative log probabilities must align")
    if not target_sid:
        raise ValueError("A target SID is required for exact-match selection")
    if any(len(candidate) != len(target_sid) for candidate in candidates):
        raise ValueError("Sampled and target SIDs must have the same depth")
    if any(not math.isfinite(score) for score in cumulative_logprobs):
        raise ValueError("SID cumulative log probabilities must be finite")
    exact_match_indices = [
        index for index, candidate in enumerate(candidates) if candidate == target_sid
    ]
    selected_index = 0
    if exact_match_indices:
        selected_index = max(exact_match_indices, key=cumulative_logprobs.__getitem__)

    first_token_unique_count = len({candidate[0] for candidate in candidates})
    return SidCandidateSelection(
        selected_index=selected_index,
        first_token_unique_count=first_token_unique_count,
        exact_match_count=len(exact_match_indices),
    )