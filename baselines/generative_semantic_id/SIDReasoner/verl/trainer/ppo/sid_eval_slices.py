from __future__ import annotations

import math
import re
from typing import Any


_SID_TOKEN_PATTERN = re.compile(r"<[^>]+>")
_SLICE_CUTOFFS = (5, 10)


def _sid_tokens(value: Any) -> tuple[str, ...]:
    return tuple(_SID_TOKEN_PATTERN.findall(str(value))[:3])


def compute_novel_repeat_ranking_metrics(
    beam_predictions: list[Any],
    ground_truths: list[Any],
    history_sids: list[Any],
) -> dict[str, list[float]]:
    """Compute per-sample HR/NDCG@5,10 for novel and repeat targets."""
    if not (len(beam_predictions) == len(ground_truths) == len(history_sids)):
        raise ValueError("SID beams, ground truths, and histories must have the same length")

    metrics = {
        f"sid_eval_{slice_name}_{metric}_at_{cutoff}": []
        for slice_name in ("novel", "repeat")
        for metric in ("hr", "ndcg")
        for cutoff in _SLICE_CUTOFFS
    }
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
        for cutoff in _SLICE_CUTOFFS:
            hit = 0 < rank <= cutoff
            metrics[f"sid_eval_{slice_name}_hr_at_{cutoff}"].append(float(hit))
            metrics[f"sid_eval_{slice_name}_ndcg_at_{cutoff}"].append(
                1.0 / math.log2(rank + 1) if hit else 0.0
            )

    return metrics