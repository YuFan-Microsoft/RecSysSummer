import torch

from verl.trainer.ppo.sid_constrained import (
    apply_constrained_sid_log_probs,
    build_future_interest_line_masks,
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


class ByteLevelOffsetTokenizer(OffsetTokenizer):
    all_special_ids = []

    def convert_ids_to_tokens(self, token_ids, **_kwargs):
        from transformers.models.gpt2.tokenization_gpt2 import bytes_to_unicode

        byte_encoder = bytes_to_unicode()
        indices = [self.token_ids.index(token_id) for token_id in token_ids]
        return [
            "".join(byte_encoder[byte] for byte in self.chunks[index].encode("utf-8"))
            for index in indices
        ]


class RawByteLevelOffsetTokenizer:
    def __init__(self, token_bytes):
        from transformers.models.gpt2.tokenization_gpt2 import bytes_to_unicode

        byte_encoder = bytes_to_unicode()
        self.token_bytes = token_bytes
        self.token_ids = list(range(100, 100 + len(token_bytes)))
        self.token_strings = [
            "".join(byte_encoder[byte] for byte in raw_bytes)
            for raw_bytes in token_bytes
        ]

    def decode(self, token_ids, **_kwargs):
        indices = [self.token_ids.index(token_id) for token_id in token_ids]
        return b"".join(self.token_bytes[index] for index in indices).decode(
            "utf-8", errors="replace"
        )

    def convert_ids_to_tokens(self, token_ids, **_kwargs):
        indices = [self.token_ids.index(token_id) for token_id in token_ids]
        return [self.token_strings[index] for index in indices]


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


def test_future_interest_line_masks_project_shared_byte_level_tokens():
    first_line = "- [exploit] <a_1><b_2><c_3> => previous interest"
    final_line = "- [explore] <a_4><b_5><c_6> => likelihood above 50%"
    tokenizer = ByteLevelOffsetTokenizer(
        [
            "<think>\n<history_summary>\n- <a_1><b_2><c_3> => history\n"
            "</history_summary>\n<future_interests>\n",
            first_line + "\n-",
            final_line[1:-1],
            "%\n</future_interests>\n</think>",
        ]
    )

    masks = build_future_interest_line_masks(
        tokenizer=tokenizer,
        token_ids=tokenizer.token_ids,
        output_length=4,
        max_lines=4,
    )

    assert torch.nonzero(masks[0], as_tuple=False).flatten().tolist() == [1]
    assert torch.nonzero(masks[1], as_tuple=False).flatten().tolist() == [1, 2, 3]


def test_future_interest_line_masks_map_isolated_invalid_utf8_byte():
    prefix = (
        "<think>\n<history_summary>\n- <a_1><b_2><c_3> => history\n"
        "</history_summary>\n<future_interests>\n"
        "- [exploit] <a_1><b_2><c_3> => interest with "
    ).encode("utf-8")
    suffix = (
        " marker\n- [explore] <a_1><b_2><c_3> => second interest\n"
        "</future_interests>\n</think>"
    ).encode("utf-8")
    tokenizer = RawByteLevelOffsetTokenizer([prefix, b"\xb3", suffix])

    masks = build_future_interest_line_masks(
        tokenizer=tokenizer,
        token_ids=tokenizer.token_ids,
        output_length=3,
        max_lines=4,
    )

    assert "\ufffd" in tokenizer.decode(tokenizer.token_ids)
    assert torch.nonzero(masks[0], as_tuple=False).flatten().tolist() == [0, 1, 2]
    assert torch.nonzero(masks[1], as_tuple=False).flatten().tolist() == [2]


def test_future_interest_line_masks_skip_invalid_format():
    tokenizer = ByteLevelOffsetTokenizer(
        [
            "<think>\n<future_interests>\nmalformed\n</future_interests>\n</think>"
        ]
    )

    masks = build_future_interest_line_masks(
        tokenizer=tokenizer,
        token_ids=tokenizer.token_ids,
        output_length=1,
        max_lines=4,
    )

    assert not masks.any()


def test_future_interest_line_masks_skip_lone_greater_than_fourth_line():
    tokenizer = ByteLevelOffsetTokenizer(
        [
            "<think>\n<history_summary>\n- <a_1><b_2><c_3> => history\n"
            "</history_summary>\n<future_interests>\n"
            "- [exploit] <a_1><b_2><c_3> => first\n"
            "- [explore] <a_1><b_2><c_3> => second\n"
            "- [exploit] <a_1><b_2><c_3> => third\n"
            ">\n</future_interests>\n</think>"
        ]
    )

    masks = build_future_interest_line_masks(
        tokenizer=tokenizer,
        token_ids=tokenizer.token_ids,
        output_length=1,
        max_lines=4,
    )

    assert not masks.any()


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