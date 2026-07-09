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
   `derive_hf_locators()` turns it into the reasoning / eval / catalog locators. The
   `./data/Amazon/...` strings are just locators, not files. Do **not** create, download, or
   preprocess local data.
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

## 3. Where the training data comes from

Phase‑2 trains on the **`<cat>_reasoning`** HF config (train split), reading its
**`reasoning_path`** column (the step‑by‑step trace). It also loads `<cat>_catalog` for the
SID↔title maps. Evaluation probes (loss only) use `<cat>_seqrec` (validation) for next‑item
SID prediction plus `<cat>_catalog` for title2sid / sid2title.

> Note: `<cat>_reasoning` also holds an `integrated_narrative` column, but that column is a
> **Phase‑1** input (sequence‑level SID‑text interleaving). Phase‑2 uses `reasoning_path`, not
> `integrated_narrative`.

## 4. The 3 domains

Run each independently, pairing `CATEGORY` with its Phase‑1 checkpoint:

| `CATEGORY`                   | `--base_model` (Phase‑1 checkpoint)                                  |
| ---------------------------- | ------------------------------------------------------------------- |
| `Video_Games`                | `./output_dir/Video_Games_stage1_sft_Qwen3-1.7B/final_checkpoint`   |
| `Office_Products`            | `./output_dir/Office_Products_stage1_sft_Qwen3-1.7B/final_checkpoint`|
| `Industrial_and_Scientific`  | `./output_dir/Industrial_and_Scientific_stage1_sft_Qwen3-1.7B/final_checkpoint` |

## 5. Environment / prerequisites

- **8× GPU @ 80 GB** (A100/H100). Config tuned for this: ZeRO‑2, bf16.
- `pip install -r requirements.txt` (`torch`, `deepspeed`, `transformers>=4.51`, `datasets`,
  `hf-transfer`, `wandb`, …).
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

## 8. Optional: sanity‑check the checkpoint with recsys metrics

Phase‑2 is a light format activation, so a single 1‑epoch checkpoint is expected — there is
no per‑epoch selection to do. If you want to confirm it didn't regress, you can score
`.../stage2_reasoning_activation_.../final_checkpoint` with the **reasoning** evaluator
(constrained beam decode over the SID codebook → NDCG@K / HR@K). See Phase‑1's `CLAUDE.md`
§7 for the exact split → `evaluate_Qwen3_think.py` → merge → `calc.py` recipe; just point the
`CK` variable at the Phase‑2 `final_checkpoint`.

## 9. Definition of done

For **each** domain you run:
- `./output_dir/<CATEGORY>_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint/` exists
  (a 1‑epoch reasoning‑activated model that reasons in `<think>…</think>` then emits a SID).
- Training log shows the single epoch completed and the eval losses (sid_pred / title2sid /
  sid2title) were recorded.

This Phase‑2 checkpoint is the initialization for **Phase‑3 (RL / GRPO)**.
