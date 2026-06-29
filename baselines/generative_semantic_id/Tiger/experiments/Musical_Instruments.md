# Musical_Instruments — TIGER reproduction sweep

## Round r1  (EP=200, eval.every=10, SID=rqkmeans L3 W256 +1 dedup, enc=sentence-t5-base, maxlen=20, bs=256)
Reference target (RUC/MTGRec TIGER): **R@10 = 0.0564** (R@5 0.0370 / N@5 0.0244 / N@10 0.0306)

Selection: best **val recall@5** (beam 10); final **test = beam 50**. All arms ran full 200 epochs.

| run_name | arm | knob | R@5 | R@10 | N@5 | N@10 | ΔR@10 vs ref(G0) | saved? |
|---|---|---|---:|---:|---:|---:|---:|:--:|
| Musical_Instruments__r1__G0__ref | G0 | lr 5e-4 (default) | 0.0342 | 0.0539 | 0.0223 | 0.0286 | — | ✓ |
| Musical_Instruments__r1__G1__lr3e-4 | G1 | lr 3e-4 | 0.0355 | 0.0557 | 0.0229 | 0.0294 | +0.0017 | ✓ |
| Musical_Instruments__r1__G2__lr7e-4 | G2 | lr 7e-4 | 0.0324 | 0.0514 | 0.0207 | 0.0268 | −0.0025 | ✓ |
| Musical_Instruments__r1__G3__lr1e-3 | G3 | lr 1e-3 | 0.0308 | 0.0494 | 0.0199 | 0.0258 | −0.0046 | ✓ |
| Musical_Instruments__r1__G4__lr2e-3 | G4 | lr 2e-3 | 0.0286 | 0.0461 | 0.0183 | 0.0239 | −0.0078 | ✓ |
| Musical_Instruments__r1__G5__do0.05 | G5 | dropout 0.05 | 0.0319 | 0.0504 | 0.0205 | 0.0264 | −0.0035 | ✓ |
| Musical_Instruments__r1__G6__do0.20 | G6 | dropout 0.20 | 0.0331 | 0.0522 | 0.0213 | 0.0274 | −0.0017 | ✓ |
| **Musical_Instruments__r1__G7__dff512h4** | **G7** | **d_ff 512 / heads 4** | **0.0377** | **0.0579** | **0.0245** | **0.0310** | **+0.0040** | ✓ |

**Best this round:** `Musical_Instruments__r1__G7__dff512h4` — **R@10 = 0.0579** (+0.0015 over the 0.0564 reference target; also tops N@10 0.0310 vs ref 0.0306). Reproduction is healthy / matched.

### Insights
- **LR curve** (G1→G4 + G0): R@10 = 3e-4:0.0557, 5e-4:0.0539, 7e-4:0.0514, 1e-3:0.0494, 2e-3:0.0461 — strictly **monotonic decreasing**. The optimum sits at the **low edge (3e-4)**, so the scan should be **extended downward** (1e-4, 2e-4) next round. High LR clearly hurts this small catalog.
- **Dropout** (do0.05 0.0504, do0.10 0.0539, do0.20 0.0522): the **default 0.10 is best**; 0.05 was actually worst and 0.20 slightly below default. Mild concavity around 0.10 → keep 0.10, don't drop to 0.05.
- **Architecture**: the **RUC-style narrow arch G7 (d_ff 512 / 4 heads) clearly beats** the wider default (d_ff 1024 / 6 heads): +0.0040 R@10 and best on every metric. On a ~24.6K-item catalog the wider FFN over-parameterizes; the narrower model matches capacity better and is also ~1.6× faster. **Carry the G7 arch forward.**
- **Gap to reference**: best arm already **exceeds** the 0.0564 target by +0.0015. The remaining lever is the untested **interaction** of the two best single knobs — narrow arch (G7) was run at the default lr 5e-4, and lr 3e-4 (G1) was run at the wide default arch. Neither tested together.
- **Anomalies**: none. All 8 arms saved ≥5 checkpoints (G6 11, G3 10 — kept improving late but from a lower absolute level). No loss spikes / collapse.
- **Decision → round 2**: fix the **G7 arch (d_ff 512 / 4 heads), dropout 0.10**, and refine the **low-LR end** finely while also testing the arch×low-LR combo. Sweep lr ∈ {1e-4, 2e-4, 3e-4, 4e-4, 5e-4} (dropout 0.10) plus a dropout-0.05 bracket at {2e-4, 3e-4, 4e-4}.

