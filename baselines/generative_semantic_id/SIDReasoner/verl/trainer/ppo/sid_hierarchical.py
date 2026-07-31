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


def compute_hierarchical_exact_match_advantages(
    exact_matches: torch.Tensor,
    prompt_ids: torch.Tensor,
    reasoning_ids: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Compute prompt-level reasoning and within-reasoning SID advantages."""
    if exact_matches.ndim != 1:
        raise ValueError("exact_matches must be one-dimensional")
    if prompt_ids.shape != exact_matches.shape or reasoning_ids.shape != exact_matches.shape:
        raise ValueError("prompt_ids and reasoning_ids must match exact_matches")

    exact_matches = exact_matches.float()
    _, prompt_inverse = torch.unique(prompt_ids, sorted=True, return_inverse=True)
    _, reasoning_inverse = torch.unique(reasoning_ids, sorted=True, return_inverse=True)
    reasoning_count = int(reasoning_inverse.max().item()) + 1
    prompt_count = int(prompt_inverse.max().item()) + 1

    per_reasoning_reward = torch.zeros(reasoning_count, device=exact_matches.device)
    per_reasoning_reward.scatter_reduce_(
        0, reasoning_inverse, exact_matches, reduce="amax", include_self=True
    )
    per_reasoning_sum = torch.zeros_like(per_reasoning_reward)
    per_reasoning_sum.scatter_add_(0, reasoning_inverse, exact_matches)
    per_reasoning_count = torch.bincount(reasoning_inverse, minlength=reasoning_count).to(exact_matches.dtype)

    sample_reasoning_count = per_reasoning_count[reasoning_inverse]
    leave_one_out = (per_reasoning_sum[reasoning_inverse] - exact_matches) / (sample_reasoning_count - 1).clamp_min(1)
    sid_advantages = torch.where(
        sample_reasoning_count > 1,
        exact_matches - leave_one_out,
        torch.zeros_like(exact_matches),
    )

    reasoning_prompt = torch.full(
        (reasoning_count,), prompt_count, dtype=torch.long, device=exact_matches.device
    )
    reasoning_prompt.scatter_reduce_(
        0, reasoning_inverse, prompt_inverse, reduce="amin", include_self=True
    )
    prompt_reasoning_count = torch.bincount(reasoning_prompt, minlength=prompt_count).to(exact_matches.dtype)
    prompt_reward_sum = torch.zeros(prompt_count, device=exact_matches.device)
    prompt_reward_sum.scatter_add_(0, reasoning_prompt, per_reasoning_reward)
    prompt_reward_mean = prompt_reward_sum / prompt_reasoning_count.clamp_min(1)

    centered_reward = per_reasoning_reward - prompt_reward_mean[reasoning_prompt]
    prompt_squared_sum = torch.zeros_like(prompt_reward_sum)
    prompt_squared_sum.scatter_add_(0, reasoning_prompt, centered_reward.square())
    prompt_reward_std = torch.sqrt(
        prompt_squared_sum / (prompt_reasoning_count - 1).clamp_min(1)
    )
    per_reasoning_advantage = torch.where(
        prompt_reward_std[reasoning_prompt] > 0,
        centered_reward / prompt_reward_std[reasoning_prompt].clamp_min(torch.finfo(exact_matches.dtype).eps),
        centered_reward,
    )

    return per_reasoning_advantage[reasoning_inverse], sid_advantages