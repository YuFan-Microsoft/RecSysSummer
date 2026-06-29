# Industrial_and_Scientific — TIGER reproduction sweep

## Round r1  (EP=200, eval.every=10, SID=rqkmeans L3 W256 +1 dedup, enc=sentence-t5-base, maxlen=20, bs=256)
Reference target (RUC/MTGRec TIGER): **R@10 = 0.0422** (R@5 0.0264 / N@5 0.0175 / N@10 0.0226)

| run_name | arm | knob | R@5 | R@10 | N@5 | N@10 | ΔR@10 vs ref(G0) | saved? |
|---|---|---|---:|---:|---:|---:|---:|:--:|
| Industrial_and_Scientific__r1__G0__ref | G0 | lr 5e-4 (default) | 0.0250 | 0.0407 | 0.0160 | 0.0210 | — | ✓ |
| Industrial_and_Scientific__r1__G1__lr3e-4 | G1 | lr 3e-4 | 0.0248 | 0.0392 | 0.0159 | 0.0205 | −0.0015 | ✓ |
| Industrial_and_Scientific__r1__G2__lr7e-4 | G2 | lr 7e-4 | 0.0225 | 0.0363 | 0.0146 | 0.0189 | −0.0045 | ✓ |
| Industrial_and_Scientific__r1__G3__lr1e-3 | G3 | lr 1e-3 | 0.0218 | 0.0349 | 0.0139 | 0.0181 | −0.0058 | ✓ |
| Industrial_and_Scientific__r1__G4__lr2e-3 | G4 | lr 2e-3 | 0.0185 | 0.0307 | 0.0116 | 0.0155 | −0.0100 | ✓ |
| Industrial_and_Scientific__r1__G5__do0.05 | G5 | dropout 0.05 | 0.0227 | 0.0360 | 0.0146 | 0.0188 | −0.0047 | ✓ |
| **Industrial_and_Scientific__r1__G6__do0.20** | **G6** | **dropout 0.20** | **0.0277** | **0.0442** | **0.0179** | **0.0231** | **+0.0034** | ✓ |
| Industrial_and_Scientific__r1__G7__dff512h4 | G7 | d_ff 512 / heads 4 | 0.0264 | 0.0418 | 0.0170 | 0.0220 | +0.0010 | ✓ |

**Best this round:** `Industrial_and_Scientific__r1__G6__do0.20` — **R@10 = 0.0442** (+0.0020 over the 0.0422 reference; tops every metric). Reproduction matched/exceeded.

### Insights
- **Dropout is the dominant lever here** (opposite of Musical_Instruments): R@10 = 0.05:0.0360, 0.10:0.0407, **0.20:0.0442** — strictly increasing. The optimum sits at the **high edge (0.20)**, so r2 must **extend dropout upward (0.25, 0.30)**. This catalog clearly over-fits at the default 0.10; stronger regularization helps a lot. (G6 also saved 18 checkpoints — it kept improving late, the hallmark of a well-regularized run.)
- **LR curve** (G1→G4 + G0): R@10 = 3e-4:0.0392, **5e-4:0.0407**, 7e-4:0.0363, 1e-3:0.0349, 2e-3:0.0307 — peak at the **center (5e-4 = default)**; both lower (3e-4) and higher LR are worse. So **keep lr 5e-4** and do NOT scan LR further. (Contrast Musical, where 3e-4 was best on the wide arch — category-dependent.)
- **Architecture**: narrow G7 (d_ff 512 / 4 heads) at 0.0418 still beats the wide default G0 at 0.0407 (+0.0010), consistent with Musical — narrow arch helps. But the *single biggest* knob (G6 dropout 0.20, on the wide arch) beat narrow G7. The obvious untested combo is **narrow arch × high dropout**, which r2 will test.
- **Gap to reference**: best arm already exceeds 0.0422 by +0.0020. Remaining upside likely from (a) pushing dropout to 0.25–0.30 and (b) stacking narrow arch with high dropout.
- **Anomalies**: none. All arms saved ≥4 ckpts; high-LR arms (G3/G4) saved many early but plateaued low.
- **Decision → round 2**: fix **lr 5e-4**. 2-arch × dropout-ladder design: {narrow d_ff512h4, wide default} × dropout {0.15, 0.20, 0.25, 0.30}, to (1) extend the dropout optimum and (2) test the narrow×high-dropout interaction. Plus one lower-LR interaction probe.

