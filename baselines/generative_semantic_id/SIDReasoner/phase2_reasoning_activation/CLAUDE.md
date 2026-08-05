# CLAUDE.md — Phase‑2 Reasoning Activation (SIDReasoner)

Instructions for an AI agent that will **run Phase‑2 training** of the SIDReasoner
pipeline. Read this fully before running anything. Phase‑2 assumes Phase‑1 is done.

---

## 1. What Phase‑2 is

Phase‑2 = **Reasoning Activation (cold start)**. We take the **Phase‑1 checkpoint** (SIDs
already aligned to language) and do a short SFT that teaches the model the output
*format*: **reason in natural language inside a `<think>…</think>` block, then emit the
target Semantic ID**. It does not teach a new ability — Phase‑1 already gave the model
the ability to reason and to recommend — it only makes the model reliably *reason first,
then recommend*. The resulting checkpoint initializes Phase‑3 (RL / GRPO).

- Training entry point: `phase2_reasoning_activation/sft_reasoning_activation.py` — an
  **explicit DeepSpeed training loop**, mirroring Phase‑1's `sft_Qwen3.py` (no HuggingFace
  `Trainer`; forward/backward/step, eval and checkpointing are all visible).
- Launcher: `phase2_reasoning_activation/sft_reasoning_activation.sh`.

## 2. Golden rules (do not violate)

1. **Initialize from the Phase‑1 checkpoint of the SAME domain.** `--base_model` must point
   to `./output_dir/<CATEGORY>_stage1_sft_Qwen3-1.7B/final_checkpoint`. That checkpoint
   already contains the SID tokens + trained embeddings; do not start from the raw base LLM.
2. **Data is NEVER on local disk.** It is pulled from Hugging Face
   `yufan/recsys-genrec-dataset` via `hf_data.py`. `--category` is the **single data knob** —
  eval datasets use explicit category/split APIs, while `derive_hf_locators()` still
  supplies the reasoning/catalog adapters used by the Phase-2 training dataset. The
  `./data/Amazon/...` strings are not files. Do **not** create or preprocess local data.
3. **Train ONE domain at a time.** 3 independent domains, each with its own SID codebook and
   its own Phase‑1 checkpoint. Never mix domains, and never point `--base_model` at a
   different domain's checkpoint than `--category`.
4. **Train exactly ONE epoch.** Phase‑2 is a *lightweight* format activation (paper §3.3.1).
   `--num_epochs 1`. Do not crank epochs — more epochs here tends to over‑imitate the teacher
   template and hurt the downstream RL stage.
5. **Loss is completion‑only.** `ReasoningActivationDataset` masks the prompt to `-100` and
   trains on the assistant turn (`<think>{reasoning}</think>\n\n{SID}`) via
   `mask_assistant_response_only(..., mask_eos=False)`. This lives in the dataset — don't change it.
6. **Use the model's built‑in Qwen3 chat template.** Do not override `tokenizer.chat_template`.
7. Run from the repo root (`SIDReasoner/`). The launcher already `cd`s there and sets `PYTHONPATH`.

## 3. Where the training data comes from (HF config & column map)

**What this is.** The authoritative provenance of Phase‑2, mirroring Phase‑1's §1.1 — for
the single training set and the three eval probes built by
`sft_reasoning_activation.py::build_datasets`, *which HF config ("category")* and *which
column(s)* each actually reads. Nothing lives on disk: training still uses the legacy
HF adapters, while eval passes category/split directly to `hf_data.py`.

**Only 3 configs are touched** (`<cat>` = the single domain being trained; no
`general_reasoning` here, unlike Phase‑1):

- **`<cat>_reasoning`** — rec samples + their step‑by‑step reasoning trace (train)
- **`<cat>_seqrec`** — user next‑item sequences (validation split only, for a loss probe)
- **`<cat>_catalog`** — item universe: titles + SID tokens (for the translation loss probes)

#### A · Training set → config & columns

