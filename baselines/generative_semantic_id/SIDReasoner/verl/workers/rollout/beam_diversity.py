from dataclasses import dataclass


@dataclass(frozen=True)
class BeamDiversity:
    first_token_unique_count: int
    normalized_reward: float


def calculate_beam_diversity(
    sid_beam: list[list[int]],
    expected_size: int,
) -> BeamDiversity:
    """Measure first-token diversity on the configured beam-width scale."""
    if expected_size < 1:
        raise ValueError("Expected SID beam size must be positive")
    if not sid_beam:
        raise ValueError("At least one SID beam candidate is required")
    if len(sid_beam) > expected_size:
        raise ValueError(
            f"SID beam has {len(sid_beam)} candidates, exceeding configured size {expected_size}"
        )
    if any(not candidate for candidate in sid_beam):
        raise ValueError("SID beam candidates must contain at least one token")

    unique_count = len({candidate[0] for candidate in sid_beam})
    return BeamDiversity(
        first_token_unique_count=unique_count,
        normalized_reward=unique_count / expected_size,
    )