import numpy as np

from verl.trainer.ppo.retry_sampling import (
    build_retry_attempt_metrics,
    classify_retry_groups,
    select_fallback_group_indices,
)


def test_retries_only_all_wrong_beam_groups():
    group_ids = np.array(["active", "active", "wrong", "wrong", "correct", "correct", "partial", "partial"])
    rewards = np.array([0.0, 0.5, 0.0, 0.0, 1.0, 1.0, 0.5, 0.5])

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
            np.array([0.0, 0.5, 0.0]),
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


def test_builds_conditional_attempt_metrics():
    metrics = build_retry_attempt_metrics(
        attempt=2,
        counts={
            "candidate_groups": 40,
            "active_groups": 10,
            "all_wrong_groups": 20,
            "all_correct_groups": 5,
            "uniform_other_groups": 5,
        },
        original_group_count=256,
    )

    assert metrics["beam_retry/attempt_2/executed"] == 1.0
    assert metrics["beam_retry/attempt_2/candidate_groups"] == 40.0
    assert metrics["beam_retry/attempt_2/candidate_rate_of_batch"] == 40 / 256
    assert metrics["beam_retry/attempt_2/active_rate"] == 0.25
    assert metrics["beam_retry/attempt_2/all_wrong_rate"] == 0.5


def test_builds_zero_metrics_for_skipped_attempt():
    metrics = build_retry_attempt_metrics(
        attempt=3,
        counts={
            "candidate_groups": 0,
            "active_groups": 0,
            "all_wrong_groups": 0,
            "all_correct_groups": 0,
            "uniform_other_groups": 0,
        },
        original_group_count=256,
    )

    assert metrics["beam_retry/attempt_3/executed"] == 0.0
    assert metrics["beam_retry/attempt_3/candidate_rate_of_batch"] == 0.0
    assert metrics["beam_retry/attempt_3/active_rate"] == 0.0


def test_rejects_inconsistent_attempt_counts():
    try:
        build_retry_attempt_metrics(
            attempt=1,
            counts={
                "candidate_groups": 10,
                "active_groups": 2,
                "all_wrong_groups": 3,
                "all_correct_groups": 1,
                "uniform_other_groups": 1,
            },
            original_group_count=10,
        )
    except ValueError as error:
        assert "must sum" in str(error)
    else:
        raise AssertionError("Expected inconsistent retry counts to fail")