## Round r2  (EP=200, eval.every=10, lr 5e-4 FIXED; 2 archs × dropout ladder {0.15,0.20,0.25,0.30})
Goal: extend the r1 dropout optimum upward and test the narrow×high-dropout interaction. arch: narrow = d_ff512/h4, wide = default d_ff1024/h6.

| run_name | arm | knob | R@5 | R@10 | N@5 | N@10 | ΔR@10 vs r1 best (0.0442) | saved? |
|---|---|---|---:|---:|---:|---:|---:|:--:|
| Industrial_and_Scientific__r2__I0__narrowdo15 | I0 | narrow, do 0.15 | 0.0275 | 0.0429 | 0.0177 | 0.0227 | −0.0013 | ✓ |
| Industrial_and_Scientific__r2__I1__narrowdo20 | I1 | narrow, do 0.20 | 0.0257 | 0.0411 | 0.0166 | 0.0216 | −0.0031 | ✓ |
| Industrial_and_Scientific__r2__I2__narrowdo25 | I2 | narrow, do 0.25 | 0.0253 | 0.0404 | 0.0161 | 0.0210 | −0.0038 | ✓ |
| Industrial_and_Scientific__r2__I3__narrowdo30 | I3 | narrow, do 0.30 | 0.0201 | 0.0333 | 0.0129 | 0.0171 | −0.0109 | ✓ |
| **Industrial_and_Scientific__r2__I4__widedo15** | **I4** | **wide, do 0.15** | **0.0278** | **0.0439** | **0.0179** | **0.0231** | **−0.0003** | ✓ |
| Industrial_and_Scientific__r2__I5__widedo25 | I5 | wide, do 0.25 | 0.0243 | 0.0402 | 0.0155 | 0.0206 | −0.0040 | ✓ |
| Industrial_and_Scientific__r2__I6__widedo30 | I6 | wide, do 0.30 | 0.0204 | 0.0330 | 0.0129 | 0.0170 | −0.0112 | ✓ |
| Industrial_and_Scientific__r2__I7__narrowdo20lr3e4 | I7 | narrow, do 0.20, lr 3e-4 | 0.0263 | 0.0414 | 0.0166 | 0.0215 | −0.0028 | ✓ |

**Best this round:** `Industrial_and_Scientific__r2__I4__widedo15` — R@10 = 0.0439, which is **−0.0003 below** the r1 winner (within the ±0.0005 noise band). **r2 did not beat r1.**

### Insights
- **Full dropout curve (wide arch, lr 5e-4, r1+r2 combined)**: 0.05:0.0360, 0.10:0.0407, **0.15:0.0439, 0.20:0.0442 (peak)**, 0.25:0.0402, 0.30:0.0330. A clear inverted-U: the optimum is **~0.15–0.20** (0.15 and 0.20 statistically tied), and **0.25/0.30 over-regularize hard**. So r1's "monotone increasing" was only the left half of the curve — the peak is at 0.20, not beyond. **Dropout 0.20 is the answer.**
- **Narrow arch curve (lr 5e-4)**: do0.10:0.0418, do0.15:0.0429 (peak), do0.20:0.0411, ... — narrow peaks slightly earlier (0.15) and lower than wide.
- **Architecture × dropout interaction**: narrow did **not** stack with high dropout to beat wide. At every matched dropout the **wide default arch ≥ narrow** here (wide/do15 0.0439 > narrow/do15 0.0429; wide/do20 0.0442 > narrow/do20 0.0411). This is the **opposite of Musical_Instruments**, where narrow won. Takeaway: the best arch is **category-dependent**; on Industrial the wider FFN + strong dropout (0.20) is best.
- **LR probe**: narrow/do20 at lr3e-4 (I7, 0.0414) ≈ at lr5e-4 (I1, 0.0411) — lr is flat here, confirming 5e-4 is fine.
- **Convergence**: best config unchanged from r1 (wide default, lr 5e-4, **dropout 0.20**), R@10 = 0.0442; r2's best is within noise below it → **Industrial_and_Scientific is CONVERGED.**
- **Final answer**: **R@10 = 0.0442** (ref 0.0422, +0.0020). Config: rqkmeans L3/W256+dedup, 4 layers, d_model 128, **d_ff 1024, heads 6 (default/wide)**, mlp_layers 2, lr 5e-4, **dropout 0.20**, wd 1e-6, bs 256, maxlen 20, 200 epochs.
- **Cross-category lesson so far**: Musical likes narrow arch + dropout 0.10; Industrial likes wide arch + dropout 0.20. Per-category tuning of {arch, dropout} matters; the standard 8-arm r1 sweep correctly surfaced the right winner in both cases (G7 vs G6).
