# CLAUDE.md — SIDReasoner

Guidance for Claude when working in this repository.

## Model initialization checkpoint

The Stage-2 (reasoning-activation) checkpoint to **initialize / resume Stage-3 RL from**:

```
/yufan/checkpoint_backup/Video_Games_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint
```

- Backbone: **Qwen3-1.7B**, domain: **Video_Games**.
- This is the `actor_rollout_ref.model.path` for GRPO RL.

## Start Stage-3 RL training

This directory ([`RL_training_script.sh`](RL_training_script.sh)) runs Stage-3 GRPO
RL on **verl 0.6.0** (`verl` is a top-level package dir at the repo root; launch is
the standard `python -m verl.trainer.main_ppo`).

Launch it from the **repo root** with the model path above. **Always launch with
`nohup … &`** so the long RL run survives SSH disconnects / terminal hangups (the
script already writes its own training log via `> "${log_file}" 2>&1`):

```bash
mkdir -p logs   # nohup's redirect target must exist before launch
nohup bash phase3_rl/RL_training_script.sh \
    actor_rollout_ref.model.path=/yufan/checkpoint_backup/Video_Games_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint \
    > logs/phase3_launch.out 2>&1 &
```

The script forwards trailing args (`"$@"`) to `python -m verl.trainer.main_ppo`,
and Hydra applies last-wins overrides, so the `model.path` above overrides the
script's default checkpoint.

### Domain: Video_Games (script default)

The script **defaults to the `Video_Games` domain end‑to‑end** — data, reward, and the
**wandb run name** all match the Games checkpoint above. Concretely the script sets
`trainer.experiment_name=Video_Games_stage3_rl_Qwen3-1.7B` (this is the wandb run name,
under project `SIDReasoner_Phase3`), `data.*=.../Video_Games/*.parquet`, and
`custom_reward_function.path=.../direct_recommendation_StepRule_Games.py`. So the launch
command above is all you need — you do **not** have to override data / reward / wandb.

To run a **different** domain, override its four knobs **and keep the wandb run name in
sync** so the experiment is labeled by its real domain, e.g. for Office_Products:

```bash
nohup bash phase3_rl/RL_training_script.sh \
    actor_rollout_ref.model.path=./output_dir/Office_Products_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint \
    trainer.experiment_name=Office_Products_stage3_rl_Qwen3-1.7B \
    data.train_files=./data/Amazon/rec_reasoning_verl/Office_Products/train.parquet \
    data.val_files=./data/Amazon/rec_reasoning_verl/Office_Products/test.parquet \
    custom_reward_function.path=./verl/utils/reward_score/direct_recommendation_StepRule_Office.py \
    > logs/phase3_launch.out 2>&1 &
```

(The Games reward reads `./data/Amazon_Games/info/Video_Games_5_2016-10-2018-11.txt`,
resolved relative to the repo root — the RL script `cd`s there.)

## Data source (Hugging Face, NOT local) — HF config & column map

Like Phase‑1/2, **all Phase‑3 data comes from `yufan/recsys-genrec-dataset`, never from
local disk.** But Phase‑3 has **two data stages**, so the provenance has two halves:

1. **Offline materialization** — [`create_reasoning_rl_data.py`](create_reasoning_rl_data.py)
   pulls from HF (`hf_data.load_df(...)`) and writes verl parquet
   (`./data/Amazon/rec_reasoning_verl/<domain>/{train,test}.parquet`).
2. **RL training** — `RL_training_script.sh` feeds those parquet to verl GRPO; the
   **reward function** then scores rollouts online, itself reading one more HF config.

The `./data/...` strings are just locators / output targets, **not** tracked local data —
run the materialization once per domain before launching RL; do not hand‑edit local files.

### A · Materialization → which HF config / columns feed the parquet

`Reasoning_RL_Dataset` builds each `(prompt, ground‑truth)` pair from:

| verl split | HF config | Column(s) actually used |
| --- | --- | --- |
| `train.parquet` | `<cat>_reasoning` (train) | `history_item_sid`, `item_sid` |
| `test.parquet` | `<cat>_seqrec` (test) | `history_item_sid`, `item_sid` |

- The **train locator** is `{cat}.integrated_narrative.csv` → `load_df` routes it to the
  `<cat>_reasoning` config; the **test locator** sits under `test/` → `<cat>_seqrec` (test).
- **RL reads only `history_item_sid` + `item_sid`.** Unlike Phase‑2 it does **not** read
  `reasoning_path` / `integrated_narrative` — GRPO makes the model generate its *own*
  reasoning, so no teacher trace is kept; only the target SID becomes the ground truth.
- **Catalog is loaded but not consumed** (same trap as Phase‑2): `Reasoning_RL_Dataset`
  also loads `<cat>_catalog` (`item.json` + `index.json`) into a `sid2title` map, but
  `pre()` never uses it — the prompt is the SID history, the ground truth is the raw
  `item_sid`.

### B · verl parquet schema (what RL actually trains on)

`convert_to_verl_format` writes one row per sample:

| Column | Content |
| --- | --- |
| `prompt` | chat `messages` = system instruction + "user interacted with {SID history}…" |
| `reward_model.ground_truth` | the target `item_sid` (raw 3‑token SID string) |
| `data_source` · `ability` · `extra_info` | routing / bookkeeping (split, index, echoed Q/A) |

### C · Reward function → which HF config / columns it reads

The custom reward (`verl/utils/reward_score/direct_recommendation_StepRule_<Domain>.py`)
builds a **SID prefix tree** for its format check:

| Loads | HF config | Column(s) used |
| --- | --- | --- |
| `construct_prefix_allowed_hashmap` → `hf_data.load_info_lines(...)` | `<cat>_catalog` (train) | `sid` (from the rebuilt `sid⇥title⇥item_id` line map) |

- The info‑file locator (e.g. `Video_Games_5_2016-10-2018-11.txt`) carries the `_5_` marker,
  so `infer_category` keys the right `<cat>_catalog`.
- Reward = **hit reward** (0.25, then ×2, then ×2 as SID tokens *a → b → c* match
  `ground_truth`) **+ 0.1 × format reward** (is the emitted 3‑token SID a valid path in the
  catalog prefix tree). Only the catalog `sid` column matters; `title` / `item_id` are read
  by `load_info_lines` but unused by the reward.

## Environment

- Build/run with [`../Dockerfile`](../Dockerfile): verl 0.6 base image
  (CUDA 12.8, torch 2.8.0, flash-attn 2.7.4) + **vllm 0.10.2** + deepspeed + fire.
- Requires GPUs (Stage-3 RL uses vLLM rollout + FSDP).
- `verl` (repo root) — v0.6.0 trainer (active, top-level package dir).

## Repo layout quick reference

Paths below are relative to the **repo root** (this file lives one level down in
`phase3_rl/`).

- `phase1_alignment_sft/`, `phase2_reasoning_activation/` — Stage 1/2 SFT (DeepSpeed).
- `phase3_rl/` — Stage 3 GRPO RL on **verl 0.6.0** (this directory).
- `evaluation/` — inference + metrics.
