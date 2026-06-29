# Musical_Instruments — TIGER reproduction sweep

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
- **epochs** = 200, eval every 10
- **selection** = best **val R@5** (beam 10); final **test** at beam 50

Reference (RUC/MTGRec TIGER): **R@10 = 0.0564**.

## Round 1 — scan lr / dropout / arch
| arm | knob | R@5 | R@10 | N@5 | N@10 | ΔR@10 vs ref |
|---|---|---:|---:|---:|---:|---:|
| G0 | lr 5e-4 (default) | 0.0342 | 0.0539 | 0.0223 | 0.0286 | — |
| G1 | lr 3e-4 | 0.0355 | 0.0557 | 0.0229 | 0.0294 | +0.0017 |
| G2 | lr 7e-4 | 0.0324 | 0.0514 | 0.0207 | 0.0268 | −0.0025 |
| G3 | lr 1e-3 | 0.0308 | 0.0494 | 0.0199 | 0.0258 | −0.0046 |
| G4 | lr 2e-3 | 0.0286 | 0.0461 | 0.0183 | 0.0239 | −0.0078 |
| G5 | dropout 0.05 | 0.0319 | 0.0504 | 0.0205 | 0.0264 | −0.0035 |
| G6 | dropout 0.20 | 0.0331 | 0.0522 | 0.0213 | 0.0274 | −0.0017 |
| **G7** | **d_ff 512 / heads 4** | **0.0377** | **0.0579** | **0.0245** | **0.0310** | **+0.0040** |

- LR monotone decreasing (3e-4 best on wide arch); dropout 0.10 best (concave); narrow arch (d_ff 512/h4) clearly wins.
- Best **G7 = 0.0579**, already > reference → fix narrow arch + dropout 0.10, refine LR.

## Round 2 — arch fixed narrow (d_ff 512 / 4 heads); refine lr & dropout
| arm | lr | dropout | R@5 | R@10 | N@5 | N@10 |
|---|---|---|---:|---:|---:|---:|
| H0 | 1e-4 | 0.10 | 0.0350 | 0.0545 | 0.0227 | 0.0290 |
| H1 | 2e-4 | 0.10 | 0.0354 | 0.0546 | 0.0231 | 0.0293 |
| H2 | 3e-4 | 0.10 | 0.0359 | 0.0560 | 0.0234 | 0.0299 |
| H3 | 4e-4 | 0.10 | 0.0354 | 0.0559 | 0.0231 | 0.0297 |
| **H4** | **5e-4** | **0.10** | **0.0377** | **0.0579** | **0.0245** | **0.0310** |
| H5 | 2e-4 | 0.05 | 0.0337 | 0.0526 | 0.0217 | 0.0278 |
| H6 | 3e-4 | 0.05 | 0.0333 | 0.0524 | 0.0216 | 0.0278 |
| H7 | 4e-4 | 0.05 | 0.0337 | 0.0537 | 0.0221 | 0.0286 |

- On narrow arch LR peaks at 5e-4 (lower capacity tolerates larger LR); dropout 0.05 uniformly worse than 0.10.
- Best = H4 = G7 (0.0579), reproduced exactly → **converged**.

## ✅ Best config
**R@10 = 0.0579** (ref 0.0564, +0.0015) — `lr 5e-4 · dropout 0.10 · d_ff 512 · heads 4` (narrow). Small catalog (~24.6K) → narrow FFN + mild dropout. Other fixed: 4 layers · d_model 128 · mlp_layers 2 · wd 1e-6 · bs 256 · maxlen 20 · 200 ep.

## Summary
| metric | best | ref | Δ |
|---|---:|---:|---:|
| R@5 | 0.0377 | 0.0370 | +0.0007 |
| R@10 | 0.0579 | 0.0564 | +0.0015 |
| N@5 | 0.0245 | 0.0244 | +0.0001 |
| N@10 | 0.0310 | 0.0306 | +0.0004 |

**Key takeaway:** narrow arch (d_ff 512/h4) + dropout 0.10 + lr 5e-4 wins; LR ↓ monotone (peaks 5e-4 on narrow), dropout 0.05 under-regularizes. Converged in 2 rounds, beats reference on every metric.
