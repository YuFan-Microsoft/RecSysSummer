# TIGER reproduction — cross-category summary

## Best metrics (vs RUC/MTGRec reference)
| category | best arm | R@5 | R@10 | N@5 | N@10 | ref R@10 | Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| Musical_Instruments | narrow, lr 5e-4, do 0.10 | 0.0377 | **0.0579** | 0.0245 | 0.0310 | 0.0564 | +0.0015 |
| Industrial_and_Scientific | wide, lr 5e-4, do 0.20 | 0.0277 | **0.0442** | 0.0179 | 0.0231 | 0.0422 | +0.0020 |
| Video_Games | wide, lr 4e-4, do 0.10 | 0.0562 | **0.0890** | 0.0370 | 0.0475 | 0.0868 | +0.0022 |
| Beauty_and_Personal_Care | wide, lr 5e-4, do 0.05 | 0.0183 | **0.0286** | 0.0119 | 0.0153 | 0.0163 | +0.0123 |

All four reproduce ≥ reference. Shared: rqkmeans L3/W256+dedup · sentence-t5-base · 4 layers · d_model 128 · mlp_layers 2 · wd 1e-6 · bs 256 · maxlen 20. (Epochs: Video_Games 250, Musical/Industrial 200, Beauty 30. lr: Video_Games 4e-4, the others 5e-4.)

## Best config per category
| category | arch (d_ff/heads) | dropout | lr | epochs |
|---|---|---|---|---|
| Musical_Instruments | 512 / 4 (narrow) | 0.10 | 5e-4 | 200 |
| Industrial_and_Scientific | 1024 / 6 (wide) | 0.20 | 5e-4 | 200 |
| Video_Games | 1024 / 6 (wide) | 0.10 | 4e-4 | 250 |
| Beauty_and_Personal_Care | 1024 / 6 (wide) | 0.05 | 5e-4 | 30 |

## Insights
- **Arch and dropout are category-dependent.** Musical (small ~24.6K) → narrow FFN + mild dropout 0.10; Industrial → wide FFN + strong dropout 0.20; Video_Games → wide FFN + dropout 0.10; Beauty (large, 6.6M interactions / 207K items) → wide FFN + low dropout 0.05. On Industrial and Video_Games arch barely matters (narrow/wide near-tied at matched dropout); the wide pick only edges ahead at its peak.
- **Dropout is an inverted-U** whose peak shifts with catalog size — 0.10–0.20 for the small/mid categories, dropping to 0.05 for the very large Beauty (more data → less regularization); ≥0.25 over-regularizes.
- **lr sits in 4e-4–5e-4** for the chosen configs; Musical/Industrial best at 5e-4, Video_Games at 4e-4 (5e-4 within noise). Beauty's lr sweep actually favors 3e-4 at matched dropout — its 5e-4 pick only ties once paired with dropout 0.05. High lr ≥1e-3 hurts everywhere (a hard collapse on Video_Games; Beauty's 2e-3 dips below reference); very low lr under-fits where tested (Musical ≤2e-4).
- **1–2 rounds suffice**: the r1 8-arm scan already picks the winner (Beauty converged in r1 alone); r2 only confirms convergence.

## Key takeaway
Reproduction matched/exceeded reference on all four. Per-category tune just **{arch, dropout, lr in 4–5e-4}** + shared defaults. Small catalog → narrow + light dropout; larger/over-fit catalog → wide; very large catalog (Beauty) → wide + minimal dropout 0.05. Arch is often near-insensitive, so dropout and lr are the real levers.
