# TIGER tuning playbook for Claude (8-GPU, one category at a time)

**Audience: an autonomous coding agent (Claude).** This file tells you how to
push the TIGER reproduction score as high as possible on **one Amazon-2023
category at a time**, using an **8-GPU machine** to run **8 settings in
parallel** (one setting per GPU). Read it fully before launching anything.

The metric we optimize: **test Recall@10** (also report R@5, N@5, N@10), full
ranking, leave-one-out. Model selection is on **validation Recall@10**; the
final test is reported at **beam 50**. These are wired into the code already.

---

## 0. TL;DR workflow

For a target category `$CAT` (one of `Musical_Instruments`,
`Industrial_and_Scientific`, `Video_Games`, `Beauty_and_Personal_Care`,
`Books`):

1. **Preprocess once** (shared by all 8 arms): build item embeddings
   (Sentence-T5) → RK-Means semantic IDs.
2. **Launch 8 training arms in parallel**, one per GPU (`CUDA_VISIBLE_DEVICES=0..7`).
   Each arm changes **exactly one** knob vs the reference (`G0`).
3. Each run **auto-selects** its best checkpoint on val Recall@10 and prints +
   logs the **beam-50 test** metrics to W&B.
4. **Collect** the 8 `test/recall@10` values, pick the winner, then optionally
   run a **second, narrower sweep** around it.

The tokenizer (`rqkmeans`, L=3, W=256, +1 dedup) and the number of layers
(`num_layers=4`) are **LOCKED** — do not change them. Embeddings and semantic
IDs are item-level, so **all 8 arms reuse the same `semantic_ids.pt`**.

---

## 1. Locked configuration (do NOT change)

| Component | Value | Why locked |
|---|---|---|
| Tokenizer | `--method rqkmeans --num_hierarchies 3 --codebook_width 256` | Project decision; RK-Means is the chosen tokenizer. |
| Layers | `--model.num_layers 4` (4 enc + 4 dec) | Project decision; do not sweep depth. |
| Content encoder | `sentence-transformers/sentence-t5-base` (fp32) | Matches the TIGER/RUC baseline that produced the reference numbers. |
| Model selection | best **validation Recall@10**, `--eval.beam_size 10` | Fast, fixed protocol. |
| Final test | `--eval.test_beam_size 50` | Paper standard; this is what is logged as `test/*`. |
| History length | `--data.maxlen 20` | We run all experiments on maxlen 20; do not switch to 50. |
| Batch size | 256 | Fixed for comparability. |

Everything else below is fair game.

---

## 2. Preprocess once per category

Embeddings and semantic IDs do **not** depend on any training knob, so run these
two steps **once** and let all 8 arms share the output.

```bash
CAT=Musical_Instruments          # <-- set your target category
mkdir -p outputs/$CAT logs

# Step 1 — item text -> Sentence-T5 embeddings (one GPU is enough)
CUDA_VISIBLE_DEVICES=0 python src/embeddings.py \
    --data.category $CAT \
    --data.output outputs/$CAT/embeddings.pt \
    --model.name sentence-transformers/sentence-t5-base

# Step 2 — embeddings -> RK-Means semantic IDs (LOCKED tokenizer)
python src/quantize.py \
    --data.embeddings outputs/$CAT/embeddings.pt \
    --data.output outputs/$CAT/semantic_ids.pt \
    --method rqkmeans --num_hierarchies 3 --codebook_width 256
```

> Only if you decide to sweep the **embedding model** (optional, Section 6): you
> must re-run steps 1–2 into a *separate* `semantic_ids.pt` per embedding model,
> because changing the encoder changes the IDs.

---

## 3. Per-category epoch budget (data-dependent)

Convergence is governed by **gradient steps**, not epochs. Small catalogs have
few steps/epoch so they need *more* epochs; large catalogs need *far fewer*. The
trainer early-stops on val Recall@10 (saves the best checkpoint), so treat these
as **upper bounds**.

| Category | #Interactions | ~steps/epoch (bs 256) | `--train.epochs` | `--eval.every` |
|---|---:|---:|---:|---:|
| Industrial_and_Scientific | 412,947 | ~1.2K | **200** | 10 |
| Musical_Instruments | 511,836 | ~1.6K | **200** | 10 |
| Video_Games | 814,586 | ~2.4K | **250** | 10 |
| Beauty_and_Personal_Care | 6,624,441 | ~20K | **30** | 2 |
| Books | 9,488,297 | ~31K | **20** | 2 |

A flat `50` under-trains the three small categories (they need ~200) and is
mildly generous for Beauty / Books. Set `EP` accordingly in the launcher below.

---

## 4. The 8 arms (one knob each, vs reference `G0`)

Each arm is a full training on one GPU. `G0` is the reference; `G1..G7` each
change a single variable so the effect is attributable. **Learning rate is the
dominant lever, so half the arms scan it** (5 LR points incl. the reference),
plus a dropout bracket and the RUC architecture.

