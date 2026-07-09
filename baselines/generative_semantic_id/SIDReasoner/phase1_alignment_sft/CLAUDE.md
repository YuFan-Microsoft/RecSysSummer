# CLAUDE.md — Phase‑1 Alignment SFT (SIDReasoner)

Instructions for an AI agent that will **run Phase‑1 training** of the SIDReasoner
pipeline. Read this fully before running anything.

---

## 1. What Phase‑1 is

Phase‑1 = **Alignment SFT**. We take a base LLM (`Qwen/Qwen3-1.7B`) and teach it to
align **Semantic IDs (SIDs)** — a 3‑token code per item, `<a_x><b_y><c_z>` — with item
semantics, across **8 mixed tasks**. Despite the “SFT” name, the mixture has **two**
objective types:
- **6 completion‑only SFT tasks** (chat template + prompt masked to `-100`, loss on the
  response only): title⇄SID translation, SID/​title history → next SID/​title, the fusion
  seqrec task, and general reasoning to preserve general ability.
- **2 continued‑pretraining (plain‑LM) tasks**: item‑level and sequence‑level **SID‑text
  interleaving** (`SidTextInterleaveItemDataset`, `SidTextInterleaveSequenceDataset`). These
  do **not** use the chat template or prompt masking — they run next‑token LM over the whole
  interleaved sequence (`labels = input_ids`) so the new SID embeddings soak up the language
  distribution.

The resulting checkpoint later initializes Phase‑2 (reasoning activation) and Phase‑3 (RL).

- Training entry point: `phase1_alignment_sft/sft_Qwen3.py` — an **explicit DeepSpeed
  training loop** (no HuggingFace `Trainer`; the forward/backward/step, eval and
  checkpointing are all visible).
- Launcher: `phase1_alignment_sft/sft_Qwen3_enrich.sh`.

### 1.1 · The 8 training datasets ↔ Hugging Face config & column map

**What this is.** The authoritative provenance of the Phase‑1 mixture — for each of the
8 datasets built by `sft_Qwen3.py::build_datasets`, *which HF config ("category")* and
*which column(s)* it actually reads. Nothing lives on disk: `derive_hf_locators` turns
`--category` into fake file paths, and `hf_data.py` parses those locators and calls
`load_dataset("yufan/recsys-genrec-dataset", <config>, split=...)`.

**Only 4 configs are ever touched per run.** `<cat>` is one of `Video_Games` /
`Office_Products` / `Industrial_and_Scientific` (each an independent SID codebook):

- **`<cat>_seqrec`** — user next‑item sequences (train / validation / test splits)
- **`<cat>_catalog`** — the item universe: titles, descriptions, SID tokens, narratives
- **`<cat>_reasoning`** — one reasoning narrative per user sequence
- **`general_reasoning`** — domain‑independent general SFT (shared, used in Phase‑1 only)

#### A · Dataset → config (build order)

| # | Dataset class | What it learns | HF config(s) |
| :-: | --- | --- | --- |
| 1 | `SidHistory2SidSFTDataset` | SID history → next SID | `<cat>_seqrec` |
| 2 | `TitleSidTranslationDataset` | Title ⇄ SID translation | `<cat>_catalog` |
| 3 | `SidHistory2TitleSFTDataset` | SID history → next Title | `<cat>_seqrec` + `<cat>_catalog` |
| 4 | `TitleHistory2TitleSFTDataset` | Title history → next Title | `<cat>_seqrec` |
| 5 | `TitleHistory2SidSFTDataset` | Title history → next SID | `<cat>_seqrec` + `<cat>_catalog` |
| 6 | `SidTextInterleaveItemDataset` | item‑level SID⇄text narrative (plain‑LM) | `<cat>_catalog` |
| 7 | `SidTextInterleaveSequenceDataset` | sequence‑level SID⇄text narrative (plain‑LM) | `<cat>_reasoning` |
| 8 | `GeneralReasoningSFTDataset` | general reasoning | `general_reasoning` |

#### B · Which columns each dataset reads

