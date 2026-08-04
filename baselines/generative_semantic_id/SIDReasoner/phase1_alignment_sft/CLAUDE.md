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
*which column(s)* it actually reads. Nothing lives on disk: `--category` and an explicit
split are passed to `hf_data.py`, which calls
`load_dataset("yufan/recsys-genrec-dataset", <config>, split=...)` directly.

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

#### C · Explicit loader → HF config

| `hf_data` API | Resolves to |
| --- | --- |
| `load_seqrec(cat, "train")` | `<cat>_seqrec` (train) |
| `load_seqrec(cat, "validation")` | `<cat>_seqrec` (validation) |
| `load_item_features(cat)` | `<cat>_catalog` (train) |
| `load_sid_indices(cat)` / `load_sid_tokens(cat)` | `<cat>_catalog` (train) |
| `load_item_narratives(cat)` | `<cat>_catalog` (train) |
| `load_sequence_narratives(cat)` | `<cat>_reasoning` (train) |
| `load_general_reasoning()` | `general_reasoning` (train) |

**Validation sets.** The 3 eval sets (`val_sid`, `val_t2s`, `val_s2t`) reuse the classes
from rows 1–2 on `<cat>_seqrec` **(validation split)** + `<cat>_catalog`.

## 2. Golden rules (do not violate)

1. **Data is NEVER on local disk.** It is always pulled from Hugging Face
  `yufan/recsys-genrec-dataset` through the explicit category/split APIs in
  `hf_data.py`. Do **not** create, download, or preprocess local data files.
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
never mixed — see §5). You only pass the `CATEGORY`:

- `Video_Games`
- `Office_Products`
- `Industrial_and_Scientific`

## 4. Environment / prerequisites

- **8× GPU @ 80 GB** (A100/H100). Config is tuned for this: ZeRO‑2, bf16,
  gradient checkpointing.
- `pip install -r requirements.txt` (needs `torch`, `deepspeed`, `transformers>=4.51`,
  `vllm`, `datasets`, `hf-transfer`, `wandb`, `fire`, …). Recommendation HR/NDCG
  uses vLLM fixed-depth beam search over exactly three SID tokens.
- Network access to Hugging Face. Recommended: `export HF_HUB_ENABLE_HF_TRANSFER=1`.
  If you hit rate limits, `export HF_TOKEN=<your token>`.
- wandb: the API key is hardcoded in `sft_Qwen3.py` and logs from rank 0 only.
  To disable, pass `--report_to none`.

## 5. How to train (all 3 domains, or a subset)

`--category` is the **single data knob**. `sft_Qwen3.py::build_datasets` passes it
directly to the explicit `hf_data` APIs, and the launcher has no file-path variables.

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
| `num_epochs` | 5 | maximum; stop after 2 consecutive non-improving eval epochs |
| `cutoff_len` | 1024 | general‑reasoning subset uses 3072 |
| `zero_stage` | 2 | not 3 |
| precision | bf16 | + gradient checkpointing |

Tuning notes:
- If you change the global batch, rescale LR ~linearly (`LR ≈ 3e-4 × global_batch / 1024`).
- If you see random OOM mid‑epoch, it's a 3072‑token batch — lower `micro_batch_size` to
  4–6. If GPUs are underutilized, raise to 12–16 and bump LR proportionally.

## 7. Checkpoint selection = recsys metrics (IMPORTANT)

**The final checkpoint MUST be chosen by recsys metrics, per domain.**

- Before training, every node creates the same SID-extended `epoch_0` checkpoint with the
  training seed. Node-0 immediately runs no-thinking catalog-constrained beam-10 evaluation
  on its copy and uploads step 0 to W&B. If preparation, evaluation, metric calculation, or
  W&B upload fails, the launcher exits before DeepSpeed starts.
- Multi-node training then loads that exact `epoch_0` checkpoint and saves every completed
  `epoch_<N>`. A manifest identifies only checkpoints from the current run, so stale
  directories are never evaluated.
- After **all** DeepSpeed processes on **all** nodes exit, node-0 evaluates the trained
  `epoch_1...N` checkpoints on its 8 local GPUs. Generation never overlaps the NCCL job,
  avoiding GPU contention and collective deadlocks.
- The four metrics are `HR@5`, `HR@10`, `NDCG@5`, and `NDCG@10`. W&B stores them under
  `recsys_eval_nothinking/*` with `recsys_eval_step = epoch`, producing one line per metric
  from the untrained SID-extended baseline through all epochs.
- Local predictions and the incrementally extended `metrics.json` are written under
  `.../recsys_eval_nothinking/`. Pick the epoch with the best NDCG@10 / HR@10; the
  lowest-validation-loss `final_checkpoint` remains only a convenience pointer.

## 8. Definition of done

For **each** of the 3 domains:
- Baseline `epoch_0` and per‑epoch checkpoints at
  `./output_dir/<CATEGORY>_stage1_sft_Qwen3-1.7B/epoch_<N>`
  (plus the loss‑best `final_checkpoint` pointer).
- `recsys_eval_nothinking/metrics.json` plus W&B HR/NDCG lines for epoch 0 through the
  last trained epoch, and the
  **selected best epoch** (by NDCG@10 / HR@10) recorded as the domain's Phase‑1 winner.

The 3 selected Phase‑1 checkpoints are the initialization for Phase‑2 (reasoning activation).
