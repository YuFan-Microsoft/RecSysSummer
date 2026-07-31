from __future__ import annotations

import numpy as np


def count_uniform_group_types(group_ids: np.ndarray, rewards: np.ndarray) -> tuple[int, int, int]:
    """Count uniform-zero, uniform-one, and other uniform reward groups."""
    group_ids = np.asarray(group_ids)
    rewards = np.asarray(rewards, dtype=float)
    if group_ids.ndim != 1 or rewards.ndim != 1 or group_ids.shape != rewards.shape:
        raise ValueError("group_ids and rewards must be aligned one-dimensional arrays")

    grouped_rewards: dict[object, list[float]] = {}
    for group_id, reward in zip(group_ids, rewards, strict=True):
        grouped_rewards.setdefault(group_id, []).append(reward)

    uniform_zero = 0
    uniform_one = 0
    uniform_other = 0
    for values in grouped_rewards.values():
        if min(values) != max(values):
            continue
        if values[0] == 0.0:
            uniform_zero += 1
        elif values[0] == 1.0:
            uniform_one += 1
        else:
            uniform_other += 1
    return uniform_zero, uniform_one, uniform_other


def select_active_group_indices(
    group_ids: np.ndarray,
    rewards: np.ndarray,
    max_groups: int | None = None,
    expected_group_size: int | None = None,
) -> tuple[np.ndarray, int]:
    """Select complete groups whose rewards are not uniform."""
    group_ids = np.asarray(group_ids)
    rewards = np.asarray(rewards, dtype=float)
    if group_ids.ndim != 1 or rewards.ndim != 1 or group_ids.shape != rewards.shape:
        raise ValueError("group_ids and rewards must be aligned one-dimensional arrays")
    if max_groups is not None and max_groups < 1:
        raise ValueError("max_groups must be positive")
    if expected_group_size is not None and expected_group_size < 1:
        raise ValueError("expected_group_size must be positive")

    grouped_indices: dict[object, list[int]] = {}
    for index, group_id in enumerate(group_ids):
        grouped_indices.setdefault(group_id, []).append(index)

    active_groups = []
    for indices in grouped_indices.values():
        if expected_group_size is not None and len(indices) != expected_group_size:
            raise ValueError("A dynamic sampling group has an unexpected number of trajectories")
        group_rewards = rewards[indices]
        if group_rewards.max() > group_rewards.min():
            active_groups.append(indices)

    active_group_count = len(active_groups)
    if max_groups is not None:
        active_groups = active_groups[:max_groups]
    selected_indices = [index for indices in active_groups for index in indices]
    return np.asarray(selected_indices, dtype=np.int64), active_group_count