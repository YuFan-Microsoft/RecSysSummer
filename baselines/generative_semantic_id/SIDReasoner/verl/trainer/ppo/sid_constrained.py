from __future__ import annotations

from typing import Any

import torch


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