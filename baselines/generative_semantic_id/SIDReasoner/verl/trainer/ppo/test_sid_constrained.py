import torch

from verl.trainer.ppo.sid_constrained import (
    apply_constrained_sid_log_probs,
    build_unique_tagged_span_mask,
)


class OffsetTokenizer:
    def __init__(self, chunks, token_strings=None):
        self.chunks = chunks
        self.token_ids = list(range(100, 100 + len(chunks)))
        self.token_strings = token_strings or chunks

    def decode(self, token_ids, **_kwargs):
        indices = [self.token_ids.index(token_id) for token_id in token_ids]
        return "".join(self.chunks[index] for index in indices)

    def convert_ids_to_tokens(self, token_ids, **_kwargs):
        indices = [self.token_ids.index(token_id) for token_id in token_ids]
        return [self.token_strings[index] for index in indices]

    def __call__(self, *_args, **_kwargs):
        raise AssertionError("Generated token IDs must never be re-encoded")


def test_tagged_span_mask_uses_original_ids_at_contextual_token_boundaries():
    tokenizer = OffsetTokenizer(
        [
            "prefix\n<",
            "future_interests",
            ">\n",
            "interest text",
            "\n</",
            "future_interests",
            ">",
            "\n</think>",
        ],
        ["prefixĊ<", "future_interests", ">Ċ", "interest", "Ċ</", "future_interests", ">", "Ċ</think>"],
    )
    mask = build_unique_tagged_span_mask(
        tokenizer=tokenizer,
        token_ids=tokenizer.token_ids,
        opening_tag="<future_interests>",
        closing_tag="</future_interests>",
        output_length=10,
    )
    assert torch.equal(
        mask,
        torch.tensor([1, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=torch.bool),
    )


def test_tagged_span_mask_is_zero_when_tags_are_missing_or_ambiguous():
    missing_tokenizer = OffsetTokenizer(["prefix", " without tags"])
    missing = build_unique_tagged_span_mask(
        missing_tokenizer,
        missing_tokenizer.token_ids,
        "<future_interests>",
        "</future_interests>",
        5,
    )
    repeated_tokenizer = OffsetTokenizer(
        [
            "<future_interests>x</future_interests>",
            "<future_interests>y</future_interests>",
        ]
    )
    repeated = build_unique_tagged_span_mask(
        repeated_tokenizer,
        repeated_tokenizer.token_ids,
        "<future_interests>",
        "</future_interests>",
        2,
    )
    assert not missing.any()
    assert not repeated.any()


def test_tagged_span_mask_rejects_short_output_length():
    tokenizer = OffsetTokenizer(["<future_interests>x</future_interests>"])
    try:
        build_unique_tagged_span_mask(
            tokenizer,
            tokenizer.token_ids,
            "<future_interests>",
            "</future_interests>",
            0,
        )
    except ValueError as error:
        assert "cover all token IDs" in str(error)
    else:
        raise AssertionError("Expected short output_length to fail")


def test_tagged_span_mask_accepts_noncanonical_generated_token_ids_without_reencoding():
    tokenizer = OffsetTokenizer(
        ["<future_interests>", "he", "l", "lo", "</future_interests>"],
    )
    mask = build_unique_tagged_span_mask(
        tokenizer,
        tokenizer.token_ids,
        "<future_interests>",
        "</future_interests>",
        5,
    )
    assert mask.all()


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