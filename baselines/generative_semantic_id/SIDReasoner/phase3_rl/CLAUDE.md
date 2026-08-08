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

The default launcher is
[`RL_training_script_no_kl.sh`](RL_training_script_no_kl.sh). It runs Stage-3 GRPO
without reference-policy KL regularization on **verl 0.6.0** (`verl` is a top-level
package dir at the repo root; launch is the standard
`python -m verl.trainer.main_ppo`).

[`RL_training_script.sh`](RL_training_script.sh) retains the original KL-regularized
configuration for reproduction and ablation only; do not use it as the default.

Launch it from the **repo root** with the model path above. **Always launch with
`nohup … &`** so the long RL run survives SSH disconnects / terminal hangups (the
script already writes its own training log via `> "${log_file}" 2>&1`):

```bash
mkdir -p logs   # nohup's redirect target must exist before launch
nohup bash phase3_rl/RL_training_script_no_kl.sh \
    actor_rollout_ref.model.path=/yufan/checkpoint_backup/Video_Games_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint \
    > logs/phase3_launch.out 2>&1 &
```

The script forwards trailing args (`"$@"`) to `python -m verl.trainer.main_ppo`,
and Hydra applies last-wins overrides, so the `model.path` above overrides the
script's default checkpoint.

## Default algorithm choice: No-KL

Use **No-KL GRPO** for Stage-3 by default. The launcher explicitly sets both KL
switches to false:

```text
actor_rollout_ref.actor.use_kl_loss=False
algorithm.use_kl_in_reward=False
```

With both switches disabled, verl does not register a `RefPolicy` worker, does not
compute reference-policy log probabilities, does not add KL to the actor loss, and
passes the custom rule-based reward directly into GRPO advantage estimation.

Observed final recommendation results:

| Variant | Office_Products NDCG@10 / R@10 | Video_Games NDCG@10 / R@10 | Industrial_and_Scientific NDCG@10 / R@10 |
| --- | --- | --- | --- |
| **No-KL** | **0.1132 / 0.1572** | 0.0481 / 0.0957 | **0.1050 / 0.1498** |
| KL | 0.1121 / 0.1562 | **0.0492 / 0.0965** | 0.1039 / 0.1480 |

Across the three domains, No-KL wins 4 of 6 reported metrics. Its macro averages are
0.08877 NDCG@10 and 0.13423 R@10, compared with 0.08840 and 0.13357 for KL. These
single-run differences support treating recommendation quality as **comparable, with
a small average advantage for No-KL**, rather than claiming statistical significance.
No-KL also reduced measured training time by approximately **30%**. Therefore, No-KL
is the default because it preserves performance while materially improving training
efficiency; use the KL script only when an experiment specifically requires that
ablation.

### Domain: Video_Games (script default)

The script **defaults to the `Video_Games` domain end‑to‑end** — data, reward, and the
**wandb run name** all match the Games checkpoint above. Concretely the script sets
`trainer.experiment_name=Video_Games_stage3_rl_constrained_sid_single_sample_no_kl_Qwen3-1.7B`
(this is the wandb run
name, under project `SIDReasoner_Phase3_MetricsV2`), `data.*=.../Video_Games/*.parquet`, and
`custom_reward_function.path=.../direct_recommendation_StepRule_Games.py`. So the
launch command above is all you need — you do **not** have to override data / reward /
wandb.

To run a **different** domain, override its four knobs **and keep the wandb run name in
sync** so the experiment is labeled by its real domain, e.g. for Office_Products:

```bash
nohup bash phase3_rl/RL_training_script_no_kl.sh \
    actor_rollout_ref.model.path=./output_dir/Office_Products_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint \
  trainer.experiment_name=Office_Products_stage3_rl_no_kl_Qwen3-1.7B \
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
2. **RL training** — `RL_training_script_no_kl.sh` feeds those parquet to verl GRPO;
  the **reward function** then scores rollouts online, itself reading one more HF
  config.

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

### C · Constrained SID rollout and reward

The vLLM rollout worker loads the selected domain's catalog and builds a token-level
**SID prefix trie**:

| Loads | HF config | Column(s) used |
| --- | --- | --- |
| `hf_data.load_sid_indices(sid_category)` | `<cat>_catalog` (train) | `sid_tokens` |

- Each of the 16 GRPO rollouts samples one reasoning, discards the sampled suffix after
  `</think>`, then samples one three-token SID path. At each position, `allowed_token_ids`
  contains only catalog-valid continuations, so the sampled SID is a real catalog path.
- Training reward is exact match only. Standard prompt-level GRPO compares the 16 complete
  `reasoning + SID` trajectories and broadcasts each trajectory's advantage to both spans.
- SID old/new log probabilities are normalized over the trie-allowed actions, so all three
  sampled SID tokens contribute actor gradients. The normalized separator and EOS remain
  outside the actor loss.
- Validation remains deterministic reasoning followed by catalog-constrained beam-10 and logs
  HR/NDCG@1/3/5/10, so the final evaluator is unchanged.

### D · Bounded all-wrong retry

The no-KL launcher gives each prompt at most three total constrained-sampling attempts.
After the first 16-trajectory group, prompts with mixed exact-match rewards are retained
once, all-correct prompts are discarded without retry, and only all-wrong prompts are
sampled again. A prompt stops retrying as soon as it produces an active group, and outputs
from uniform attempts are never merged into the retained group.

Retries stay within the original 256-prompt dataloader batch and never consume the next
prompt batch. After the third attempt, the trainer updates on however many unique active
groups were accumulated. The count is rounded down only to the multiple required for full
distributed micro-batches; with 8 actor workers, `rollout.n=16`, and micro-batch size 8,
that multiple is four groups. For example, 59 raw active groups become 56 selected groups.
The actor retains the original fixed 256-prompt PPO normalization rather than renormalizing
by the smaller active batch. Consequently, a 56-group update contributes proportionally less
gradient than a full 256-group update.

W&B logs the active rate for each attempted round and the cumulative unique active rate after
bounded retry. If fewer than four prompts become active, the trainer fails explicitly instead
of applying an empty or partial distributed micro-batch.

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
