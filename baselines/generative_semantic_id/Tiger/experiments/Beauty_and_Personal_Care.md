# Beauty_and_Personal_Care — TIGER reproduction sweep

**Fixed config (same for every arm):**
- **SID** = rqkmeans, L3/W256 +1 dedup — semantic-ID quantizer: 3 codebook levels, 256 codewords each, +1 dedup token
- **encoder** = sentence-t5-base — text encoder for item embeddings
- **layers** = 4 — transformer encoder/decoder depth (each)
- **d_model** = 128 — token/embedding width (the model's hidden size)
- **d_ff** = swept — feed-forward inner width (FFN); narrow 512 / wide 1024
- **heads** = swept — attention heads; narrow 4 / wide 6
- **mlp_layers** = 2 — layers in the FFN block
- **wd** = 1e-6 — weight decay
- **bs** = 256 — batch size
- **maxlen** = 20 — max user history length
- **epochs** = 30
- **selection** = best **val R@10** (beam 10); final **test** at beam 50

Reference (RUC/MTGRec TIGER): **R@10 = 0.0163**.
(Catalog: 6.6M interactions, 207K items.)

## Round 1 — scan lr / dropout / arch (one knob vs ref)
| arm | knob | R@5 | R@10 | N@5 | N@10 | ΔR@10 vs ref |
|---|---|---:|---:|---:|---:|---:|
| G0 | ref: lr 5e-4, do 0.10, wide | 0.0119 | 0.0192 | 0.0077 | 0.0100 | +0.0029 |
| G1 | lr 3e-4 | 0.0182 | 0.0286 | 0.0119 | 0.0152 | +0.0123 |
| G2 | lr 7e-4 | 0.0112 | 0.0180 | 0.0073 | 0.0094 | +0.0017 |
| G3 | lr 1e-3 | 0.0106 | 0.0168 | 0.0069 | 0.0089 | +0.0005 |
| G4 | lr 2e-3 | 0.0088 | 0.0141 | 0.0056 | 0.0073 | −0.0022 |
| **G5** | **dropout 0.05** | **0.0183** | **0.0286** | **0.0119** | **0.0153** | **+0.0123** |
| G6 | dropout 0.20 | 0.0104 | 0.0167 | 0.0068 | 0.0088 | +0.0004 |
| G7 | narrow (d_ff 512 / 4 heads) | 0.0150 | 0.0239 | 0.0097 | 0.0126 | +0.0076 |

- Dropout is the dominant lever: 0.10→0.05 lifts R@10 +49% (G0→G5) — lots of data → less regularization needed; do 0.20 collapses.
- LR: 3e-4 best, 5e-4 only competitive at low dropout, ≥7e-4 hurts hard.
- Arch: wide ≥ narrow (G7).
- Best **G5 = 0.0286** (lr 5e-4, do 0.05, wide), tied by **G1** (lr 3e-4, do 0.10); both beat reference by **+75%** → **converged on r1**.

## ✅ Best config
**R@10 = 0.0286** (ref 0.0163, +0.0123 / +75%) — `lr 5e-4 · dropout 0.05 · d_ff 1024 · heads 6` (wide). Other fixed: 4 layers · d_model 128 · mlp_layers 2 · wd 1e-6 · bs 256 · maxlen 20 · 30 ep. Final test (G5): R@5 0.0183 · R@10 0.0286 · N@5 0.0119 · N@10 0.0153. Tied by G1 (lr 3e-4, do 0.10).

## Summary
| metric | best |
|---|---:|
| R@5 | 0.0183 |
| R@10 | 0.0286 |
| N@5 | 0.0119 |
| N@10 | 0.0153 |

(Reference only published for R@10: 0.0163 → **+0.0123 / +75%**.)

**Key takeaway:**
- Dropout is the big lever — the very large catalog pushes the optimum down to 0.05 (0.10→0.05 = +49% R@10); do 0.20 collapses.
- lr 3e-4 best; 5e-4 competitive only at low dropout; ≥7e-4 hurts hard.
- Arch: wide ≥ narrow.
- **Opposite of small catalogs:** Beauty (6.6M interactions, 207K items) wants low dropout + low lr, unlike Musical's narrow + do 0.10.
- Converged in 1 round (8 runs), beats reference by +75%.
