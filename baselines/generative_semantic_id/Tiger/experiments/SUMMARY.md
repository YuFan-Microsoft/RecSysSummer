# TIGER reproduction — cross-category summary

## Best metrics (vs RUC/MTGRec reference)
| category | best arm | R@5 | R@10 | N@5 | N@10 | ref R@10 | Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| Musical_Instruments | narrow, lr 5e-4, do 0.10 | 0.0377 | **0.0579** | 0.0245 | 0.0310 | 0.0564 | +0.0015 |
| Industrial_and_Scientific | wide, lr 5e-4, do 0.20 | 0.0277 | **0.0442** | 0.0179 | 0.0231 | 0.0422 | +0.0020 |

Both reproduce ≥ reference. Fixed for all: rqkmeans L3/W256+dedup · sentence-t5-base · 4 layers · d_model 128 · mlp_layers 2 · wd 1e-6 · bs 256 · maxlen 20 · 200 ep · lr 5e-4.

## Best config per category
| category | arch (d_ff/heads) | dropout | lr |
|---|---|---|---|
| Musical_Instruments | 512 / 4 (narrow) | 0.10 | 5e-4 |
| Industrial_and_Scientific | 1024 / 6 (wide) | 0.20 | 5e-4 |

## Insights
- **Arch and dropout are category-dependent, and opposite here.** Musical (small ~24.6K) → narrow FFN + mild dropout 0.10; Industrial → wide FFN + strong dropout 0.20.
- **Dropout is an inverted-U**, peaks 0.10–0.20; ≥0.25 over-regularizes.
- **lr 5e-4 wins both** at the final arch; narrow tolerates higher lr, low lr (≤2e-4) under-fits.
- **2 rounds suffice**: r1 8-arm scan picks the winner, r2 only confirms convergence (no arm beat r1).

## Key takeaway
Reproduction matched/exceeded reference on both. Per-category tune just **{arch, dropout}**; keep **lr 5e-4** + shared defaults. Small catalog → narrow+light; larger/over-fit catalog → wide+heavy.
