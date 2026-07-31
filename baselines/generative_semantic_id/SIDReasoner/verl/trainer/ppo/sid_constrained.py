from __future__ import annotations

import torch


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