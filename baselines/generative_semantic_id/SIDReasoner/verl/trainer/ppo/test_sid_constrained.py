import torch

from verl.trainer.ppo.sid_constrained import (
    apply_constrained_sid_log_probs,
    build_unique_tagged_span_mask,
)


def test_tagged_span_mask_includes_unique_opening_content_and_closing_tags():
    mask = build_unique_tagged_span_mask(
        token_ids=[9, 1, 2, 5, 6, 3, 4, 8],
        opening_tag_ids=[1, 2],
        closing_tag_ids=[3, 4],
        output_length=10,
    )
    assert torch.equal(
        mask,
        torch.tensor([0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=torch.bool),
    )


def test_tagged_span_mask_is_zero_when_tags_are_missing_or_ambiguous():
    missing = build_unique_tagged_span_mask([1, 2, 5], [1, 2], [3, 4], 5)
    repeated = build_unique_tagged_span_mask(
        [1, 2, 5, 3, 4, 1, 2, 6, 3, 4],
        [1, 2],
        [3, 4],
        10,
    )
    assert not missing.any()
    assert not repeated.any()


def test_tagged_span_mask_rejects_short_output_length():
    try:
        build_unique_tagged_span_mask([1, 2, 3], [1], [3], 2)
    except ValueError as error:
        assert "cover all token IDs" in str(error)
    else:
        raise AssertionError("Expected short output_length to fail")


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


def test_constrained_log_probs_support_three_sid_positions_per_response():
    logits = torch.zeros((2, 5, 8))
    responses = torch.tensor([[0, 2, 3, 4, 0], [1, 0, 5, 0, 6]])
    sid_token_mask = torch.tensor(
        [[0, 1, 1, 1, 0], [1, 0, 1, 0, 1]],
        dtype=torch.bool,
    )
    full_log_probs = torch.log_softmax(logits, dim=-1).gather(-1, responses.unsqueeze(-1)).squeeze(-1)

    log_probs = apply_constrained_sid_log_probs(
        log_probs=full_log_probs,
        logits=logits,
        responses=responses,
        sid_token_mask=sid_token_mask,
        sid_allowed_token_ids=[[[2, 7], [3, 6], [1, 4]], [[1, 2], [5, 7], [0, 6]]],
    )

    assert torch.allclose(log_probs[sid_token_mask], torch.full((6,), -torch.log(torch.tensor(2.0))))
    assert torch.allclose(log_probs[~sid_token_mask], full_log_probs[~sid_token_mask])


def test_constrained_log_probs_reject_missing_sid_mask():
    try:
        apply_constrained_sid_log_probs(
            log_probs=torch.zeros((1, 2)),
            logits=torch.zeros((1, 2, 4)),
            responses=torch.zeros((1, 2), dtype=torch.long),
            sid_token_mask=torch.zeros((1, 2), dtype=torch.bool),
            sid_allowed_token_ids=[[]],
        )
    except ValueError as error:
        assert "must contain SID" in str(error)
    else:
        raise AssertionError("Expected an empty SID mask to fail")