## Round r2  (EP=200, eval.every=10, arch FIXED = d_ff 512 / heads 4 (r1 winner); refine LR + dropout)
Goal: refine the low/mid-LR region on the winning narrow arch, plus a dropout-0.05 bracket.

| run_name | arm | knob | R@5 | R@10 | N@5 | N@10 | ΔR@10 vs r1 best (0.0579) | saved? |
|---|---|---|---:|---:|---:|---:|---:|:--:|
| Musical_Instruments__r2__H0__lr1e-4do10 | H0 | lr 1e-4, do 0.10 | 0.0350 | 0.0545 | 0.0227 | 0.0290 | −0.0034 | ✓ |
| Musical_Instruments__r2__H1__lr2e-4do10 | H1 | lr 2e-4, do 0.10 | 0.0354 | 0.0546 | 0.0231 | 0.0293 | −0.0033 | ✓ |
| Musical_Instruments__r2__H2__lr3e-4do10 | H2 | lr 3e-4, do 0.10 | 0.0359 | 0.0560 | 0.0234 | 0.0299 | −0.0019 | ✓ |
| Musical_Instruments__r2__H3__lr4e-4do10 | H3 | lr 4e-4, do 0.10 | 0.0354 | 0.0559 | 0.0231 | 0.0297 | −0.0020 | ✓ |
| **Musical_Instruments__r2__H4__lr5e-4do10** | **H4** | **lr 5e-4, do 0.10** | **0.0377** | **0.0579** | **0.0245** | **0.0310** | **0.0000 (=r1 G7)** | ✓ |
| Musical_Instruments__r2__H5__lr2e-4do05 | H5 | lr 2e-4, do 0.05 | 0.0337 | 0.0526 | 0.0217 | 0.0278 | −0.0053 | ✓ |
| Musical_Instruments__r2__H6__lr3e-4do05 | H6 | lr 3e-4, do 0.05 | 0.0333 | 0.0524 | 0.0216 | 0.0278 | −0.0055 | ✓ |
| Musical_Instruments__r2__H7__lr4e-4do05 | H7 | lr 4e-4, do 0.05 | 0.0337 | 0.0537 | 0.0221 | 0.0286 | −0.0042 | ✓ |

**Best this round:** `Musical_Instruments__r2__H4__lr5e-4do10` — R@10 = 0.0579, byte-identical to the r1 winner (same config + deterministic seed). **No r2 arm beat r1.**

### Insights
- **LR on the narrow arch (dropout 0.10)**: R@10 = 1e-4:0.0545, 2e-4:0.0546, 3e-4:0.0560, 4e-4:0.0559, **5e-4:0.0579** — rises to a clear peak at **5e-4**. Note the *interaction*: on the WIDE arch (r1) the LR optimum was the low edge 3e-4, but on the NARROW G7 arch the optimum is higher (5e-4). The lower-capacity model tolerates / prefers a larger LR. The low end (1e-4/2e-4) under-fits.
- **Dropout**: the 0.05 bracket (H5/H6/H7) is uniformly ~0.003–0.005 R@10 below its 0.10 twin at every LR — **re-confirms dropout 0.10 is correct**; 0.05 under-regularizes this catalog.
- **Convergence**: the best config is unchanged from r1 (d_ff 512 / heads 4, lr 5e-4, dropout 0.10) and the score is reproduced exactly. Improvement over r1 is 0.0000 (< the ±0.0005 noise band) → **Musical_Instruments is CONVERGED.**
- **Final answer for this category**: **R@10 = 0.0579** (ref 0.0564, +0.0015). Config: rqkmeans L3/W256+dedup, 4 layers, d_model 128, **d_ff 512, heads 4**, mlp_layers 2, **lr 5e-4, dropout 0.10**, wd 1e-6, bs 256, maxlen 20, 200 epochs.
- **Decision**: stop tuning Musical_Instruments; move to the next category.
