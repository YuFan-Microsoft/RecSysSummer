import numpy as np

from verl.trainer.ppo.dynamic_sampling import count_uniform_group_types, select_active_group_indices


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