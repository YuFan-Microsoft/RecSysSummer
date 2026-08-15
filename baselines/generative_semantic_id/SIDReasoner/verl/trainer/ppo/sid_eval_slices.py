from __future__ import annotations

import math
import re
from typing import Any


_SID_TOKEN_PATTERN = re.compile(r"<[^>]+>")
_SLICE_CUTOFFS = (5, 10)
SLICE_METRIC_KEYS = tuple(
    f"sid_eval_{slice_name}_{metric}_at_{cutoff}"
    for slice_name in ("novel", "repeat")
    for metric in ("hr", "ndcg")
    for cutoff in _SLICE_CUTOFFS
)


def _sid_tokens(value: Any) -> tuple[str, ...]:
    return tuple(_SID_TOKEN_PATTERN.findall(str(value))[:3])


def compute_novel_repeat_ranking_metrics(
    beam_predictions: list[Any],
    ground_truths: list[Any],
    history_sids: list[Any],
) -> dict[str, list[float | None]]:
    """Compute per-sample HR/NDCG@5,10 for novel and repeat targets."""
    if not (len(beam_predictions) == len(ground_truths) == len(history_sids)):
        raise ValueError("SID beams, ground truths, and histories must have the same length")

    metrics: dict[str, list[float | None]] = {key: [] for key in SLICE_METRIC_KEYS}
    for beam, ground_truth, sample_history_sids in zip(
        beam_predictions,
        ground_truths,
        history_sids,
    ):
        target_sid = _sid_tokens(ground_truth)
        if len(target_sid) != 3:
            raise ValueError(f"Expected a three-token ground-truth SID, got {ground_truth!r}")

        normalized_history = {_sid_tokens(history_sid) for history_sid in sample_history_sids}
        slice_name = "repeat" if target_sid in normalized_history else "novel"
        rank = next(
            (
                candidate_rank
                for candidate_rank, prediction in enumerate(list(beam)[:10], start=1)
                if _sid_tokens(prediction) == target_sid
            ),
            0,
        )
        sample_metrics: dict[str, float | None] = {key: None for key in SLICE_METRIC_KEYS}
        for cutoff in _SLICE_CUTOFFS:
            hit = 0 < rank <= cutoff
            sample_metrics[f"sid_eval_{slice_name}_hr_at_{cutoff}"] = float(hit)
            sample_metrics[f"sid_eval_{slice_name}_ndcg_at_{cutoff}"] = (
                1.0 / math.log2(rank + 1) if hit else 0.0
            )
        for key in SLICE_METRIC_KEYS:
            metrics[key].append(sample_metrics[key])

    return metrics


def mean_present_values(values: list[float | None]) -> float | None:
    """Average defined slice values, returning None for an empty slice."""
    present_values = [float(value) for value in values if value is not None]
    return sum(present_values) / len(present_values) if present_values else None