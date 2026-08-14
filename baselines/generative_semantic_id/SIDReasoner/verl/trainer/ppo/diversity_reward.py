import math


def binary_diversity_rewards(
    unique_counts: list[int],
    baseline_threshold: float,
) -> list[float]:
    """Threshold raw distinct-SID0 counts against a frozen baseline mean."""
    if not math.isfinite(baseline_threshold) or baseline_threshold <= 0:
        raise ValueError("SID diversity baseline threshold must be positive and finite")
    if any(count < 0 for count in unique_counts):
        raise ValueError("SID diversity counts must be non-negative")
    return [float(count >= baseline_threshold) for count in unique_counts]