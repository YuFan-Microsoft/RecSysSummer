from __future__ import annotations

import numpy as np


def build_retry_attempt_metrics(
    attempt: int,
    counts: dict[str, int],
    original_group_count: int,
) -> dict[str, float]:
    """Build stable W&B metrics for one retry attempt."""
    if attempt < 1:
        raise ValueError("attempt must be positive")
    if original_group_count < 1:
        raise ValueError("original_group_count must be positive")

    candidate_groups = counts["candidate_groups"]
    if candidate_groups < 0:
        raise ValueError("candidate_groups cannot be negative")
    category_keys = (
        "active_groups",
        "all_wrong_groups",
        "all_correct_groups",
        "uniform_other_groups",
    )
    if any(counts[key] < 0 for key in category_keys):
        raise ValueError("retry group counts cannot be negative")
    if sum(counts[key] for key in category_keys) != candidate_groups:
        raise ValueError("retry group categories must sum to candidate_groups")

    prefix = f"beam_retry/attempt_{attempt}"
    denominator = candidate_groups if candidate_groups else 1
    return {
        f"{prefix}/executed": float(candidate_groups > 0),
        f"{prefix}/candidate_groups": float(candidate_groups),
        f"{prefix}/candidate_rate_of_batch": candidate_groups / original_group_count,
        f"{prefix}/active_groups": float(counts["active_groups"]),
        f"{prefix}/active_rate": counts["active_groups"] / denominator,
        f"{prefix}/all_wrong_groups": float(counts["all_wrong_groups"]),
        f"{prefix}/all_wrong_rate": counts["all_wrong_groups"] / denominator,
        f"{prefix}/all_correct_groups": float(counts["all_correct_groups"]),
        f"{prefix}/all_correct_rate": counts["all_correct_groups"] / denominator,
        f"{prefix}/uniform_other_groups": float(counts["uniform_other_groups"]),
        f"{prefix}/uniform_other_rate": counts["uniform_other_groups"] / denominator,
    }


def classify_retry_groups(
    group_ids: np.ndarray,
    rewards: np.ndarray,
    expected_group_size: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """Select active groups and identify all-wrong groups eligible for retry."""
    group_ids = np.asarray(group_ids)
    rewards = np.asarray(rewards, dtype=float)
    if group_ids.ndim != 1 or rewards.ndim != 1 or group_ids.shape != rewards.shape:
        raise ValueError("group_ids and rewards must be aligned one-dimensional arrays")
    if expected_group_size < 1:
        raise ValueError("expected_group_size must be positive")

    grouped_indices: dict[object, list[int]] = {}
    for index, group_id in enumerate(group_ids):
        grouped_indices.setdefault(group_id, []).append(index)

    active_groups = []
    all_wrong_group_ids = []
    all_correct_count = 0
    uniform_other_count = 0
    for group_id, indices in grouped_indices.items():
        if len(indices) != expected_group_size:
            raise ValueError("A retry group has an unexpected number of trajectories")
        group_rewards = rewards[indices]
        min_reward = group_rewards.min()
        max_reward = group_rewards.max()
        if max_reward > min_reward:
            active_groups.append(indices)
        elif max_reward == 0.0:
            all_wrong_group_ids.append(group_id)
        elif min_reward == 1.0:
            all_correct_count += 1
        else:
            uniform_other_count += 1

    selected_indices = [index for indices in active_groups for index in indices]
    counts = {
        "candidate_groups": len(grouped_indices),
        "active_groups": len(active_groups),
        "all_wrong_groups": len(all_wrong_group_ids),
        "all_correct_groups": all_correct_count,
        "uniform_other_groups": uniform_other_count,
    }
    return (
        np.asarray(selected_indices, dtype=np.int64),
        np.asarray(all_wrong_group_ids, dtype=object),
        counts,
    )


def select_fallback_group_indices(
    group_ids: np.ndarray,
    accepted_group_ids: set[object],
    expected_group_size: int,
) -> np.ndarray:
    """Select complete first-attempt groups that were never replaced by an active retry."""
    group_ids = np.asarray(group_ids)
    grouped_indices: dict[object, list[int]] = {}
    for index, group_id in enumerate(group_ids):
        grouped_indices.setdefault(group_id, []).append(index)

    selected_indices = []
    for group_id, indices in grouped_indices.items():
        if len(indices) != expected_group_size:
            raise ValueError("A retry group has an unexpected number of trajectories")
        if group_id not in accepted_group_ids:
            selected_indices.extend(indices)
    return np.asarray(selected_indices, dtype=np.int64)