from __future__ import annotations

import re
from typing import Any, Callable, Optional

from phase3_interest_retriever.client import InterestRetrieverClient
from verl.utils.reward_score.sid_reasoning_format import extract_future_interest_texts


_SID_PATTERN = re.compile(r"<a_\d+><b_\d+><c_\d+>")
_MONITORED_CUTOFFS = (10, 20, 50, 100)
_VALIDATION_CUTOFFS = (20, 50, 100)


def _extract_target_sid(value: Any) -> str:
    text = str(value).strip()
    match = _SID_PATTERN.fullmatch(text)
    if match is None:
        raise ValueError(f"ground truth must be exactly one SID: {value}")
    return match.group(0)


def _chunked(values: list[Any], chunk_size: int):
    for start in range(0, len(values), chunk_size):
        yield values[start : start + chunk_size]


def _best_rank(ranks: list[int]) -> float:
    positive_ranks = [rank for rank in ranks if rank > 0]
    return float(min(positive_ranks)) if positive_ranks else -1.0


def evaluate_interest_rewards(
    solutions: list[str],
    target_sids: list[str],
    endpoint: str,
    reward_top_k: int,
    request_batch_size: int = 2048,
    timeout: int = 600,
    max_attempts: int = 3,
    client_factory: Optional[Callable[..., Any]] = None,
) -> dict[str, list[float]]:
    if len(solutions) != len(target_sids):
        raise ValueError("solutions and target_sids must have the same length")
    if not 1 <= reward_top_k <= 100:
        raise ValueError("reward_top_k must be between 1 and 100")
    if request_batch_size < 1 or request_batch_size > 8192:
        raise ValueError("request_batch_size must be between 1 and 8192")

    sample_interest_ranks: list[list[int]] = [[] for _ in solutions]
    requests: list[dict[str, str]] = []
    request_sample_indices: list[int] = []
    interest_counts = []
    format_valid = []
    for sample_index, (solution, target_sid) in enumerate(zip(solutions, target_sids)):
        interests = extract_future_interest_texts(solution)
        interest_counts.append(float(len(interests)))
        format_valid.append(float(bool(interests)))
        for interest in interests:
            requests.append({"interest": interest, "target_sid": target_sid})
            request_sample_indices.append(sample_index)

    if requests:
        factory = client_factory or InterestRetrieverClient
        client = factory(endpoint, timeout=timeout, max_attempts=max_attempts)
        all_ranks: list[int] = []
        for request_batch in _chunked(requests, request_batch_size):
            all_ranks.extend(client.rank_batch(request_batch))
        if len(all_ranks) != len(requests):
            raise RuntimeError("rank endpoint returned the wrong number of results")
        for sample_index, rank in zip(request_sample_indices, all_ranks):
            rank = int(rank)
            if rank < -1 or rank > 100 or rank == 0:
                raise RuntimeError(f"rank endpoint returned invalid rank: {rank}")
            sample_interest_ranks[sample_index].append(rank)

    block_ranks = [_best_rank(ranks) for ranks in sample_interest_ranks]
    output: dict[str, list[float]] = {
        "interest_reward": [
            float(0 < rank <= reward_top_k) for rank in block_ranks
        ],
        "interest_block_rank": block_ranks,
        "interest_query_count": interest_counts,
        "interest_format_valid": format_valid,
    }
    for cutoff in _MONITORED_CUTOFFS:
        output[f"interest_hit_at_{cutoff}"] = [
            float(0 < rank <= cutoff) for rank in block_ranks
        ]
    return output


def build_interest_validation_metrics(
    interest_results: dict[str, list[float]],
    sid_hit_at_10: list[float],
) -> dict[str, list[float]]:
    sid_hits = [bool(value) for value in sid_hit_at_10]
    metrics: dict[str, list[float]] = {}
    for cutoff in _VALIDATION_CUTOFFS:
        interest_hits = [bool(value) for value in interest_results[f"interest_hit_at_{cutoff}"]]
        if len(interest_hits) != len(sid_hits):
            raise ValueError("Interest and SID validation metrics must have the same length")
        metrics[f"interest_only_hit_at_{cutoff}"] = [
            float(interest_hit and not sid_hit)
            for interest_hit, sid_hit in zip(interest_hits, sid_hits)
        ]
    return metrics


def decode_interest_reward_inputs(batch: Any, tokenizer: Any) -> tuple[list[str], list[str]]:
    solutions = []
    target_sids = []
    for sample_index in range(len(batch)):
        item = batch[sample_index]
        prompt_length = item.batch["prompts"].shape[-1]
        valid_response_length = int(item.batch["attention_mask"][prompt_length:].sum())
        valid_response_ids = item.batch["responses"][:valid_response_length]
        solutions.append(tokenizer.decode(valid_response_ids, skip_special_tokens=True))
        try:
            target_sids.append(
                _extract_target_sid(item.non_tensor_batch["reward_model"]["ground_truth"])
            )
        except ValueError as error:
            raise ValueError(f"interest reward sample {sample_index}: {error}") from error
    return solutions, target_sids


def compute_batch_interest_rewards(
    batch: Any,
    tokenizer: Any,
    config: Any,
) -> dict[str, list[float]]:
    if not config.endpoint:
        raise ValueError("Enabled interest reward requires a nonempty endpoint")
    solutions, target_sids = decode_interest_reward_inputs(batch, tokenizer)
    return evaluate_interest_rewards(
        solutions=solutions,
        target_sids=target_sids,
        endpoint=str(config.endpoint),
        reward_top_k=int(config.reward_top_k),
        request_batch_size=int(config.get("request_batch_size", 2048)),
        timeout=int(config.get("timeout", 600)),
        max_attempts=int(config.get("max_attempts", 3)),
    )