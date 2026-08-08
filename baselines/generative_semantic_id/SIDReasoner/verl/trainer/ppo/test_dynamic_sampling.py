import numpy as np

from verl.trainer.ppo.dynamic_sampling import (
    CyclingIterator,
    count_uniform_group_types,
    select_active_group_indices,
    validate_dynamic_batch_sizes,
)


def test_cycling_iterator_consumes_fresh_batches_before_restart():
    batches = CyclingIterator(["batch-a", "batch-b", "batch-c"])

    consumed = [next(batches) for _ in range(4)]

    assert consumed == ["batch-a", "batch-b", "batch-c", "batch-a"]
    assert batches.cycles == 1


def test_accepts_distributed_batch_sizes_used_by_launcher():
    validate_dynamic_batch_sizes(
        target_active_groups=256,
        ppo_mini_batch_size=256,
        rollout_n=16,
        world_size=8,
    )


def test_rejects_partial_final_ppo_mini_batch():
    try:
        validate_dynamic_batch_sizes(
            target_active_groups=192,
            ppo_mini_batch_size=128,
            rollout_n=16,
            world_size=8,
        )
    except ValueError as error:
        assert "divisible by actor.ppo_mini_batch_size" in str(error)
    else:
        raise AssertionError("Expected a partial final PPO mini-batch to fail")


def test_rejects_trajectory_batch_not_divisible_by_world_size():
    try:
        validate_dynamic_batch_sizes(
            target_active_groups=3,
            ppo_mini_batch_size=1,
            rollout_n=2,
            world_size=4,
        )
    except ValueError as error:
        assert "actor world size" in str(error)
    else:
        raise AssertionError("Expected an uneven distributed trajectory batch to fail")


def test_selects_complete_non_uniform_groups_only():
    group_ids = np.array(["a", "a", "b", "b", "c", "c"], dtype=object)
    rewards = np.array([0.0, 1.0, 0.0, 0.0, 1.0, 1.0])

    selected, active_count = select_active_group_indices(group_ids, rewards)

    assert active_count == 1
    assert selected.tolist() == [0, 1]


def test_truncates_by_whole_groups_in_encounter_order():
    group_ids = np.array(["a", "a", "b", "b", "c", "c"], dtype=object)
    rewards = np.array([0.0, 1.0, 1.0, 0.0, 0.0, 1.0])

    selected, active_count = select_active_group_indices(group_ids, rewards, max_groups=2)

    assert active_count == 3
    assert selected.tolist() == [0, 1, 2, 3]


def test_supports_interleaved_group_members():
    group_ids = np.array(["a", "b", "a", "b"], dtype=object)
    rewards = np.array([0.0, 1.0, 1.0, 1.0])

    selected, active_count = select_active_group_indices(group_ids, rewards)

    assert active_count == 1
    assert selected.tolist() == [0, 2]


def test_rejects_incomplete_rollout_groups():
    try:
        select_active_group_indices(
            np.array(["a", "a", "b"], dtype=object),
            np.array([0.0, 1.0, 0.0]),
            expected_group_size=2,
        )
    except ValueError as error:
        assert "unexpected number" in str(error)
    else:
        raise AssertionError("Expected an incomplete rollout group to fail")


def test_counts_uniform_group_types_without_counting_active_groups():
    group_ids = np.array(["a", "a", "b", "b", "c", "c", "d", "d"], dtype=object)
    rewards = np.array([0.0, 0.0, 1.0, 1.0, 0.5, 0.5, 0.0, 1.0])

    counts = count_uniform_group_types(group_ids, rewards)

    assert counts == (1, 1, 1)