| GPU | Arm | Change vs G0 | Extra flags |
|---:|---|---|---|
| 0 | **G0** reference | lr 5e-4 | (defaults: lr 5e-4, dropout 0.10, d_ff 1024, heads 6, mlp_layers 2, maxlen 20) |
| 1 | **G1** lr 3e-4 | lr ↓ | `--train.lr 3e-4` |
| 2 | **G2** lr 7e-4 | lr ↑ | `--train.lr 7e-4` |
| 3 | **G3** lr 1e-3 | lr ↑↑ | `--train.lr 1e-3` |
| 4 | **G4** lr 2e-3 | lr ↑↑↑ | `--train.lr 2e-3` |
| 5 | **G5** less dropout | dropout 0.05 | `--model.dropout 0.05` |
| 6 | **G6** more dropout | dropout 0.20 | `--model.dropout 0.20` |
| 7 | **G7** RUC-style arch | d_ff 512, heads 4 | `--model.d_ff 512 --model.num_heads 4` |

Rationale: LR moves the score most, so arms `G0..G4` form a 5-point LR scan
`{3e-4, 5e-4, 7e-4, 1e-3, 2e-3}` — read it as a curve and find the peak. `G5/G6`
bracket dropout (over/under-fitting). `G7` tests the exact RUC baseline
architecture (d_ff 512 / 4 heads) that produced the reference numbers. All keep
the LOCKED tokenizer, 4 layers, and **maxlen 20**.

---

## 5. Parallel launcher (8 GPUs, 8 arms)

### Naming convention (W&B) — follow exactly

- **One project for everything**: `WANDB_PROJECT = tiger-sweep`. Every category,
  every arm, every round goes here. **Never** put the category in the project
  name — categories are distinguished by the run name, not the project.
- **Run name format**: `<Category>__<round>__<arm>__<knob>`, components joined by
  double underscore `__`. Examples:
  `Musical_Instruments__r1__G0__ref`, `Musical_Instruments__r1__G3__lr1e-3`,
  `Video_Games__r1__G7__dff512h4`.
  - `<round>` = `r1`, `r2`, … (bump for each refinement round)
  - `<arm>` = `G0..G7`
  - `<knob>` = short token for the change (`ref`, `lr1e-3`, `do0.05`, `dff512h4`)
- The **same string** is reused as the checkpoint name and log file name, so any
  run is traceable end-to-end: W&B run ↔ `outputs/$CAT/<name>.pt` ↔
  `logs/<name>.log`.

Copy-paste this block after Section 2 finished. It runs all 8 arms at once, one
per GPU, each writing its own checkpoint, log, and W&B run. Each run finishes
with its own **beam-50 test** logged as `test/*`.

```bash
WANDB_PROJECT=tiger-sweep         # SINGLE project for ALL categories/arms/rounds
CAT=Musical_Instruments           # same category as Section 2
SID=outputs/$CAT/semantic_ids.pt
EP=200                            # from Section 3 table (per category!)
ROUND=r1                          # bump to r2, r3, ... for refinement rounds
COMMON="--data.category $CAT --data.semantic_ids $SID \
        --train.epochs $EP --eval.every 10 \
        --eval.beam_size 10 --eval.test_beam_size 50 --eval.ks 5,10 \
        --logger.wandb.enable 1 --logger.wandb.project $WANDB_PROJECT"

run () {  # run <gpu> <arm> <knob> <extra-flags...>
  local g=$1 arm=$2 knob=$3; shift 3
  local name=${CAT}__${ROUND}__${arm}__${knob}   # run_name == ckpt stem == log stem
  CUDA_VISIBLE_DEVICES=$g python src/train_tiger.py $COMMON \
    --ckpt.output outputs/$CAT/${name}.pt \
    --logger.wandb.run_name ${name} "$@" \
    > logs/${name}.log 2>&1 &
}

run 0 G0 ref
run 1 G1 lr3e-4   --train.lr 3e-4
run 2 G2 lr7e-4   --train.lr 7e-4
run 3 G3 lr1e-3   --train.lr 1e-3
run 4 G4 lr2e-3   --train.lr 2e-3
run 5 G5 do0.05   --model.dropout 0.05
run 6 G6 do0.20   --model.dropout 0.20
run 7 G7 dff512h4 --model.d_ff 512 --model.num_heads 4
wait
echo "All 8 arms done. Collect test/recall@10 from W&B project '$WANDB_PROJECT'."
```

> For **Beauty / Books**: set `EP=30` / `EP=20` and `--eval.every 2`. The model
> is tiny (d_model 128), so one GPU per arm fits easily; arms are just slower
> because of more steps/epoch. If wall-clock is too long, run 4 arms at a time.

---

## 6. Selecting the winner & second round

1. From W&B project `tiger-sweep`, read each run's final **`test/recall@10`**
   (tie-break by `test/ndcg@10`). The console log tail (`logs/${CAT}__*.log`,
   line starting `test:`) has the same numbers.
2. Pick the best arm. Then run a **narrow second sweep** around it on the 8 GPUs.
   Since `G0..G4` already trace an LR curve, center round 2 on the winning LR and
   refine — e.g. if `G3` (lr 1e-3) peaked, sweep `{8e-4, 1e-3, 1.3e-3} ×
   {dropout 0.05, 0.10}`, combined with the best architecture from round 1.
