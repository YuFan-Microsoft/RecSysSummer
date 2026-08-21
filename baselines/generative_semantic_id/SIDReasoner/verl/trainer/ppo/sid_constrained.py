from __future__ import annotations

from functools import lru_cache
from typing import Any

import torch


@lru_cache(maxsize=1)
def _byte_level_decoder() -> dict[str, int]:
    visible_bytes = list(range(ord("!"), ord("~") + 1))
    visible_bytes += list(range(161, 173))
    visible_bytes += list(range(174, 256))
    byte_values = visible_bytes.copy()
    code_points = visible_bytes.copy()
    visible_set = set(visible_bytes)
    extra_index = 0
    for byte_value in range(256):
        if byte_value in visible_set:
            continue
        byte_values.append(byte_value)
        code_points.append(256 + extra_index)
        extra_index += 1
    return {
        chr(code_point): byte_value
        for byte_value, code_point in zip(byte_values, code_points)
    }


def _decode_utf8_with_byte_spans(raw_bytes: bytes) -> tuple[str, list[tuple[int, int]]]:
    """Decode like ``errors='replace'`` while retaining each character's byte span."""
    characters = []
    character_byte_spans = []
    cursor = 0
    while cursor < len(raw_bytes):
        remaining = raw_bytes[cursor:]
        try:
            valid_text = remaining.decode("utf-8")
        except UnicodeDecodeError as error:
            valid_bytes = remaining[: error.start]
            valid_text = valid_bytes.decode("utf-8")
            valid_cursor = cursor
            for character in valid_text:
                character_end = valid_cursor + len(character.encode("utf-8"))
                characters.append(character)
                character_byte_spans.append((valid_cursor, character_end))
                valid_cursor = character_end

            error_start = cursor + error.start
            error_end = cursor + error.end
            characters.append("\ufffd")
            character_byte_spans.append((error_start, error_end))
            cursor = error_end
        else:
            valid_cursor = cursor
            for character in valid_text:
                character_end = valid_cursor + len(character.encode("utf-8"))
                characters.append(character)
                character_byte_spans.append((valid_cursor, character_end))
                valid_cursor = character_end
            break
    return "".join(characters), character_byte_spans


