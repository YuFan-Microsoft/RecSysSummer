from __future__ import annotations

import numpy as np


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
            raise ValueError("A retry sampling group has an unexpected number of trajectories")
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
            raise ValueError("A retry sampling group has an unexpected number of trajectories")
        if group_id not in accepted_group_ids:
            selected_indices.extend(indices)
    return np.asarray(selected_indices, dtype=np.int64)