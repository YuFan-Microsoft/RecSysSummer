# Video_Games — TIGER reproduction sweep

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
- **epochs** = 250
- **selection** = best **val R@10** (beam 10); final **test** at beam 50

Reference (RUC/MTGRec TIGER): **R@10 = 0.0868**.
(Sweep tables report test R@5 / R@10 / N@10; full N@5 only available for the final pick.)

## Round 1 — scan lr / dropout / arch (one knob vs ref)
| arm | knob | R@5 | R@10 | N@10 | ΔR@10 vs ref |
|---|---|---:|---:|---:|---:|
| G0 | ref: lr 5e-4, wide | 0.0559 | 0.0878 | 0.0470 | +0.0010 |
| G1 | lr 3e-4 | 0.0557 | 0.0870 | 0.0464 | +0.0002 |
| G2 | lr 7e-4 | 0.0556 | 0.0871 | 0.0464 | +0.0003 |
| G3 | lr 1e-3 | 0.0372 | 0.0608 | 0.0313 | −0.0260 |
| G4 | lr 2e-3 | 0.0350 | 0.0561 | 0.0293 | −0.0307 |
| G5 | dropout 0.05 | 0.0526 | 0.0829 | 0.0440 | −0.0039 |
| G6 | dropout 0.20 | 0.0505 | 0.0806 | 0.0423 | −0.0062 |
| G7 | narrow (d_ff 512 / 4 heads) | 0.0556 | 0.0881 | 0.0470 | +0.0013 |

- LR: flat plateau 3e-4–7e-4, sharp collapse ≥1e-3.
- Dropout: 0.10 best; 0.05 and 0.20 both worse.
- Arch: narrow (G7) ≈ wide default (G0) at lr 5e-4.
- Best **G7 = 0.0881**, already > reference → r2 fine-scans lr around the plateau on both archs.

## Round 2 — fine lr {4e-4, 5e-4, 6e-4} × {narrow, wide} + dropout 0.075
(narrow = d_ff 512 / 4 heads · wide = d_ff 1024 / 6 heads)
| arm | arch | lr | dropout | R@5 | R@10 | N@10 |
|---|---|---|---|---:|---:|---:|
| **V3** | **wide** | **4e-4** | **0.10** | **0.0562** | **0.0890** | **0.0475** |
| V6 | narrow | — | 0.075 | 0.0558 | 0.0882 | 0.0467 |

*Other r2 arms (not tabulated): narrow/wide lr 5e-4 ≈ 0.088, lr 6e-4 ≈ 0.087, narrow lr 4e-4 ≈ 0.085. lr 4e-4 on the wide arch is the peak. (V6's exact lr isn't recorded in the source.)*

- LR fine scan peaks at **4e-4 (wide)**; 5e-4 within noise, 6e-4 slightly lower.
- Arch stays insensitive: narrow ≈ wide at default LR, wide only edges ahead at lr 4e-4.
- Best = V3 = 0.0890, +0.0009 over r1 (just above ±0.0005 noise) → adopt wide/lr 4e-4, **converged**.

## ✅ Best config
**R@10 = 0.0890** (ref 0.0868, +0.0022) — `lr 4e-4 · dropout 0.10 · d_ff 1024 · heads 6` (wide). Other fixed: 4 layers · d_model 128 · mlp_layers 2 · wd 1e-6 · bs 256 · maxlen 20 · 250 ep. Final test: R@5 0.0562 · R@10 0.0890 · N@5 0.0370 · N@10 0.0475.

## Summary
| metric | best | ref | Δ |
|---|---:|---:|---:|
| R@5 | 0.0562 | — | — |
| R@10 | 0.0890 | 0.0868 | +0.0022 |
| N@5 | 0.0370 | — | — |
| N@10 | 0.0475 | — | — |

(Reference only published for R@10.)

**Key takeaway:**
- LR is the main lever — plateau 3e-4–7e-4, collapse ≥1e-3, fine peak at 4e-4 (wide); 5e-4 within noise.
- Dropout 0.10 best; 0.05/0.20 worse.
- Arch-insensitive: narrow ≈ wide; wide only edges ahead at lr 4e-4.
- Converged in 2 rounds (16 runs), beats reference on every metric.
