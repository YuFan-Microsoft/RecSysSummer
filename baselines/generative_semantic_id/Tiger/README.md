# TIGER — Generative Recommendation with Semantic IDs

A small, readable PyTorch reimplementation of **TIGER** (Rajput et al.,
NeurIPS 2023), trained on **Amazon-2023**. Design choices follow the GRID
practitioner's handbook (*"Generative Recommendation with Semantic IDs: A
Practitioner's Handbook"*, Snap, [arXiv:2507.22224](https://arxiv.org/abs/2507.22224)).
Data streams straight from the Hub — there are no local data files to prepare.

> **TL;DR recipe.** RK-Means semantic IDs `(L=3, W=256)` · T5 encoder–decoder ·
> sliding-window augmentation · **0** user tokens · Adam lr `5e-4` / wd `1e-6` ·
> select on validation Recall@10 · report at **beam 50**.

---

## Quickstart

### Install

```bash
pip install -r requirements.txt
```

### Data (from HuggingFace, no download step)

- Items: [`yufan/amazon2023-item-metadata`](https://huggingface.co/datasets/yufan/amazon2023-item-metadata)
- Interactions: [`yufan/amazon2023-user-interactions`](https://huggingface.co/datasets/yufan/amazon2023-user-interactions)
  (5-core, chronological, leave-one-out, with sliding-window augmentation)

Pick a category with `--data.category`:
`Musical_Instruments`, `Industrial_and_Scientific`, `Video_Games`,
`Beauty_and_Personal_Care`, `Books`.

### Pipeline (run in order)

```bash
# 1 — item text → embeddings
python src/embeddings.py \
    --data.category Beauty_and_Personal_Care \
    --data.output outputs/embeddings.pt \
    --model.name sentence-transformers/sentence-t5-base

# 2 — embeddings → semantic IDs
python src/quantize.py \
    --data.embeddings outputs/embeddings.pt \
    --data.output outputs/semantic_ids.pt \
    --method rqkmeans --num_hierarchies 3 --codebook_width 256

# 3 — train TIGER (also evaluates on the test set at the end)
python src/train_tiger.py \
    --data.category Beauty_and_Personal_Care \
    --data.semantic_ids outputs/semantic_ids.pt \
    --ckpt.output outputs/tiger.pt \
    --train.epochs 50 --train.batch_size 256

# 4 (optional) — re-evaluate a saved checkpoint
python src/train_tiger.py --eval_only \
    --data.category Beauty_and_Personal_Care \
    --data.semantic_ids outputs/semantic_ids.pt \
    --ckpt.output outputs/tiger.pt
```

**Multi-GPU.** Step 3 has a DeepSpeed version for one node with several GPUs;
steps 1, 2, 4 are unchanged.

```bash
deepspeed --num_gpus 8 src/train_tiger_ds.py \
    --data.category Beauty_and_Personal_Care \
    --data.semantic_ids outputs/semantic_ids.pt \
    --ckpt.output outputs/tiger.pt \
    --train.epochs 50 --train.micro_batch_size 256
```

### Options

- Use the **same `--data.category`** in steps 1 and 3 (the item index must match).
- `--method` (step 2): `rqkmeans` · `rvq` · `rqvae` (see [Tokenizers](#semantic-id-tokenizers-rk-means--r-vq--rq-vae)).
- `--data.maxlen` (20 or 50) selects history length / HF split. Default 20.
- Metrics: Recall@K, NDCG@K, MRR@K (default K = 5, 10; set with `--eval.ks`).
- **W&B**: logs automatically if a key is found (`--logger.wandb.key` or
  `export WANDB_API_KEY=...`); disable with `--logger.wandb.enable 0`.

---

## How it works

Three stages, then evaluation:

1. **`src/embeddings.py`** — encode each item's text with a Sentence-T5 / Flan-T5
   encoder → `(N, d)` content embeddings.
2. **`src/quantize.py`** — residual-quantize embeddings into **semantic IDs**:
   `L` hierarchies × `W` codebook entries, plus one TIGER append-digit to
   de-duplicate colliding items → `H = L + 1` tokens/item.
3. **`src/train_tiger.py`** (or `_ds.py` for DeepSpeed) — a T5-style
   encoder–decoder autoregressively generates the next item's semantic ID.

**Evaluation** — beam search (constrained or free-form), full ranking over the
catalog, Recall@K / NDCG@K / MRR@K. **Protocol**: train → pick the checkpoint
with the best **validation Recall@10** → evaluate it once on the held-out test
split.

### Why input uses one shared table but output uses per-hierarchy heads

A semantic ID is `H` tokens, each drawn from the same range `0..V-1`, but the
*same* number means different things at different hierarchies. TIGER handles this
asymmetrically:

- **Input — one big embedding table (`H*V + 1` rows).** Just like an LLM token
  table; a per-hierarchy offset `h*V` routes level `h`'s code to its own rows.
  Lookup is "grab a row", so a shared big matrix is fine.
- **Output — `H` separate heads, each `d_model → V`.** Decoding step `h` must
  pick a code *within level `h`'s `V` options*, so the softmax is over `V`, never
  `H*V`. A single combined `H*V` softmax would be meaningless — it would force a
  level-0 code to compete with a level-2 code that isn't even a valid candidate
  at that step. (A single *shared* width-`V` head is also valid; TIGER uses `H`
  per-level heads because each level carries distinct semantics.)

The takeaway: a big shared matrix is fine for *lookup* (input), but the *softmax
normalization set* must be per-hierarchy (output).

---

## Design choices that matter (GRID handbook)

The handbook ablates each component one at a time. Below is *which knobs actually
move the needle* — a checklist for new runs. Gains are dataset-dependent; these
are directional, not numbers to hit.

| Lever | Recommendation | Why it matters |
|-------|----------------|----------------|
| **Sliding-window augmentation** | **Use it — paramount.** Expand each user sequence into **all contiguous sub-sequences**. | The single biggest *free* win; mitigates overfitting & sparsity. |
| **Architecture** | **Encoder–decoder**, not decoder-only. | The encoder's dense attention over full history captures richer patterns. |
| **Tokenizer** | **RK-Means** (≈ R-VQ) over RQ-VAE. | Simpler, faster, at least as good — RQ-VAE needs far more steps and is collapse-prone. |
| **SID dimension** | **L=3, W=256.** | Sweet spot; *more* residual layers can hurt (learnability vs. semantic-info trade-off). |
| **User tokens** | **Drop them (0).** | A larger user-token vocab doesn't improve personalization. |
| **SID de-duplication** | **TIGER append-digit** (or random-pick). | Comparable; random-pick scales better (no global SID stats). |
| **Beam search** | **Free-form is fine** and cheaper. | Comparable quality to constrained, significantly faster. |
| **Semantic encoder size** | **Small is enough.** | Scaling the LLM encoder gives only marginal gains. |
| **Beam size** *(eval-only)* | **Small to select, large to report.** | The dominant lever for Recall@K at test time — pure inference knob. |

**Rules of thumb.** The two biggest *free* wins are **sliding-window
augmentation** and the **enc-dec architecture** (both training-side). Several
"standard" TIGER pieces are **droppable** — user tokens, RQ-VAE, constrained
decoding. And **more capacity ≠ better**: extra SID layers or a bigger encoder
add cost with little gain.

---

## Best configuration

| Component | Setting |
|-----------|---------|
| Tokenizer | RK-Means, L=3, W=256, +1 TIGER dedup digit → **H=4 tokens/item** |
| Content encoder | Sentence-T5 (`sentence-transformers/sentence-t5-base`, fp32) |
| Model | T5 enc-dec, d_model 128, 4+4 layers, 6 heads, d_kv 64, d_ff 1024, dropout 0.10, mlp_layers 2 |
| Optimizer | Adam, lr `5e-4`, weight-decay `1e-6`, batch 256 |
| Epochs | **per-category — see table below** (data-dependent) |
| Model selection | best **validation Recall@10** (beam 10, fast) |
| Final test | **beam 50** (paper standard) |

### Per-category settings (epochs are data-dependent)

Convergence is governed by **gradient steps**, not epochs, so the same epoch
count is wrong across categories: small catalogs need *more* epochs (few
steps/epoch), large catalogs need *far fewer*. Everything else (tokenizer,
encoder, model, lr `5e-4`, wd `1e-6`, dropout 0.10, batch 256, beam 10→50) is
shared. The trainer saves the **best validation Recall@10** checkpoint, so the
epoch value is an upper bound with early-stopping, not a fixed run length.

| Category | #Interactions | ~steps/epoch (bs 256) | **Recommended epochs** |
|---|---:|---:|---:|
| Industrial_and_Scientific | 412,947 | ~1.2K | **200** |
| Musical_Instruments | 511,836 | ~1.6K | **200** |
| Video_Games | 814,586 | ~2.4K | **250** |
| Beauty_and_Personal_Care | 6,624,441 | ~20K | **30** |
| Books | 9,488,297 | ~31K | **20** |

> All five land at roughly **300K–600K total gradient steps** — the regime where
> the paper's small-category TIGER converges (~186–253 epochs on Instrument /
> Scientific / Game). A flat `--train.epochs 50` **under-trains** the three small
> categories (they need ~200) and is mildly generous for Beauty / Books.

---

## Semantic-ID tokenizers: RK-Means / R-VQ / RQ-VAE

All three are **residual quantizers**: assign to the nearest centroid → emit a
code → subtract the chosen centroid → repeat on the residual for `L` levels.

```text
residual = x
for level in range(L):
    residual = normalize(residual)          # RK-Means & R-VQ only
    c = nearest_centroid(residual, codebook[level])
    code[level] = index_of(c)
    residual = residual - c                  # what level+1 must still explain
```

The reconstruction is the sum of chosen centroids $\hat{x} = \sum_l c_l$; the
final residual $x - \hat{x}$ is the reconstruction error. They differ only in
*where* and *how* the codebooks are learned (verified against the GRID reference,
`snap-research/GRID`):

| | **rqkmeans** | **rvq** | **rqvae** |
|---|---|---|---|
| Training granularity | layer-wise | layer-wise | **joint** (all levels) |
| Quantization space | original embedding | original embedding | **encoder's low-dim latent** |
| Codebook update | k-means / Lloyd (exact mean) | **gradient** on quant. loss | gradient on quant. loss |
| Loss terms | quantization | quantization | quantization **+ reconstruction** |
| Encoder / decoder | none | none | **both** |
| GRID module | `MiniBatchKMeans` | `VectorQuantization` | `VectorQuantization` + enc/dec |

Paper ranking: **rqkmeans ≈ rvq > rqvae**, despite RQ-VAE training ~5× longer.

**Why R-VQ has no decoder.** R-VQ quantizes *in the input space*, so its
quantization loss $\sum_l\lVert r_l - c_l\rVert^2$ telescopes to
$\lVert x-\hat{x}\rVert^2$ — the quantization loss **is** the reconstruction
loss. RQ-VAE quantizes in a *learned latent*, so it needs a decoder +
reconstruction loss to train the encoder and guarantee the latent maps back to
`x`. A decoder is only useful **paired with an encoder**; add both to R-VQ and
you have simply rebuilt RQ-VAE.

**R-VQ vs RK-Means — same objective, different optimizer.** Both minimize the
k-means within-cluster sum of squares per level,

$$\min_{C}\ \sum_i \big\lVert r_i - c_{a(i)} \big\rVert^2,\qquad a(i)=\arg\min_k \lVert r_i-c_k\rVert.$$

Setting the R-VQ gradient to zero gives $c_k = \text{mean(assigned residuals)}$ —
exactly the k-means fixed point. So **a RK-Means solution is a stationary point
of the R-VQ objective**; RK-Means just uses a more direct (exact-mean) solver and
tends to reach slightly lower quantization error. In GRID the two are even
closer: `MiniBatchKMeans` (Sculley) carries the comment that its update *"is
equivalent to an SGD step with lr 0.5"* on the same `WeightedSquaredError` loss —
the only residual difference is RK-Means uses a count-weighted **mean** target,
R-VQ a **per-point** gradient.

**GRID's R-VQ ≠ the audio-codec mainstream.** GRID's R-VQ is one specific
variant; it is *not* the EnCodec / SoundStream / `lucidrains` flavor. The core
residual loop is identical across all of them — these are just
codebook-update / normalization choices, and our `rvq` deliberately targets GRID:

| | Mainstream RVQ | GRID R-VQ (= our `rvq`) |
|---|---|---|
| Codebook update | usually **EMA** (or grad + commitment) | gradient on quantization loss |
| Training granularity | usually **joint** | **layer-wise** |
| Residual normalization | usually **none** | **yes** |
| Commitment loss | yes (to train an encoder) | **no** (no encoder) |

**Fidelity of our `rvq`.** Algorithmically matched to GRID: per-level trainable
codebooks, gradient on the quantization loss, layer-wise, normalized residuals,
k-means++ seed, no encoder/decoder, no STE/commitment (STE in GRID is only for
the RQ-VAE encoder's reconstruction path). Remaining differences are
hyperparameter-level — we use **Adam lr 1e-3 + mean** reduction; GRID's
clustering modules default to **SGD lr 0.5 + sum** — i.e. a learning-rate
rescaling.

### Dead codes & empty clusters

A code (or centroid) is **dead** when no point picks it. In `rvq` / `rqvae` we
periodically reset dead codes onto random data points (`_revive_dead_codes`,
every 10 epochs) — the standard **code reset / random restart** trick and the
single most effective anti-collapse measure for VQ-style codebooks. The plain
`kmeans` solver currently leaves an empty cluster's centroid untouched, so a dead
centroid just stays put.

The same revival could be applied inside the k-means Lloyd loop (reset empty
clusters to a random point, or split the largest cluster). This is in fact what
mature k-means implementations (e.g. scikit-learn) already do for empty clusters.
But the payoff differs by regime:

- **Plain k-means** — empty clusters are rare (k ≪ #points, assignments rebuilt
  each pass), so it's a low-impact safety net, not a headline trick.
- **VQ / semantic IDs** — with a wide codebook, high dimension, and residual
  stacking, dead codes are common, so code reset is a **mainstream and necessary**
  technique (VQ-VAE-2, Jukebox, SoundStream, RQ-VAE all use it).

We keep `kmeans` as-is for reproducibility; reviving its empty clusters would
slightly raise codebook utilization (and ease `append_dedup_digit` pressure for
`rqkmeans`) at the cost of changing existing results.

---

## Reference baselines & reproduction reliability

To judge whether our reproduction is trustworthy, we compare **only** against
published results on **byte-identical data**. A number is a valid reference only
if it passes both gates (source:
[`amazon_2023/Matching_Papers_Results_Summary.md`](../../../amazon_2023/Matching_Papers_Results_Summary.md)):

1. **Statistics match** — the paper's `#users / #items / #interactions` equal
   ours for that category (off-by-one tolerated; wildly different → excluded).
2. **Processing matches** — official 5-core → chronological → **leave-one-out**,
   full-ranking evaluation.

Target statistics (after 5-core) our data must equal:

| Category | #Users | #Items | #Interactions |
|---|---:|---:|---:|
| Musical_Instruments | 57,439 | 24,587 | 511,836 |
| Video_Games | 94,762 | 25,612 | 814,586 |
| Industrial_and_Scientific | 50,985 | 25,848 | 412,947 |
| Beauty_and_Personal_Care | 729,576 | 207,649 | 6,624,441 |
| Books | 776,370 | 495,063 | 9,488,297 |

> Each paper re-implements its own baselines, so **compare a method only against
> the baselines inside its own paper / lineage** — never put numbers from
> different papers on one scale.

### Directly-comparable leaderboard

UTGRec / MTGRec / CCFRec / Pctx are exact-match on all three categories *and*
share one baseline implementation (RecBole, maxlen 20, full ranking), so they sit
on a single leaderboard.

**Musical Instruments** — R@5 / R@10 / N@5 / N@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0333 | 0.0523 | 0.0213 | 0.0274 |
| TIGER | 0.0370 | 0.0564 | 0.0244 | 0.0306 |
| LETTER | 0.0372 | 0.0580 | 0.0246 | 0.0313 |
| UTGRec | 0.0398 | 0.0616 | 0.0263 | 0.0334 |
| MTGRec | 0.0413 | 0.0635 | 0.0275 | 0.0346 |
| Pctx | 0.0419 | 0.0655 | 0.0275 | 0.0350 |
| **CCFRec** | **0.0432** | **0.0682** | **0.0281** | **0.0361** |

**Industrial & Scientific** — R@5 / R@10 / N@5 / N@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0259 | 0.0412 | 0.0150 | 0.0199 |
| TIGER | 0.0264 | 0.0422 | 0.0175 | 0.0226 |
| LETTER | 0.0279 | 0.0435 | 0.0182 | 0.0232 |
| UTGRec | 0.0308 | 0.0481 | 0.0204 | 0.0255 |
| Pctx | 0.0323 | 0.0504 | 0.0205 | 0.0263 |
| MTGRec | 0.0322 | 0.0506 | 0.0212 | 0.0271 |
| **CCFRec** | **0.0364** | **0.0555** | **0.0224** | **0.0285** |

**Video Games** — R@5 / R@10 / N@5 / N@10
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| SASRec | 0.0535 | 0.0847 | 0.0331 | 0.0438 |
| TIGER | 0.0559 | 0.0868 | 0.0366 | 0.0467 |
| LETTER | 0.0563 | 0.0877 | 0.0372 | 0.0473 |
| UTGRec | 0.0592 | 0.0909 | 0.0390 | 0.0491 |
| MTGRec | 0.0621 | 0.0956 | 0.0410 | 0.0517 |
| Pctx | 0.0638 | 0.0981 | 0.0416 | 0.0527 |
| **CCFRec** | **0.0658** | **0.1042** | 0.0413 | **0.0536** |

Ranking (Recall@10), consistent across all three:
`CCFRec > Pctx ≈ MTGRec > UTGRec > LETTER > TIGER > SASRec`.

### Other exact-match papers (each vs its own baselines)

Full metrics as each paper reports them; **bold** = the paper's proposed method.

**LARES** (full ranking):
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

**SID-MLP** (distillation; matches its TIGER teacher at ~8.7× throughput, `last_out` split):
| Cat | Method | R@5 | R@10 | N@5 | N@10 |
|---|---|---:|---:|---:|---:|
| Instrument | TIGER (teacher) | 0.0386 | 0.0606 | 0.0252 | 0.0323 |
| Instrument | **SID-MLP** | **0.0396** | **0.0620** | **0.0259** | **0.0332** |
| Scientific | TIGER (teacher) | 0.0295 | 0.0457 | 0.0191 | 0.0243 |
| Scientific | **SID-MLP** | **0.0297** | **0.0472** | **0.0193** | **0.0250** |
| Video Games | TIGER (teacher) | 0.0612 | 0.0951 | 0.0403 | 0.0512 |
| Video Games | **SID-MLP** | 0.0610 | **0.0953** | 0.0402 | 0.0512 |

**GrIT** (maxlen 50 ⇒ higher absolute scores; own non-TIGER baselines):
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

**Token-Weighted** — Musical Instruments (its Scientific is off-by-one item; Hit@K = Recall@K):
| Method | H@5 | H@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| TIGER | 0.0316 | 0.0501 | 0.0203 | 0.0263 |
| TIGER + IGD | 0.0325 | 0.0503 | 0.0210 | 0.0268 |
| **TIGER + Ours** | **0.0330** | **0.0512** | **0.0215** | **0.0273** |

**MARIUS** — the only exact-match + LOO paper on **Beauty**:
| Method | R@5 | R@10 | N@5 | N@10 |
|---|---:|---:|---:|---:|
| TIGER | 0.0098 | 0.0163 | 0.0064 | 0.0084 |
| SASRec++ | 0.0268 | 0.0384 | 0.0188 | **0.0225** |
| **MARIUS** | **0.0271** | **0.0404** | 0.0181 | 0.0224 |

### Reliability of each category

- **Instrument / Scientific / Video Games** — many exact-match references; a
  reproduced TIGER landing in the published range is **well-validated**.
- **Beauty** — exactly **one** exact-match LOO paper (MARIUS); thin anchor.
- **Books** — **no** comparable reference. The one exact-match Books paper uses a
  different protocol (re-rank 20 candidates, HR@1), so it is **not cited**; our
  Books result cannot be externally validated.

---

## Bugs found & fixed

| File | Symptom | Fix |
|------|---------|-----|
| `src/embeddings.py` | `from_pretrained` loaded Sentence-T5 in fp16; apex fused RMSNorm rejects half → `expected scalar type Float but found Half`. | Force `torch_dtype=torch.float32` at load. |
| `src/quantize.py` | RQ-VAE **codebook collapse** — all items map to one code. | Input standardization + **k-means warm-start** + **dead-code revival** (every 10 epochs). |
| `src/quantize.py` | `rvq` was *not* GRID's R-VQ — it was RK-Means with residual normalization disabled (gradient-free). | Rewrote `rvq` to GRID's `VectorQuantization`: per-level **trainable codebooks**, gradient on the quantization loss, layer-wise, normalized residuals, k-means++ seed. |

---

## Citation

Rajput et al., *Recommender Systems with Generative Retrieval*, NeurIPS 2023 —
[arXiv:2305.05065](https://arxiv.org/abs/2305.05065).
Ju et al., *Generative Recommendation with Semantic IDs: A Practitioner's
Handbook*, 2025 — [arXiv:2507.22224](https://arxiv.org/abs/2507.22224).