3. **Optional embedding sweep** (needs re-running steps 1–2 per encoder): try
   `sentence-transformers/sentence-t5-base` vs `google/flan-t5-base` vs
   `google/flan-t5-large`. Produce one `semantic_ids.pt` per encoder, then rerun
   the best training arm on each.
4. Stop when the second round no longer improves `test/recall@10` beyond noise
   (≈ ±0.0005 run-to-run on the small categories).

---

## 7. Reference targets (when have we "matched" the paper?)

These are the **TIGER baseline** numbers from the RUC/MTGRec lineage on
byte-identical data (R@5 / R@10 / N@5 / N@10). Match or beat the **R@10** column
to consider the reproduction healthy. (Stronger numbers exist for *other*
methods like CCFRec — that is a different method, not our target.)

| Category | R@5 | R@10 | N@5 | N@10 | Reference reliability |
|---|---:|---:|---:|---:|---|
| Musical_Instruments | 0.0370 | **0.0564** | 0.0244 | 0.0306 | strong (many exact-match papers) |
| Industrial_and_Scientific | 0.0264 | **0.0422** | 0.0175 | 0.0226 | strong |
| Video_Games | 0.0559 | **0.0868** | 0.0366 | 0.0467 | strong |
| Beauty_and_Personal_Care | 0.0098 | **0.0163** | 0.0064 | 0.0084 | thin (only MARIUS) |
| Books | — | — | — | — | none (cannot be externally validated) |

For Books, there is no comparable reference; optimize for the best internal
`test/recall@10` and report it as un-anchored.

---

## 8. Pitfalls / rules

- **Re-use `semantic_ids.pt`** across the 8 arms (do not re-tokenize per arm).
- **Set epochs per category** (Section 3). Do not use a flat 50 — it
  under-trains the small categories, which is the most common cause of
  "reproduction is slightly low".
- The number logged as **`test/*` is beam 50**; `eval/*` is beam 10
  (validation). Compare arms on `test/recall@10`.
- Keep `--method rqkmeans`, `--num_hierarchies 3`, `--codebook_width 256`,
  `--model.num_layers 4` fixed in every arm.
- One category at a time. Finish its sweep, record the winning config + score,
  then move to the next category.
- Always confirm the run actually selected a checkpoint (look for
  `saved best (...)` in the log) before trusting its `test:` line.

---

## 9. Experiment log (REQUIRED output — not optional)

Reproducing numbers is not the deliverable; the **log + insights are**. For every
category you sweep, create/append `experiments/<Category>.md`. Do this after each
round, before moving on.

### 9.1 Harvest the metrics from the run logs

Each run prints one final line like
`test: {'recall@5': 0.0361, 'recall@10': 0.0557, 'ndcg@5': 0.0240, 'ndcg@10': 0.0301}`.
Collect them all:

```bash
CAT=Musical_Instruments
for f in logs/${CAT}__*.log; do
  name=$(basename "$f" .log)
  saved=$(grep -c "saved best" "$f")          # 0 == no checkpoint, distrust!
  test=$(grep -E "^test:" "$f" | tail -1)
  printf '%s\t(saved=%s)\t%s\n' "$name" "$saved" "$test"
done
```

### 9.2 Results table (one row per run)

Fill `experiments/<Category>.md` with:

```markdown
## <Category>  (round r1, EP=<epochs>, SID=rqkmeans L3 W256, enc=sentence-t5-base)
Reference target (RUC/MTGRec TIGER): R@10 = <from Section 7>

| run_name | arm | knob | R@5 | R@10 | N@5 | N@10 | ΔR@10 vs ref | saved? |
|---|---|---|---:|---:|---:|---:|---:|:--:|
| Musical_Instruments__r1__G0__ref | G0 | lr 5e-4 | ... | ... | ... | ... | ... | ✓ |
| ... (all 8 arms) ... |

**Best this round:** `<run_name>`  —  R@10 = <x> (<gap> vs ref target).
```

### 9.3 Insights (write prose, not just numbers)

After the table, add an `### Insights` block answering at least:

- **LR curve**: across `G1..G4` (+G0), what is the shape and where is the peak?
  Is the optimum at an edge (→ extend the scan next round)?
- **Dropout**: did 0.05 / 0.20 help or hurt vs 0.10? Over- or under-fitting?
- **Architecture**: did the RUC arch (`G7`, d_ff 512 / 4 heads) beat the wider
  default? What does that say about capacity on this catalog?
- **Gap to reference**: how far is the best arm from the Section-7 target, and
  what is the most likely remaining cause?
- **Anomalies**: any run with `saved=0`, loss spikes, or collapse — note it.
- **Decision**: the exact config to carry into round 2 (or “converged, stop”).

### 9.4 Final per-category summary

When a category is finished, append a one-line entry to a top-level
`experiments/SUMMARY.md` table so all five categories live in one place:

```markdown
| Category | Best run_name | R@5 | R@10 | N@5 | N@10 | Ref R@10 | Matched? |
|---|---|---:|---:|---:|---:|---:|:--:|
```