def _locate_fragment_token_spans(
    tokenizer: Any,
    token_ids: list[int],
    token_strings: list[str],
    fragment: str,
) -> list[tuple[int, int]]:
    matches = []
    max_window_tokens = len(fragment.encode("utf-8")) + 8
    for start, token_string in enumerate(token_strings):
        if fragment[0] not in token_string:
            continue
        first_piece = tokenizer.decode(
            [token_ids[start]],
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        window_end = min(len(token_ids), start + max_window_tokens)
        window = tokenizer.decode(
            token_ids[start:window_end],
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        fragment_start = window.find(fragment)
        if fragment_start < 0 or fragment_start >= len(first_piece):
            continue
        for end in range(start + 1, window_end + 1):
            candidate = tokenizer.decode(
                token_ids[start:end],
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False,
            )
            if fragment in candidate:
                matches.append((start, end))
                break
    return matches


def build_unique_tagged_span_mask(
    tokenizer: Any,
    token_ids: list[int],
    opening_tag: str,
    closing_tag: str,
    output_length: int,
) -> torch.Tensor:
    """Mask one uniquely delimited decoded span in the original token IDs."""
    if not opening_tag or not closing_tag:
        raise ValueError("tags must not be empty")
    if output_length < len(token_ids):
        raise ValueError("output_length must cover all token IDs")

    decoded = tokenizer.decode(
        token_ids,
        skip_special_tokens=False,
        clean_up_tokenization_spaces=False,
    )

    mask = torch.zeros(output_length, dtype=torch.bool)
    if decoded.count(opening_tag) != 1 or decoded.count(closing_tag) != 1:
        return mask
    if decoded.index(closing_tag) < decoded.index(opening_tag) + len(opening_tag):
        return mask

    token_strings = tokenizer.convert_ids_to_tokens(token_ids, skip_special_tokens=False)
    if not isinstance(token_strings, list) or len(token_strings) != len(token_ids):
        raise ValueError("Tokenizer did not return one token string per reasoning token ID")

    def locate_fragment(fragment: str) -> tuple[int, int]:
        matches = _locate_fragment_token_spans(
            tokenizer,
            token_ids,
            token_strings,
            fragment,
        )
        if len(matches) != 1:
            raise ValueError(
                f"Expected one original-token span for {fragment!r}, found {len(matches)}"
            )
        return matches[0]

    opening_start, _ = locate_fragment(opening_tag)
    _, closing_end = locate_fragment(closing_tag)
    if closing_end <= opening_start:
        raise ValueError("Future-interest closing tag precedes its opening tag")

    mask[opening_start:closing_end] = True
    return mask


def build_future_interest_line_masks(
    tokenizer: Any,
    token_ids: list[int],
    output_length: int,
    max_lines: int,
) -> torch.Tensor:
    """Project parsed future-interest character spans onto original Qwen tokens."""
    from verl.utils.reward_score.sid_reasoning_format import extract_future_interest_line_spans

    if output_length < len(token_ids):
        raise ValueError("output_length must cover all token IDs")
    if max_lines < 1:
        raise ValueError("max_lines must be positive")

    decoded = tokenizer.decode(
        token_ids,
        skip_special_tokens=False,
        clean_up_tokenization_spaces=False,
    )
    masks = torch.zeros((max_lines, output_length), dtype=torch.bool)
    interest_spans = extract_future_interest_line_spans(decoded)
    if not interest_spans:
        return masks
    if len(interest_spans) > max_lines:
        raise ValueError("Parsed more future-interest lines than max_lines")

    token_strings = tokenizer.convert_ids_to_tokens(token_ids, skip_special_tokens=False)
    if not isinstance(token_strings, list) or len(token_strings) != len(token_ids):
        raise ValueError("Tokenizer did not return one token string per reasoning token ID")

    byte_decoder = _byte_level_decoder()
    token_byte_spans = []
    token_bytes = []
    byte_cursor = 0
    for token_id, token_string in zip(token_ids, token_strings):
        try:
            raw_bytes = bytes(byte_decoder[character] for character in token_string)
        except KeyError:
            # Qwen added tokens such as <think> are not necessarily listed in
            # all_special_ids and are not encoded with the ByteLevel alphabet.
            raw_bytes = tokenizer.decode(
                [token_id],
                skip_special_tokens=False,
                clean_up_tokenization_spaces=False,
            ).encode("utf-8")
        token_bytes.append(raw_bytes)
        token_byte_spans.append((byte_cursor, byte_cursor + len(raw_bytes)))
        byte_cursor += len(raw_bytes)

    raw_response = b"".join(token_bytes)
    reconstructed, character_byte_spans = _decode_utf8_with_byte_spans(raw_response)
    if reconstructed != decoded:
        raise ValueError("Original token bytes do not reproduce the decoded reasoning")

    for line_index, (_, character_start, character_end) in enumerate(interest_spans):
        byte_start = character_byte_spans[character_start][0]
        byte_end = character_byte_spans[character_end - 1][1]
        for token_index, (token_start, token_end) in enumerate(token_byte_spans):
            if token_start < byte_end and token_end > byte_start:
                masks[line_index, token_index] = True
    return masks


def apply_constrained_sid_log_probs(
    log_probs: torch.Tensor,
    logits: torch.Tensor,
    responses: torch.Tensor,
    sid_token_mask: torch.Tensor,
    sid_allowed_token_ids,
) -> torch.Tensor:
    """Replace SID-token log probabilities with trie-conditional probabilities."""
    constrained_log_probs = log_probs.clone()
    for batch_index in range(logits.shape[0]):
        sid_positions = torch.nonzero(sid_token_mask[batch_index], as_tuple=False).flatten().tolist()
        allowed_per_position = sid_allowed_token_ids[batch_index]
        if not sid_positions:
            raise ValueError("Every constrained response must contain SID token positions")
        if len(sid_positions) != len(allowed_per_position):
            raise ValueError("SID mask and allowed-token metadata have different lengths")

        for sid_position, allowed in zip(sid_positions, allowed_per_position, strict=True):
            allowed_tensor = torch.as_tensor(allowed, dtype=torch.long, device=logits.device)
            action = responses[batch_index, sid_position]
            if not torch.any(allowed_tensor == action):
                raise ValueError("Sampled SID token is not in its recorded allowed-token set")
            position_logits = logits[batch_index, sid_position]
            constrained_log_probs[batch_index, sid_position] = (
                position_logits[action] - torch.logsumexp(position_logits[allowed_tensor], dim=0)
            )
    return constrained_log_probs