1. **`SidHistory2SidSFTDataset`**
   - `<cat>_seqrec` → `history_item_sid`, `item_sid`

2. **`TitleSidTranslationDataset`**
   - `<cat>_catalog` → `item_id`, `title`, `sid_tokens`  *(builds the title ⇄ SID map)*

3. **`SidHistory2TitleSFTDataset`**
   - `<cat>_seqrec` → `history_item_sid`, `item_sid`
   - `<cat>_catalog` → `item_id`, `title`, `sid_tokens`
   - *(also loads `description`, but the current sample builder does not use it)*

4. **`TitleHistory2TitleSFTDataset`**
   - `<cat>_seqrec` → `history_item_title`, `item_title`

5. **`TitleHistory2SidSFTDataset`**
   - `<cat>_seqrec` → `history_item_title`, `item_id`
   - `<cat>_catalog` → `item_id`, `sid_tokens`
   - *(also loads `item.json`, but only `sid_tokens` from `index.json` is used)*

6. **`SidTextInterleaveItemDataset`**
   - `<cat>_catalog` → `sid_interleaved_narrative`  *(keyed by `item_id`)*

7. **`SidTextInterleaveSequenceDataset`**
   - `<cat>_reasoning` → `integrated_narrative`

8. **`GeneralReasoningSFTDataset`**
   - `general_reasoning` → `messages`

#### C · Locator → loader (how the fake paths resolve)

| Locator (from `derive_hf_locators`) | `hf_data` loader | Resolves to |
| --- | --- | --- |
| `train_file` — `{cat}_5_2016-10-2018-11.csv` under `train/` | `load_df` | `<cat>_seqrec` (train) |
| `eval_file` — same stem under `valid/` | `load_df` | `<cat>_seqrec` (validation) |
| `item_meta_path` — `{cat}.item.json` | `load_item_feat` | `<cat>_catalog` (train) |
| `sid_index_path` — `{cat}.index.json` | `load_indices` | `<cat>_catalog` (train) |
| `llm_generated_data_path` — `{cat}.item_enhanced_v2.json` | `load_enhanced` | `<cat>_catalog` (train) |
| `llm_generated_sequence_path` — `{cat}.integrated_narrative.csv` | `load_df` | `<cat>_reasoning` (train) |
| `general_reasoning_path` — `general/sampled_data.arrow` | `load_general` | `general_reasoning` (train) |

**Resolution rules** (`hf_data.py`):

- `infer_category` keys off the `_5_` marker (seqrec files) and the leading `<cat>.`
  (catalog files).
- `_seqrec_split` maps the `train` / `valid` parent dir (and `test`) to the split.
- `load_df` special‑cases any filename containing `integrated_narrative` → the
  `<cat>_reasoning` config.

**Validation sets.** The 3 eval sets (`val_sid`, `val_t2s`, `val_s2t`) reuse the classes
from rows 1–2 on `<cat>_seqrec` **(validation split)** + `<cat>_catalog`.

## 2. Golden rules (do not violate)

1. **Data is NEVER on local disk.** It is always pulled from Hugging Face
   `yufan/recsys-genrec-dataset` through `hf_data.py`. The file paths in the shell
   script (`./data/Amazon/...`) are just **locators** — `hf_data` parses the category
   (and split) out of the path and calls `datasets.load_dataset(...)`. Do **not** try to
   create, download, or preprocess local data files.
2. **Train ONE domain at a time.** There are **3 independent domains**, each with its own
   SID codebook. Never mix domains in a single run.
3. **SFT loss is computed on the assistant response only** (`--mask_assistant True`);
   everything else is masked to `-100`. This governs the **6 SFT tasks**; the 2 SID‑text
   interleaving tasks are continued‑pretraining and intentionally ignore this flag (they
   always run full‑sequence LM). Keep `--mask_assistant True`.
4. **Use the model's built‑in Qwen3 chat template** (via `tokenizer.apply_chat_template`).
   Do not override `tokenizer.chat_template`.
5. Run from the repo root (`SIDReasoner/`). The launcher already `cd`s there and sets
   `PYTHONPATH`.

