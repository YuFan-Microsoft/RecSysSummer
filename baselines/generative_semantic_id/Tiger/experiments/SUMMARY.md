# TIGER reproduction — cross-category summary

## Best metrics (vs RUC/MTGRec reference)
| category | best arm | R@5 | R@10 | N@5 | N@10 | ref R@10 | Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| Musical_Instruments | narrow, lr 5e-4, do 0.10 | 0.0377 | **0.0579** | 0.0245 | 0.0310 | 0.0564 | +0.0015 |
| Industrial_and_Scientific | wide, lr 5e-4, do 0.20 | 0.0277 | **0.0442** | 0.0179 | 0.0231 | 0.0422 | +0.0020 |
| Video_Games | wide, lr 4e-4, do 0.10 | 0.0562 | **0.0890** | 0.0370 | 0.0475 | 0.0868 | +0.0022 |

All three reproduce ≥ reference. Shared: rqkmeans L3/W256+dedup · sentence-t5-base · 4 layers · d_model 128 · mlp_layers 2 · wd 1e-6 · bs 256 · maxlen 20. (Video_Games uses 250 ep / lr 4e-4; the other two 200 ep / lr 5e-4.)

## Best config per category
| category | arch (d_ff/heads) | dropout | lr | epochs |
|---|---|---|---|---|
| Musical_Instruments | 512 / 4 (narrow) | 0.10 | 5e-4 | 200 |
| Industrial_and_Scientific | 1024 / 6 (wide) | 0.20 | 5e-4 | 200 |
| Video_Games | 1024 / 6 (wide) | 0.10 | 4e-4 | 250 |

## Insights
- **Arch and dropout are category-dependent.** Musical (small ~24.6K) → narrow FFN + mild dropout 0.10; Industrial → wide FFN + strong dropout 0.20; Video_Games → wide FFN + dropout 0.10. On Industrial and Video_Games arch barely matters (narrow/wide near-tied at matched dropout); the wide pick only edges ahead at its peak.
- **Dropout is an inverted-U**, peaks 0.10–0.20; 0.05 under- and ≥0.25 over-regularizes.
- **lr sits in 4e-4–5e-4**; Musical/Industrial peak at 5e-4, Video_Games at 4e-4 (5e-4 within noise). High lr ≥1e-3 hurts everywhere (a hard collapse on Video_Games); very low lr under-fits where tested (Musical ≤2e-4).
- **2 rounds suffice**: r1 8-arm scan picks the winner, r2 only confirms convergence.

## Key takeaway
Reproduction matched/exceeded reference on all three. Per-category tune just **{arch, dropout, lr in 4–5e-4}** + shared defaults. Small catalog → narrow+light dropout; larger/over-fit catalog → wide; arch is often near-insensitive, so dropout and lr are the real levers.
