import numpy as np

from verl.trainer.ppo.retry_sampling import (
    classify_retry_groups,
    select_fallback_group_indices,
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


def test_selects_only_unreplaced_first_attempt_groups():
    group_ids = np.array(["a", "b", "a", "b", "c", "c"], dtype=object)

    selected = select_fallback_group_indices(group_ids, accepted_group_ids={"b"}, expected_group_size=2)

    assert selected.tolist() == [0, 2, 4, 5]