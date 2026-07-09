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

## Data source (Hugging Face, NOT local)

Like Phase‑1/2, **all Phase‑3 data comes from your Hugging Face dataset
`yufan/recsys-genrec-dataset`, never from local disk.** The verl parquet files the RL
script reads (`./data/Amazon/rec_reasoning_verl/<domain>/{train,test}.parquet`) are a
one‑time **materialization from HF**: [`create_reasoning_rl_data.py`](create_reasoning_rl_data.py)
loads the source splits with `hf_data.load_df(...)` and writes them out in verl format.
The `./data/...` strings are just locators / output targets, **not** tracked local data —
run that script (which pulls from HF) once per domain before launching RL; do not create
or hand‑edit local data files.

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
