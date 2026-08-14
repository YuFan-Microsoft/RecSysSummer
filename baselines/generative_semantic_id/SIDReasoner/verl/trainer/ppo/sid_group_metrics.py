from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any


def compute_exact_match_count_histogram(
    group_ids: Iterable[Any],
    rewards: Iterable[float],
) -> dict[int, int]:
    """Count groups containing exactly k positive rewards."""
    group_ids = list(group_ids)
    rewards = list(rewards)
    if len(group_ids) != len(rewards):
        raise ValueError("Group IDs and rewards must have the same length")
    if not group_ids:
        raise ValueError("At least one reward group is required")

    grouped_rewards: dict[Any, list[float]] = defaultdict(list)
    for group_id, reward in zip(group_ids, rewards):
        reward = float(reward)
        if reward not in (0.0, 1.0):
            raise ValueError("Exact-match group metrics require binary rewards")
        grouped_rewards[group_id].append(reward)

    group_sizes = {len(group_rewards) for group_rewards in grouped_rewards.values()}
    if len(group_sizes) != 1:
        raise ValueError("All exact-match reward groups must have the same size")
    group_size = group_sizes.pop()

    count_histogram = {positive_count: 0 for positive_count in range(group_size + 1)}
    for group_rewards in grouped_rewards.values():
        count_histogram[int(sum(group_rewards))] += 1

    return count_histogram


def compute_exact_match_count_buckets(
    group_ids: Iterable[Any],
    rewards: Iterable[float],
    expected_group_size: int = 16,
) -> dict[str, int]:
    """Compress a 16-rollout exact-match histogram into six group counts."""
    group_ids = list(group_ids)
    rewards = list(rewards)
    count_histogram = compute_exact_match_count_histogram(group_ids, rewards)
    group_size = max(count_histogram)
    if group_size != expected_group_size:
        raise ValueError(
            f"Expected exact-match groups of size {expected_group_size}, got {group_size}"
        )
    return {
        "all_wrong": count_histogram[0],
        "one_correct": count_histogram[1],
        "k_2_4": sum(count_histogram[positive_count] for positive_count in range(2, 5)),
        "k_5_11": sum(count_histogram[positive_count] for positive_count in range(5, 12)),
        "k_12_15": sum(count_histogram[positive_count] for positive_count in range(12, 16)),
        "all_correct": count_histogram[16],
    }