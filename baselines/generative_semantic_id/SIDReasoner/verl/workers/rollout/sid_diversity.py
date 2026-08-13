from dataclasses import dataclass
import math


@dataclass(frozen=True)
class SidCandidateSelection:
    selected_index: int
    first_token_unique_count: int
    diversity_reward: float
    exact_match_count: int


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
        diversity_reward=first_token_unique_count / len(candidates),
        exact_match_count=len(exact_match_indices),
    )