## 3. The 3 domains

The launcher trains these three in sequence by default (one training run per domain,
never mixed — see §5). You normally only pass the `CATEGORY`; the file stem below is the
internal seqrec filename `derive_hf_locators` builds and is shown only for reference.

| `CATEGORY`                    | file stem (`STEM`)                          |
| ----------------------------- | ------------------------------------------- |
| `Video_Games`                 | `Video_Games_5_2016-10-2018-11`             |
| `Office_Products`             | `Office_Products_5_2016-10-2018-11`         |
| `Industrial_and_Scientific`   | `Industrial_and_Scientific_5_2016-10-2018-11` |

## 4. Environment / prerequisites

- **8× GPU @ 80 GB** (A100/H100). Config is tuned for this: ZeRO‑2, bf16,
  gradient checkpointing.
- `pip install -r requirements.txt` (needs `torch`, `deepspeed`, `transformers>=4.51`,
  `datasets`, `hf-transfer`, `wandb`, `fire`, …).
- Network access to Hugging Face. Recommended: `export HF_HUB_ENABLE_HF_TRANSFER=1`.
  If you hit rate limits, `export HF_TOKEN=<your token>`.
- wandb: the API key is hardcoded in `sft_Qwen3.py` and logs from rank 0 only.
  To disable, pass `--report_to none`.

## 5. How to train (all 3 domains, or a subset)

`--category` is the **single data knob**: every data locator (`train_file`, `eval_file`,
`sid_index_path`, `item_meta_path`, `llm_generated_data_path`,
`llm_generated_sequence_path`) is derived from it inside
`sft_Qwen3.py::derive_hf_locators`. The launcher has **no** per-file path variables.

`sft_Qwen3_enrich.sh` **defaults to training all 3 domains in sequence**
(`Video_Games → Office_Products → Industrial_and_Scientific`), one domain per run —
never mixed. For each domain it auto-derives `RUN_NAME` / `OUTPUT_DIR` / `LOG_FILE` from
the category, so you do **not** edit the script.

```bash
cd baselines/generative_semantic_id/SIDReasoner
mkdir -p logs   # nohup's redirect target must exist before launch

# All 3 domains, back to back (default). ALWAYS launch with `nohup … &` so the long
# multi-domain run survives SSH disconnects / terminal hangups:
nohup bash phase1_alignment_sft/sft_Qwen3_enrich.sh > logs/phase1_launch.out 2>&1 &

# Or train a subset — pass category names as args (still under nohup):
nohup bash phase1_alignment_sft/sft_Qwen3_enrich.sh Video_Games > logs/phase1_launch.out 2>&1 &
nohup bash phase1_alignment_sft/sft_Qwen3_enrich.sh Office_Products Industrial_and_Scientific > logs/phase1_launch.out 2>&1 &
```

Follow progress with `tail -f logs/<CATEGORY>_stage1_sft_Qwen3-1.7B.txt` — the script
writes each domain's full training log there.

The loop is **fail-fast** (`set -euo pipefail`): if one domain errors, the remaining
domains do not run. Per-domain outputs:

- Training log → `./logs/<CATEGORY>_stage1_sft_Qwen3-1.7B.txt`
- Best checkpoint → `./output_dir/<CATEGORY>_stage1_sft_Qwen3-1.7B/final_checkpoint`

## 6. Key hyperparameters (already set for 8×80 GB)

| Item | Value | Note |
| --- | --- | --- |
| `micro_batch_size` | 8 | per‑GPU; sized for the 3072‑token general‑reasoning samples |
| `grad_accum` | 1 | **hardcoded** in code |
| world size | 8 | → global batch = `8 × 1 × 8 = 64` |
| `learning_rate` | 2e‑5 | scaled from the base (batch 1024 ↔ LR 3e‑4) |
| `num_epochs` | 5 | every epoch is saved; early stopping off by default |
| `cutoff_len` | 1024 | general‑reasoning subset uses 3072 |
| `zero_stage` | 2 | not 3 |
| precision | bf16 | + gradient checkpointing |

