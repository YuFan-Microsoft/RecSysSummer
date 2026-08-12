# Phase-2 Rejection Sampling

For each history, sample exactly four target-blind reasoning traces. Run
catalog-constrained beam-100 for every unique reasoning. Among candidates that
pass deterministic rules and contain the target in beam-100, retain the one
with the best target rank. Drop the row when all four miss or fail rules.

```bash
python data_curation/rejection_sampling/distributed_phase3_inference.py \
  --checkpoint /path/to/best_checkpoint/actor_merged \
  --samples-per-prompt 4 \
  --num-beams 100 \
  --max-target-rank 100 \
  --gpus 0,1,2,3,4,5,6,7 \
  --output-dir ./rejection_sampling_beam100
```

Use a stricter value such as `--max-target-rank 20` after inspecting the pilot
rank distribution. A source row is omitted when all four candidates miss,
fail rules, or the best target rank exceeds this threshold.

The output directory contains only:

- `selected.jsonl`: one best accepted Phase-2 training row per retained source.
- `summary.json`: selected/dropped counts, selection rate, rank buckets, and
  oracle metrics at 1/2/4 reasoning samples.

Rules enforce V4 format, history-only SID citations, exploit/explore presence,
no exact duplicate claims, and no literal target leakage. They do not verify
semantic alignment with catalog descriptions.