Exactly **one** training dataset (no mixture, unlike Phase‑1's 8):

| Dataset class | What it learns | HF config | Column(s) actually used |
| --- | --- | --- | --- |
| `ReasoningActivationDataset` | reason over SID history in `<think>…</think>`, then emit the target SID | `<cat>_reasoning` (train) | `history_item_sid`, `item_sid`, `reasoning_path` |

Per‑sample construction (`get_history` / `pre`): prompt = the `history_item_sid` sequence;
assistant target = `<think>\n{reasoning_path}\n</think>\n\n{item_sid}`. Rows with an empty /
unclosed `reasoning_path` are dropped. Loss is completion‑only (`mask_eos=False`).

> **Caveat — catalog is loaded but not consumed by the training sample.**
> `build_datasets` also passes `item_meta_path` (`<cat>_catalog`) + `sid_index_path` into
> `ReasoningActivationDataset`, which builds `sid2title` / `sid2description` maps. But the
> current `pre()` uses only `history_item_sid`, `item_sid`, `reasoning_path` — the catalog
> maps do **not** enter the Phase‑2 training example. (Catalog is genuinely used only by the
> eval probes below.)

> **Trap — `integrated_narrative` vs `reasoning_path`.** The training locator is literally
> named `{cat}.integrated_narrative.csv`, and its filename routes `load_df` to the
> `<cat>_reasoning` config — **but Phase‑2 reads the `reasoning_path` column, not
> `integrated_narrative`.** The `integrated_narrative` column of the same config is a
> **Phase‑1** input (sequence‑level SID‑text interleaving, see Phase‑1 §1.1 row 7).

#### B · Eval probes → config & columns (loss only)

These three compute eval loss only (no checkpoint selection — Phase‑2 is 1 epoch):

| Probe | Dataset class | HF config | Column(s) used |
| --- | --- | --- | --- |
| `val_sid` (next‑item SID) | `SidHistory2SidSFTDataset` | `<cat>_seqrec` **(validation)** | `history_item_sid`, `item_sid` |
| `val_t2s` (title → SID) | `TitleSidTranslationDataset` | `<cat>_catalog` (train) | `item_id`, `title`, `sid_tokens` |
| `val_s2t` (SID → title) | `TitleSidTranslationDataset` | `<cat>_catalog` (train) | `item_id`, `title`, `sid_tokens` |

#### C · Loader → HF config

| Input | `hf_data` loader | Resolves to |
| --- | --- | --- |
| `reasoning_train_file` — `{cat}.integrated_narrative.csv` | `load_df` | `<cat>_reasoning` (train) |
| `category` + `split="validation"` | `load_seqrec` | `<cat>_seqrec` (validation) |
| `item_meta_path` — `{cat}.item.json` | `load_item_feat` | `<cat>_catalog` (train) |
| `sid_index_path` — `{cat}.index.json` | `load_indices` | `<cat>_catalog` (train) |

**Resolution rules** (`hf_data.py`): `load_df` special‑cases any filename containing
`integrated_narrative` → the `<cat>_reasoning` config; the leading `<cat>.` keys the
catalog files. Evaluation no longer relies on these filename rules.

## 4. The 3 domains

Run each independently, pairing `CATEGORY` with its Phase‑1 checkpoint:

| `CATEGORY`                   | `--base_model` (Phase‑1 checkpoint)                                  |
| ---------------------------- | ------------------------------------------------------------------- |
| `Video_Games`                | `./output_dir/Video_Games_stage1_sft_Qwen3-1.7B/final_checkpoint`   |
| `Office_Products`            | `./output_dir/Office_Products_stage1_sft_Qwen3-1.7B/final_checkpoint`|
| `Industrial_and_Scientific`  | `./output_dir/Industrial_and_Scientific_stage1_sft_Qwen3-1.7B/final_checkpoint` |

## 5. Environment / prerequisites

- **8× GPU @ 80 GB** (A100/H100). Config tuned for this: ZeRO‑2, bf16.
- `pip install -r requirements.txt` (`torch`, `deepspeed`, `transformers>=4.51`, `vllm`,
  `datasets`, `hf-transfer`, `wandb`, …). Thinking and no-thinking HR/NDCG use
  the same vLLM fixed-depth beam search over exactly three SID tokens.
- Network access to Hugging Face. Recommended: `export HF_HUB_ENABLE_HF_TRANSFER=1`.
  If you hit rate limits, `export HF_TOKEN=<your token>`.
- The Phase‑1 checkpoint for the chosen domain must already exist under `./output_dir/...`.
- wandb: the API key is hardcoded in `sft_reasoning_activation.py` and logs from rank 0 only
  (project `SIDReasoner_Phase2`). To disable, pass `--report_to none`.

## 6. How to train one domain

The launcher is currently wired to **`Video_Games`**. To train another domain, edit the four
vars at the top of `sft_reasoning_activation.sh` (`CATEGORY` + the three `<CATEGORY>_...` paths):

```bash
CATEGORY="Video_Games"
BASE_MODEL="./output_dir/${CATEGORY}_stage1_sft_Qwen3-1.7B/final_checkpoint"
OUTPUT_DIR="./output_dir/${CATEGORY}_stage2_reasoning_activation_Qwen3-1.7B"
RUN_NAME="${CATEGORY}_stage2_reasoning_activation_Qwen3-1.7B"
```

Then launch from the repo root. **Always launch with `nohup … &`** so the run survives
SSH disconnects / terminal hangups (the script writes its own training log to
`./logs/<RUN_NAME>.txt`):

```bash
cd baselines/generative_semantic_id/SIDReasoner
mkdir -p logs   # nohup's redirect target must exist before launch
nohup bash phase2_reasoning_activation/sft_reasoning_activation.sh > logs/phase2_launch.out 2>&1 &
```

- Training log → `./logs/<RUN_NAME>.txt`
- Output checkpoint → `./output_dir/<CATEGORY>_stage2_reasoning_activation_Qwen3-1.7B/`
  (`epoch_1/`, and `final_checkpoint/` which for a 1‑epoch run is the same weights).
- Recommendation metrics → `.../recsys_eval/{pretrain,posttrain}/metrics.json`.
  Each stage reports thinking and no-thinking `HR@5`, `HR@10`, `NDCG@5`, and `NDCG@10`.
- W&B keeps the stages together in two blocks: `recsys_eval_nothinking/*` and
  `recsys_eval_thinking/*`. Their charts use `recsys_eval_step` as the x-axis, where
  `0` is before training and `1` is after training.

Repeat for each domain you need (edit the vars, or copy the launcher per domain).

## 7. Key hyperparameters (already set for 8×80 GB)

| Item | Value | Note |
| --- | --- | --- |
| `--base_model` | Phase‑1 `final_checkpoint` | same domain as `--category` |
| `micro_batch_size` | 8 | per‑GPU |
| `grad_accum` | 1 | **hardcoded** in code |
| world size | 8 | → global batch = `8 × 1 × 8 = 64` |
| `num_epochs` | **1** | cold‑start activation; keep at 1 |
| `learning_rate` | 1e‑5 | linear schedule + 10 warmup steps |
| `cutoff_len` | 1024 | left‑truncation; no 3072 general subset here |
| `zero_stage` | 2 | not 3 |
| precision | bf16 | |
| gradient checkpointing | **OFF** | seqs ≤1024 & global batch 64 → memory is fine without it |
| early stopping | off (`-1`) | only 1 epoch anyway |

The launcher also exports `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (the same
allocator fix used in Phase‑1) to avoid fragmentation OOM.

Tuning notes:
- If you change the global batch, rescale LR ~linearly.
- If a GPU OOMs, drop `micro_batch_size` to 4–6. If GPUs are underutilized, raise it.

## 8. Automatic recommendation evaluation

The launcher evaluates twice: the Phase‑1 `BASE_MODEL` before training and `epoch_1` after
training. At each point it runs both no-thinking direct decoding and thinking-mode two-pass
decoding, with catalog-constrained beam-10 in both modes. It records `HR@5`, `HR@10`,
`NDCG@5`, and `NDCG@10` under `OUTPUT_DIR/recsys_eval/` so the before/after effect is directly
comparable. The launcher gives the pre-evaluation, training process, and post-evaluation one
shared W&B run ID, so these metrics appear alongside the training loss instead of creating
separate runs. W&B does not create separate pretrain/posttrain metric blocks: each HR/NDCG
chart has the two evaluation points connected in one line. The local JSON snapshots remain
separate for reproducibility. Set `EVAL_NUM_SAMPLES` in the launcher to a positive value for
a pilot; `-1` evaluates the full test split.

## 9. Definition of done

For **each** domain you run:
- `./output_dir/<CATEGORY>_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint/` exists
  (a 1‑epoch reasoning‑activated model that reasons in `<think>…</think>` then emits a SID).
- Training log shows the single epoch completed and the eval losses (sid_pred / title2sid /
  sid2title) were recorded.
- `recsys_eval/pretrain/metrics.json` and `recsys_eval/posttrain/metrics.json` contain both
  thinking and no-thinking HR/NDCG at 5 and 10.

This Phase‑2 checkpoint is the initialization for **Phase‑3 (RL / GRPO)**.