Tuning notes:
- If you change the global batch, rescale LR ~linearly (`LR ≈ 3e-4 × global_batch / 1024`).
- If you see random OOM mid‑epoch, it's a 3072‑token batch — lower `micro_batch_size` to
  4–6. If GPUs are underutilized, raise to 12–16 and bump LR proportionally.

## 7. Checkpoint selection = recsys metrics (IMPORTANT)

**The final checkpoint MUST be chosen by recsys metrics, per domain.**

- Training saves **every epoch** to `./output_dir/<CATEGORY>_stage1_sft_Qwen3-1.7B/epoch_<N>`
  (early stopping is **off by default**, so all `num_epochs` are produced). It also copies
  the lowest‑val‑loss epoch to `.../final_checkpoint` as a convenience pointer — but
  val loss is only a **proxy**, not the selection criterion.
- **Selection = evaluate each `epoch_<N>` with the recsys pipeline and keep the best.**
  The pipeline does **constrained beam decoding over the SID codebook** and computes
  **NDCG@K / HR@K** (K ∈ {1,3,5,10,20,50}). Pick the epoch with the best **NDCG@10 / HR@10**.

Evaluate one checkpoint (uses HF data automatically):

```bash
CAT="Video_Games"; STEM="Video_Games_5_2016-10-2018-11"
CKPT="epoch_5"                                  # <-- the epoch_<N> dir to score (N in 1..num_epochs)
CK="./output_dir/${CAT}_stage1_sft_Qwen3-1.7B/${CKPT}"
TEST="./data/Amazon/test/${STEM}.csv"          # locator → HF test split
INFO="./data/Amazon/info/${STEM}.txt"
ITEM="./data/Amazon/index/${CAT}.item.json"
INDEX="./data/Amazon/index/${CAT}.index.json"
TMP="./temp/eval_${CAT}_${CKPT}"; OUT="./results/eval_${CAT}_${CKPT}"; mkdir -p "$TMP" "$OUT"

# 1) shard the test set across 8 GPUs
python evaluation/split.py --input_path "$TEST" --output_path "$TMP" --cuda_list "0,1,2,3,4,5,6,7"

# 2) constrained beam-search decode on each GPU
for i in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$i python -u evaluation/evaluate_Qwen3_think.py \
    --base_model "$CK" --info_file "$INFO" --category "$CAT" \
    --test_data_path "$TMP/$i.csv" --item_file "$ITEM" --index_file "$INDEX" \
    --result_json_data "$TMP/$i.json" \
    --batch_size 4 --num_beams 10 --max_new_tokens 1024 --length_penalty 0.0 &
done; wait

# 3) merge + compute NDCG / HR
python evaluation/merge.py --input_path "$TMP" --output_path "$OUT/final_result_${CAT}.json" --cuda_list "0,1,2,3,4,5,6,7"
python evaluation/calc.py --path "$OUT/final_result_${CAT}.json" --item_path "$INFO"
```

`calc.py` prints `NDCG` and `HR` at each K. **Loop the block above over every
`epoch_<N>` dir**, record NDCG@10 / HR@10, and keep the best epoch as the domain's final
Phase‑1 checkpoint. (Evaluating every epoch is the reliable way to pick the winner; the
per‑epoch checkpoints exist precisely for this.)

A ready‑made end‑to‑end evaluator for all 3 domains lives at
`../run_all_domains.sh` (split → decode → merge → calc). It is currently wired to RL
`actor_merged` checkpoints; for Phase‑1, point its `CK` at an `epoch_<N>` dir.

## 8. Definition of done

For **each** of the 3 domains:
- Per‑epoch checkpoints at `./output_dir/<CATEGORY>_stage1_sft_Qwen3-1.7B/epoch_<N>`
  (plus the loss‑best `final_checkpoint` pointer).
- A recsys‑metrics table (NDCG/HR per epoch) from the evaluation pipeline, and the
  **selected best epoch** (by NDCG@10 / HR@10) recorded as the domain's Phase‑1 winner.

The 3 selected Phase‑1 checkpoints are the initialization for Phase‑2 (reasoning activation).
