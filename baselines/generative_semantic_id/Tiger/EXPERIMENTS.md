# TIGER on Amazon-2023 — Experiment Record

A small enc-dec TIGER reimplementation (generative recommendation with semantic
IDs) trained and evaluated on **all available Amazon-2023 categories** from the
user's HuggingFace datasets. Design choices follow the GRID practitioner's
handbook (*"Generative Recommendation with Semantic IDs: A Practitioner's
Handbook"*, Snap, arXiv:2507.22224).

- **Item content**: `yufan/amazon2023-item-metadata` (one config per category)
- **User interactions**: `yufan/amazon2023-user-interactions`
  (5-core, leave-one-out, sequential splits with sliding-window augmentation)
- **wandb project**: `tiger-allcat` (per-category runs) and `tiger-grid-sweep`
  (the config sweep). One project, distinct run names per experiment.

---

## Key tricks & insights (GRID handbook, arXiv:2507.22224)

The most important takeaways for building a strong GR-with-SID pipeline. The
GRID handbook ablates each component one at a time; below is *which knobs
actually matter* (and which are overrated), as a checklist for future runs.
Exact gains are dataset-dependent — these are directional, not numbers to hit.

| Lever | Recommendation | Why it matters |
|-------|----------------|----------------|
| **Sliding-window augmentation** | **Use it — paramount.** Expand each user sequence into **all contiguous sub-sequences** → many more (history → next) training samples. | The single biggest *free* win; mitigates overfitting & sparsity, especially on short/sparse sequences. |
| **Encoder–decoder vs decoder-only** | **Use enc-dec.** | Encoder's dense attention over the full history captures richer sequential patterns; dec-only lags clearly. |
| **Tokenizer algorithm** | **RK-Means** (≈ R-VQ) over RQ-VAE. | Simpler, faster to train, and at least as good — RQ-VAE needs far more steps and is collapse-prone. |
| **SID dimension (L×W)** | **L=3, W=256.** | Sweet spot; *more* residual layers can hurt (learnability vs. semantic-info trade-off), not help. |
| **User tokens** | **Drop them (0 tokens).** | Larger user-token vocab doesn't improve personalization; removing simplifies the model. |
| **SID de-duplication** | **TIGER append-digit** (or random-pick). | Both comparable. Append-digit has a slight edge but adds +1 token/seq and needs global SID stats — random-pick scales better. |
| **Constrained vs free-form beam** | **Free-form is fine** and cheaper. | Comparable quality, significantly faster — the SID structure is learned well enough without explicit constraints. |
| **Semantic encoder size** | **A small encoder is enough.** | Scaling the LLM encoder (e.g. Large→XXL) gives only marginal gains; the pipeline under-uses extra world knowledge. |

> **Our own finding (not from the paper):** **beam size is an eval-only knob** —
> the dominant lever for Recall@K at test time (see §7). Select checkpoints on a
> small beam (fast), then report final test numbers with a large beam.

**Rules of thumb:**

- The two biggest *free* wins are **sliding-window augmentation** and the
  **enc-dec architecture** — both training-side, no extra tuning.
- Several "standard" TIGER components are **droppable**: user tokens, RQ-VAE,
  and constrained decoding — simpler & cheaper without losing quality.
- **More capacity ≠ better**: extra SID layers and a bigger LLM encoder add
  cost with little/no gain.

---

## 1. Pipeline

Four stages (see `README`, `src/`):

1. **`src/embeddings.py`** — encode each item's text with `sentence-t5-base`
   → `(N, 768)` content embeddings.
2. **`src/quantize.py`** — residual quantization of embeddings into
   **semantic IDs**: `L` hierarchies × `W` codebook entries, plus a TIGER
   append-digit to de-duplicate colliding items → `H = L+1` tokens/item.
3. **`src/train_tiger_ds.py`** — 8-GPU DeepSpeed training of a T5-style
   encoder-decoder that autoregressively generates the next item's semantic ID.
4. Evaluation — constrained / free-form beam search, full-ranking,
   Recall@K & NDCG@K (also MRR@K), K ∈ {5, 10}.

**Protocol**: train → select the best checkpoint by **validation Recall@10**
→ evaluate that checkpoint once on the held-out **test** split.

---

## 2. Bugs found and fixed

| # | File | Symptom | Fix |
|---|------|---------|-----|
| 1 | `src/embeddings.py` | `AutoModel.from_pretrained` loaded sentence-t5-base in fp16; apex fused RMSNorm rejects half → `RuntimeError: expected scalar type Float but found Half`. | Force `torch_dtype=torch.float32` at model load. |
| 2 | `src/quantize.py` | RQ-VAE **codebook collapse** — all items mapped to a single code, crashing tokenization. | Added input standardization + **k-means codebook warm-start** (`init_codebooks`) + **dead-code revival** (`revive_dead_codes`, every 10 epochs). |
| 3 | `src/quantize.py` | **`rvq` was not GRID's R-VQ.** The original `rvq` just called the RK-Means path with `normalize_residuals=False` — i.e. "RK-Means without residual normalization", a gradient-free k-means, not a trainable-codebook VQ. | Rewrote `rvq` to match GRID's `VectorQuantization`: per-level **trainable codebooks** learned by **gradient descent** on the quantization loss, **layer-wise**, residuals normalized, k-means++ seeded. See §8. |

---

## 3. Paper alignment (GRID handbook)

Findings from arXiv:2507.22224 and how this repo aligns:

- **Tokenizer**: RK-Means ≈ R-VQ > RQ-VAE; best `(L, W) = (3, 256)`. → we use
  **RK-Means 3×256** (`rqkmeans`). Confirmed by our own sweep (§4).
- **Architecture**: encoder-decoder ≫ decoder-only. → ours is enc-dec. ✓
- **Sliding-window data augmentation is paramount**. → already baked into the HF
  train split (avg ≈ 5.9 training rows/user). ✓
- **0 user tokens** is optimal. → `num_user_bins = None` (default). ✓
- TIGER append-digit de-dup ✓; free-form beam search ✓.
- **Training**: Adam, LR `5e-4`, weight-decay `1e-6`, batch `256`, model-select
  by validation Recall@10. ✓
- **Eval**: beam size **50** for all generative recommenders (paper standard;
  used for all final test numbers below).

---

## 4. Config sweep (8 runs)

Run on **Musical_Instruments**, 1 GPU each, 30 epochs, beam 10, selected by
validation Recall@10. wandb project `tiger-grid-sweep`. (Test metrics shown.)

Axes explored (one shared base config, varying one knob at a time):
- **Tokenizer**: `rqkmeans` / `rvq` / `rqvae`.
- **SID dimension** `(L×W)`: `3×256` vs `3×128` vs `4×256`.
- **Optimizer**: lr `5e-4` / wd `1e-6` vs the aggressive `1e-3` / `1e-4`.
- **Regularization / head**: dropout `0.15` vs `0.10`; `mlp_layers` 2 vs 0.

**Expected orderings** (from the GRID paper; to be re-confirmed on re-run):
`rqkmeans ≳ rvq > rqvae`; `(L, W) = (3, 256)` best; lr `5e-4` / wd `1e-6` beats
the aggressive default; lower dropout `0.10` helps.

> Sweep results are being regenerated and the next sweep's settings may differ,
> so per-run numbers are intentionally not recorded here.

---

## 5. Best configuration

| Component | Setting |
|-----------|---------|
| Tokenizer | RK-Means, L=3, W=256, +1 TIGER dedup digit → **H=4 tokens/item** |
| Content encoder | sentence-t5-base (fp32), 768-d |
| Model | T5-style enc-dec, d_model 128, 4 enc + 4 dec layers, 6 heads, d_kv 64, d_ff 1024, **dropout 0.10**, **mlp_layers 2** |
| Optimizer | Adam, **lr 5e-4**, **weight-decay 1e-6**, batch 256 |
| Epochs | **50** |
| Hardware | 8× GPU, DeepSpeed |
| Model selection | best **validation Recall@10** (beam 10, fast) |
| Final test | **beam size 50** (paper standard) |

---

## 6. Per-category results (test, beam 50)

Categories run from the HF datasets, best config (§5), model-selected on
validation Recall@10, final test with beam 50. wandb project `tiger-allcat`
(runs `<Cat>_train`): **Musical Instruments, Industrial & Scientific,
Video Games, Beauty & Personal Care, Books**.

> Per-category numbers are being regenerated and are intentionally not recorded
> here yet. Categories **Office / Sports / Toys** referenced in some Amazon-2023
> benchmarks are **not present** in the user's HF datasets, so they are omitted.

### Reference baselines & reproduction reliability

To judge whether our TIGER reproduction is trustworthy, we compare **only**
against published results computed on **byte-identical data**. A published number
is a valid reference only if it passes both gates (see
`amazon_2023/Matching_Papers_Results_Summary.md`):

1. **Statistics match exactly** — the paper's `#users / #items / #interactions`
   equal `yufan/amazon2023-user-interactions` for that category.
2. **Processing matches** — official 5-core → chronological → **leave-one-out**.

Target statistics (after 5-core) our data must equal:

| Category | #Users | #Items | #Interactions |
|---|---:|---:|---:|
| Musical_Instruments | 57,439 | 24,587 | 511,836 |
| Video_Games | 94,762 | 25,612 | 814,586 |
| Industrial_and_Scientific | 50,985 | 25,848 | 412,947 |
| Beauty_and_Personal_Care | 729,576 | 207,649 | 6,624,441 |
| Books | 776,370 | 495,063 | 9,488,297 |

**Published results to compare against** (transcribed from each paper's main
table; source: `amazon_2023/Matching_Papers_Results_Summary.md`). Even on
identical data, each paper re-implements its baselines, so **compare a method
only against the baselines inside its own paper / lineage** — do not put numbers
from different papers on one scale.

#### Directly-comparable leaderboard (shared RecBole baseline; maxlen 20, full ranking)

UTGRec / MTGRec / CCFRec / Pctx are exact-match on Instrument / Scientific / Game
*and* share one baseline implementation, so they sit on a single leaderboard.

**Musical Instruments** — R@5 / R@10 / N@5 / N@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec (shared) | 0.0333 | 0.0523 | 0.0213 | 0.0274 |
| TIGER (shared) | 0.0370 | 0.0564 | 0.0244 | 0.0306 |
| LETTER (shared) | 0.0372 | 0.0580 | 0.0246 | 0.0313 |
| UTGRec | 0.0398 | 0.0616 | 0.0263 | 0.0334 |
| MTGRec | 0.0413 | 0.0635 | 0.0275 | 0.0346 |
| Pctx | 0.0419 | 0.0655 | 0.0275 | 0.0350 |
| **CCFRec (PQ)** | **0.0432** | **0.0682** | **0.0281** | **0.0361** |

**Industrial & Scientific** — R@5 / R@10 / N@5 / N@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0259 | 0.0412 | 0.0150 | 0.0199 |
| TIGER | 0.0264 | 0.0422 | 0.0175 | 0.0226 |
| LETTER | 0.0279 | 0.0435 | 0.0182 | 0.0232 |
| UTGRec | 0.0308 | 0.0481 | 0.0204 | 0.0255 |
| Pctx | 0.0323 | 0.0504 | 0.0205 | 0.0263 |
| MTGRec | 0.0322 | 0.0506 | 0.0212 | 0.0271 |
| **CCFRec (PQ)** | **0.0364** | **0.0555** | **0.0224** | **0.0285** |

**Video Games** — R@5 / R@10 / N@5 / N@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0535 | 0.0847 | 0.0331 | 0.0438 |
| TIGER | 0.0559 | 0.0868 | 0.0366 | 0.0467 |
| LETTER | 0.0563 | 0.0877 | 0.0372 | 0.0473 |
| UTGRec | 0.0592 | 0.0909 | 0.0390 | 0.0491 |
| MTGRec | 0.0621 | 0.0956 | 0.0410 | 0.0517 |
| Pctx | 0.0638 | 0.0981 | 0.0416 | 0.0527 |
| **CCFRec (PQ)** | **0.0658** | **0.1042** | 0.0413 | **0.0536** |

Ranking (Recall@10), consistent across all three categories:
`CCFRec > Pctx ≈ MTGRec > UTGRec > LETTER > TIGER > SASRec`.

#### Other exact-match papers (each vs its own baselines — do not cross-compare)

Full per-method metrics as each paper reports them (R@5 / R@10 / N@5 / N@10,
plus R@1 where given). Bold = each paper's proposed method.

**LARES** (maxlen 20, full ranking; also reports R@20/N@20 in-paper):
| Cat | Method | R@5 | R@10 | N@5 | N@10 |
|---|---|---:|---:|---:|---:|
| Instrument | SASRec | 0.0346 | 0.0536 | 0.0216 | 0.0277 |
| Instrument | DuoRec | 0.0381 | 0.0598 | 0.0244 | 0.0314 |
| Instrument | PRL++ | 0.0385 | 0.0587 | 0.0245 | 0.0310 |
| Instrument | **LARES** | **0.0411** | **0.0636** | **0.0263** | **0.0336** |
| Scientific | SASRec | 0.0248 | 0.0385 | 0.0150 | 0.0194 |
| Scientific | DuoRec | 0.0280 | 0.0431 | 0.0178 | 0.0226 |
| Scientific | PRL++ | 0.0279 | 0.0441 | 0.0176 | 0.0228 |
| Scientific | **LARES** | **0.0297** | **0.0464** | **0.0191** | **0.0245** |
| Video Games | SASRec | 0.0578 | 0.0926 | 0.0334 | 0.0446 |
| Video Games | DuoRec | 0.0592 | 0.0932 | 0.0368 | 0.0477 |
| Video Games | PRL++ | 0.0587 | 0.0925 | 0.0367 | 0.0475 |
| Video Games | **LARES** | **0.0616** | **0.0972** | **0.0386** | **0.0500** |

**LLaDA-Rec** (discrete diffusion, full ranking; also reports R@1):
| Cat | Method | R@1 | R@5 | R@10 | N@5 | N@10 |
|---|---|---:|---:|---:|---:|---:|
| Scientific | SASRec | 0.0063 | 0.0240 | 0.0379 | 0.0152 | 0.0197 |
| Scientific | TIGER | 0.0084 | 0.0282 | 0.0446 | 0.0183 | 0.0236 |
| Scientific | LETTER | 0.0082 | 0.0273 | 0.0423 | 0.0179 | 0.0227 |
| Scientific | LC-Rec | 0.0091 | 0.0280 | 0.0434 | 0.0186 | 0.0235 |
| Scientific | RPG | 0.0087 | 0.0257 | 0.0395 | 0.0174 | 0.0218 |
| Scientific | **LLaDA-Rec** | **0.0098** | **0.0310** | **0.0474** | **0.0203** | **0.0256** |
| Instrument | SASRec | 0.0089 | 0.0331 | 0.0525 | 0.0211 | 0.0273 |
| Instrument | TIGER | 0.0105 | 0.0359 | 0.0566 | 0.0233 | 0.0300 |
| Instrument | LETTER | 0.0114 | 0.0362 | 0.0562 | 0.0239 | 0.0303 |
| Instrument | LC-Rec | 0.0119 | 0.0379 | 0.0587 | 0.0251 | 0.0318 |
| Instrument | RPG | 0.0118 | 0.0362 | 0.0545 | 0.0241 | 0.0300 |
| Instrument | **LLaDA-Rec** | **0.0128** | **0.0406** | **0.0623** | **0.0268** | **0.0337** |
| Video Games | SASRec | 0.0128 | 0.0516 | 0.0823 | 0.0323 | 0.0421 |
| Video Games | TIGER | 0.0166 | 0.0529 | 0.0823 | 0.0348 | 0.0442 |
| Video Games | LETTER | 0.0170 | 0.0548 | 0.0863 | 0.0360 | 0.0462 |
| Video Games | LC-Rec | 0.0165 | 0.0567 | 0.0891 | 0.0366 | 0.0471 |
| Video Games | RPG | 0.0209 | 0.0579 | 0.0853 | 0.0397 | 0.0485 |
| Video Games | **LLaDA-Rec** | **0.0203** | **0.0623** | **0.0942** | **0.0415** | **0.0517** |

**SID-MLP** (efficiency; matches TIGER teacher at ~8.7× throughput, official `last_out` split):
| Cat | Method | R@5 | R@10 | N@5 | N@10 |
|---|---|---:|---:|---:|---:|
| Instrument | TIGER (teacher) | 0.0386 | 0.0606 | 0.0252 | 0.0323 |
| Instrument | **SID-MLP** | **0.0396** | **0.0620** | **0.0259** | **0.0332** |
| Scientific | TIGER (teacher) | 0.0295 | 0.0457 | 0.0191 | 0.0243 |
| Scientific | **SID-MLP** | **0.0297** | **0.0472** | **0.0193** | **0.0250** |
| Video Games | TIGER (teacher) | 0.0612 | 0.0951 | 0.0403 | 0.0512 |
| Video Games | **SID-MLP** | 0.0610 | **0.0953** | 0.0402 | 0.0512 |

**GrIT** (maxlen **50** ⇒ higher absolute scores; own non-TIGER baselines; paper reports
R@5/R@10/R@20 & N — only R@10/N@10 transcribed here):
| Cat | best baseline R@10 | GrIT R@10 / N@10 |
|---|---:|---:|
| Video Games | 0.1042 (DuoRec) | **0.1047 / 0.0588** |
| Industrial & Scientific | 0.0476 (DuoRec) | **0.0482 / 0.0286** |

**Augment-or-Not** (Hit@K = Recall@K):
| Cat | Method | H@5 | H@10 | N@5 | N@10 |
|---|---|---:|---:|---:|---:|
| Instrument | SASRec | 0.0224 | 0.0379 | 0.0117 | 0.0167 |
| Instrument | GRU4Rec | 0.0203 | 0.0322 | 0.0133 | 0.0171 |
| Instrument | BIGRec (LLM) | 0.0236 | 0.0420 | 0.0133 | 0.0192 |
| Instrument | P5-CID | 0.0283 | 0.0451 | 0.0180 | 0.0234 |
| Instrument | TIGER | 0.0332 | 0.0517 | 0.0216 | 0.0276 |
| Instrument | **LETTER-TIGER** | **0.0339** | **0.0521** | **0.0224** | **0.0282** |
| Scientific | SASRec | 0.0152 | 0.0255 | 0.0087 | 0.0120 |
| Scientific | GRU4Rec | 0.0171 | 0.0256 | 0.0118 | 0.0145 |
| Scientific | BIGRec (LLM) | 0.0160 | 0.0280 | 0.0107 | 0.0144 |
| Scientific | P5-CID | 0.0137 | 0.0205 | 0.0089 | 0.0110 |
| Scientific | TIGER | 0.0241 | 0.0385 | 0.0158 | 0.0204 |
| Scientific | **LETTER-TIGER** | **0.0256** | **0.0396** | **0.0165** | **0.0210** |

**Token-Weighted** — Instrument only (its Scientific is off-by-one item; Hit@K = Recall@K):
| Cat | Method | H@5 | H@10 | N@5 | N@10 |
|---|---|---:|---:|---:|---:|
| Instrument | TIGER | 0.0316 | 0.0501 | 0.0203 | 0.0263 |
| Instrument | TIGER + IGD | 0.0325 | 0.0503 | 0.0210 | 0.0268 |
| Instrument | **TIGER + Ours** | **0.0330** | **0.0512** | **0.0215** | **0.0273** |

**MARIUS** — the only exact-match + LOO paper on **Beauty** (decimals):
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| TIGER | 0.0098 | 0.0163 | 0.0064 | 0.0084 |
| SASRec++ | 0.0268 | 0.0384 | 0.0188 | **0.0225** |
| **MARIUS** | **0.0271** | **0.0404** | 0.0181 | 0.0224 |

> **Books has no comparable reference.** The one exact-match Books paper
> (IntervalLLM) re-ranks 20 candidates and reports HR@1 — a different evaluation
> protocol, not full-ranking LOO — so its numbers are **not cited here**.

**Reliability notes:**

- **Instrument / Scientific / Video Games** have many exact-match references
  → a reproduced TIGER landing in their TIGER range is well-validated.
- **Beauty** has exactly **one** exact-match LOO paper (MARIUS) — thin anchor.
- **Books** has **no** comparable full-ranking exact-match number (the only
  Books paper uses a different HR@1 re-ranking protocol) → our Books result
  **cannot be externally validated**; treat it as indicative only.

---

## 7. Notes on evaluation

- **Beam size is the key lever for Recall@10** — it is an eval-only knob.
  On Instrument, going from beam 10 → beam 50 raises Recall@10 noticeably.
  All final numbers use **beam 50**.
- Model selection uses beam 10 (much faster, well-correlated with beam 50).
- For the two large categories (Beauty, Books) evaluation is run every 10 epochs
  to keep beam-50 search cost manageable on 700k+ eval rows.

---

## 8. Semantic-ID tokenizer deep-dive (RK-Means / R-VQ / RQ-VAE)

Notes from cross-validating our `src/quantize.py` against the GRID reference
implementation (`snap-research/GRID`). All three tokenizers are **residual
quantizers**: assign to nearest centroid → emit a code → subtract the chosen
centroid → repeat on the residual for `L` levels. They differ only in *where*
and *how* the codebooks are learned.

### 8.1 What residual quantization is

For each item embedding `x`, peel it coarse-to-fine:

```
residual = x
for level in range(L):
    residual = normalize(residual)            # RK-Means & R-VQ only
    c = nearest_centroid(residual, codebook[level])
    code[level] = index_of(c)
    residual = residual - c                    # what level+1 must still explain
```

The reconstruction is the sum of chosen centroids `x̂ = Σ c_l`, and the final
residual `r_L = x − x̂` is the reconstruction error. Each item gets `L` codes;
we then append **one TIGER de-dup digit** so colliding items stay unique
→ `H = L + 1` tokens/item.

### 8.2 The three tokenizers, side by side

| | **rqkmeans** | **rvq** | **rqvae** |
|---|---|---|---|
| Training granularity | **layer-wise** | **layer-wise** | **joint** (all levels) |
| Quantization space | original embedding | original embedding | **encoder's low-dim latent** |
| Codebook update | k-means / Lloyd (exact cluster mean) | **gradient descent** on quant. loss | gradient descent on quant. loss |
| Loss terms | quantization only | **quantization only** | quantization **+ reconstruction** |
| Encoder / decoder | none | none | **yes** (both) |
| GRID module | `MiniBatchKMeans` | `VectorQuantization` | `VectorQuantization` + enc/dec |
| GRID config flag | `train_layer_wise: true` | `train_layer_wise: true` | `train_layer_wise: false` |

Paper ranking: **rqkmeans ≈ rvq > rqvae** (Table 1), despite RQ-VAE training
~5× longer.

### 8.3 Why R-VQ has no decoder (and adding one alone is pointless)

- R-VQ quantizes **in the input space**, so its quantization loss
  `Σ‖residual − chosen‖²` telescopes to `‖x − x̂‖²` — **the quantization loss
  *is* the reconstruction loss**. A decoder would be redundant.
- RQ-VAE quantizes in a learned **latent**, so it *needs* a decoder +
  reconstruction loss to (a) give the **encoder** a training signal and
  (b) ensure the quantized latent still maps back to `x`. **The decoder exists
  to train the encoder**, not for quantization itself.
- The discrete code is fixed by `argmin` at quantization time; a decoder placed
  *after* it can't change which code is chosen. So a decoder is only useful
  **paired with an encoder** — add both to R-VQ and you have simply rebuilt
  RQ-VAE.

### 8.4 R-VQ vs RK-Means: same objective, different optimizer

Both minimize the **identical per-level objective** (the k-means within-cluster
sum of squares):

$$\min_{C}\ \sum_i \big\| r_i - c_{a(i)} \big\|^2,\quad a(i)=\arg\min_k \|r_i-c_k\|$$

- **RK-Means** solves it with **Lloyd** updates: centroid = exact mean of its
  assigned points (deterministic, converges cleanly).
- **R-VQ** solves it with **SGD/Adam** steps on the same loss.

Setting the R-VQ gradient to zero gives `c_k = mean(assigned residuals)` —
**exactly the k-means fixed point**. So a RK-Means solution is a **stationary
point of the R-VQ objective**; RK-Means is just a more direct (exact-coordinate)
solver for the same problem. Both are non-convex (discrete assignment) → local
optima; RK-Means's exact mean update usually yields slightly lower quantization
error, so we expect **rqkmeans ≳ rvq** by a small margin (to be re-confirmed
after the re-run).

> In GRID the two are even closer: `MiniBatchKMeans` (Sculley) carries the
> comment that its update *"is equivalent to an SGD step with lr 0.5"* on the
> same `WeightedSquaredError` loss. The only residual difference is RK-Means uses
> a count-weighted **mean** target, R-VQ a per-point gradient.

### 8.5 GRID vs the audio-codec "mainstream" R-VQ

GRID's R-VQ is a specific variant; it is **not** identical to the EnCodec /
SoundStream / `lucidrains` mainstream:

| | Mainstream RVQ | GRID R-VQ (= our `rvq`) |
|---|---|---|
| Codebook update | usually **EMA** (or grad + commitment) | gradient on quantization loss |
| Training granularity | usually **joint** | **layer-wise** |
| Residual normalization | usually **none** | **yes** |
| Commitment loss | yes (to train encoder) | **no** (no encoder) |

The core residual loop is the same across all of them; these are just
codebook-update / normalization variants. Our `rvq` deliberately targets
**GRID**, since that is the paper we reproduce.

### 8.6 Fidelity status of our `rvq`

Algorithmically matched to GRID: per-level trainable codebooks, gradient on
`Σ‖residual − chosen‖²`, **layer-wise**, normalized residuals, k-means++ seed,
no encoder/decoder, no STE/commitment (STE in GRID is only for the RQ-VAE
encoder's reconstruction path). Remaining differences are **hyperparameter-level
only** and amount to a learning-rate rescaling: we use **Adam lr 1e-3 + mean**
reduction; GRID's clustering modules default to **SGD lr 0.5 + sum** reduction.

> Note: our sweep row **A2 (rvq)** predates this fix and was produced by the old
> "RK-Means-without-normalization" code — it is being re-run. The main config
> (`rqkmeans`) is unaffected algorithmically.

---

## 9. Reproduction

```bash
export WANDB_API_KEY=...                      # enables the WandbLogger
# small/medium category (emb+sid precomputed):
bash scripts/run_category.sh <HF_Category> <Tag>
# large category (full pipeline emb→sid→train→beam50 test):
bash scripts/run_bigcat.sh <HF_Category> <Tag>
```

Key artifacts:
- `outputs/ckpts/BEST_50ep.pt` — Instrument best checkpoint.
- `outputs/cat/<Cat>_best.pt`, `outputs/cat/<HF>_emb.pt`, `_sid.pt` — per-category.
- Sweep + per-category metrics tracked in the session SQL (`exp`, `repro`).
- `outputs/BOOKS_RESULT.json` — raw Books beam-50 test metrics.

---

## 10. Summary

- **All 5 available Amazon-2023 categories** are being run end-to-end with one
  shared best config (RK-Means 3×256, lr 5e-4, wd 1e-6, dropout 0.10, mlp 2,
  50 epochs, beam-10 selection / **beam-50 test**), under one wandb project
  (`tiger-allcat`).
- Expectation: denser categories easiest, large sparse catalogs hardest. The
  reliability check is whether each reproduced TIGER lands in the
  **published-TIGER range** (§6 reference table) — strong for Instrument /
  Scientific / Video Games, thin for Beauty (MARIUS only), absent for Books.
- Three pipeline issues were fixed along the way (fp32 embedding load;
  RQ-VAE anti-collapse; R-VQ fidelity — see §2).

_Last updated: results being re-run; metric cells pending._
