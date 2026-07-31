import torch

from verl.trainer.ppo.sid_hierarchical import (
    apply_constrained_sid_log_probs,
    compute_hierarchical_exact_match_advantages,
)


def test_constrained_log_prob_normalizes_only_over_allowed_tokens_and_backpropagates():
    logits = torch.zeros((1, 2, 5), requires_grad=True)
    responses = torch.tensor([[0, 2]])
    sid_token_mask = torch.tensor([[0, 1]], dtype=torch.bool)
    full_log_probs = torch.log_softmax(logits, dim=-1).gather(-1, responses.unsqueeze(-1)).squeeze(-1)

    log_probs = apply_constrained_sid_log_probs(
        log_probs=full_log_probs,
        logits=logits,
        responses=responses,
        sid_token_mask=sid_token_mask,
        sid_allowed_token_ids=[[[2, 3]]],
    )

    assert torch.allclose(log_probs[0, 1], -torch.log(torch.tensor(2.0)))
    (-log_probs[0, 1]).backward()
    assert torch.allclose(logits.grad[0, 1], torch.tensor([0.0, 0.0, -0.5, 0.5, 0.0]))


def test_hierarchical_advantages_use_hit_any_and_within_reasoning_baseline():
    exact_matches = torch.tensor([0, 1, 1, 0, 0, 0, 0, 0], dtype=torch.float32)
    prompt_ids = torch.zeros(8, dtype=torch.long)
    reasoning_ids = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1])

    reasoning_advantages, sid_advantages = compute_hierarchical_exact_match_advantages(
        exact_matches,
        prompt_ids,
        reasoning_ids,
    )

    assert torch.allclose(
        reasoning_advantages,
        torch.tensor([0.70710677] * 4 + [-0.70710677] * 4),
    )
    assert torch.allclose(
        sid_advantages,
        torch.tensor([-2 / 3, 2 / 3, 2 / 3, -2 / 3, 0, 0, 0, 0]),
    )


def test_hierarchical_advantages_do_not_reward_duplicate_hits_more():
    exact_matches = torch.tensor([1, 0, 0, 0, 1, 1, 0, 0], dtype=torch.float32)
    prompt_ids = torch.zeros(8, dtype=torch.long)
    reasoning_ids = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1])

    reasoning_advantages, _ = compute_hierarchical_exact_match_advantages(
        exact_matches,
        prompt_ids,
        reasoning_ids,
    )

    assert torch.equal(reasoning_advantages, torch.zeros_like(reasoning_advantages))


def test_all_miss_group_has_no_sid_signal():
    exact_matches = torch.zeros(3)
    group_ids = torch.zeros(3, dtype=torch.long)

    reasoning_advantages, sid_advantages = compute_hierarchical_exact_match_advantages(
        exact_matches,
        group_ids,
        group_ids,
    )

    assert torch.equal(reasoning_advantages, torch.zeros_like(reasoning_advantages))
    assert torch.equal(sid_advantages, torch.zeros_like(sid_advantages))


def test_hierarchical_advantages_are_grouped_per_prompt():
    exact_matches = torch.tensor([1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0])
    prompt_ids = torch.tensor([0] * 8 + [1] * 8)
    reasoning_ids = torch.tensor([0] * 4 + [1] * 4 + [2] * 4 + [3] * 4)

    reasoning_advantages, _ = compute_hierarchical_exact_match_advantages(
        exact_matches,
        prompt_ids,
        reasoning_ids,
    )

    assert torch.all(reasoning_advantages[:4] > 0)
    assert torch.all(reasoning_advantages[4:8] < 0)
    assert torch.all(reasoning_advantages[8:12] > 0)
    assert torch.all(reasoning_advantages[12:] < 0)


def test_single_sid_sample_has_no_within_reasoning_advantage():
    exact_matches = torch.tensor([1.0, 0.0, 1.0, 0.0])
    prompt_ids = torch.tensor([0, 0, 1, 1])
    reasoning_ids = torch.tensor([0, 1, 2, 3])

    _, sid_advantages = compute_hierarchical_exact_match_advantages(
        exact_matches,
        prompt_ids,
        reasoning_ids,
    )

    assert torch.equal(sid_advantages, torch.zeros_like(sid_advantages))