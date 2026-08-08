import numpy as np

from verl.trainer.ppo.retry_sampling import (
    align_active_group_count,
    classify_retry_groups,
    required_active_group_multiple,
    select_first_complete_groups,
)


def test_retries_only_all_wrong_groups():
    group_ids = np.array(["active", "active", "wrong", "wrong", "correct", "correct", "partial", "partial"])
    rewards = np.array([0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.5, 0.5])

    selected, retry_group_ids, counts = classify_retry_groups(group_ids, rewards, expected_group_size=2)

    assert selected.tolist() == [0, 1]
    assert retry_group_ids.tolist() == ["wrong"]
    assert counts == {
        "candidate_groups": 4,
        "active_groups": 1,
        "all_wrong_groups": 1,
        "all_correct_groups": 1,
        "uniform_other_groups": 1,
    }


def test_rejects_incomplete_retry_group():
    try:
        classify_retry_groups(
            np.array(["a", "a", "b"], dtype=object),
            np.array([0.0, 1.0, 0.0]),
            expected_group_size=2,
        )
    except ValueError as error:
        assert "unexpected number" in str(error)
    else:
        raise AssertionError("Expected an incomplete retry group to fail")


def test_aligns_active_groups_for_current_distributed_batch():
    assert required_active_group_multiple(rollout_n=16, world_size=8, micro_batch_size=8) == 4
    assert align_active_group_count(56, rollout_n=16, world_size=8, micro_batch_size=8) == 56
    assert align_active_group_count(59, rollout_n=16, world_size=8, micro_batch_size=8) == 56


def test_alignment_formula_handles_nontrivial_gcd():
    assert required_active_group_multiple(rollout_n=6, world_size=4, micro_batch_size=8) == 16
    assert align_active_group_count(31, rollout_n=6, world_size=4, micro_batch_size=8) == 16


def test_selects_unique_complete_groups_in_order():
    group_ids = np.array(["a", "b", "a", "b", "c", "c"], dtype=object)

    selected = select_first_complete_groups(group_ids, max_groups=2, expected_group_size=2)

    assert selected.tolist() == [0, 2, 1, 3]