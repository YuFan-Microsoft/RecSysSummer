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

### Constrained sampling with process reward

Training samples one catalog-valid SID per reasoning. The primary reward remains
the pure sampled-SID exact match. Process supervision follows the same two stages
used to construct the Phase-2 V4 traces:

```text
process_reward = 1 if strict_format_valid
          and all_citations_are_from_history
          and latest_history_sid_is_cited_in_history_summary
        else 0
```

`format_reward` is `1` only when the text before the single `</think>` marker has
exactly one `<history_summary>...</history_summary>` block followed by one
`<future_interests>...</future_interests>` block, with no surrounding text.
History summaries require 1-3 valid `- SID[, SID...] => text` lines. Future
interests require 2-4 valid `- [exploit|explore] SID[, SID...] => text` lines and
at least one of each mode. Any violation makes the strict format reward `0`.

Grounding is computed separately for the two stages as the fraction of lines
whose complete leading citation list belongs to the real history. The final
`process_reward` has a hard validity gate: any format violation or any line with
a non-history citation makes it `0`; only a strict-format trace with every cited
SID grounded in history and the latest history SID cited in `history_summary`
receives `1`. Citing the latest SID only in `future_interests` does not satisfy
the gate. The component grounding and latest-reference scores retain their
values for diagnostics and logging.
`history_reference_coverage` is the fraction of unique history SIDs referenced
at least once across both stages; it is monitoring-only and does not enter the
process advantage. Repeated citations are allowed, but multiple citations must
be comma separated to match the V4 data contract.

These online rules intentionally do not claim to verify semantic factuality,
whether an exploit is truly instantiated, or whether an explore bridge is
meaningful: the reward path has history SIDs but no trustworthy item metadata or
semantic judge. Those properties are taught by the reviewed Phase-2 V4 traces;
the online process reward enforces their observable schema and grounding proxies.

SID and process advantages are normalized separately. SID advantage trains both
reasoning and sampled SID tokens. Process advantage is multiplied by `0.1` and
trains reasoning tokens only, so process quality cannot reinforce an incorrect
SID action. Thinking format is logged as one strict `format_reward` metric;
history-summary grounding, future-interests grounding, history-reference
coverage, and combined process metrics remain separate.

### Retrieval-grounded interest reward

Use [`RL_training_script_interest_reward_no_kl.sh`](RL_training_script_interest_reward_no_kl.sh)
for the treatment run. It health-checks the external single-GPU retriever before
delegating to the baseline No-KL launcher. Defaults are `K=50` and weight `0.1`:

```bash
INTEREST_REWARD_TOP_K=50 \
INTEREST_REWARD_WEIGHT=0.1 \
bash phase3_rl/RL_training_script_interest_reward_no_kl.sh
```

The default endpoint is hardcoded as
`https://86c9a1ebd964c9e188.gradio.live/v1/rank/batch`. Set
`INTEREST_REWARD_ENDPOINT` only to
override it intentionally.

For every strict-format rollout, the trainer extracts pure text after each
future-interest `=>`, sends `interest + target_sid` pairs through
`POST /v1/rank/batch`, and receives 1-based Top-100 ranks (`-1` for a miss). The
best positive rank in the rollout becomes a binary reward under the configured
K. Malformed traces skip retrieval and receive zero.

Interest reward uses standard signed GRPO normalization within each 16-rollout
prompt group. Its weighted advantage is applied only to
`future_interest_token_mask`, never to history-summary or final SID tokens. Keep
the SID and process advantages independent:

```text
A = A_sid + 0.1 * A_process + interest_weight * A_interest
```

The trainer logs hit rates and active-group rates at K=10/20/50/100 from the
same Top-100 calls, plus selected-K all-zero/all-one rates, query count, strict
format rate, and token-mask coverage. Endpoint errors are fatal after bounded
retry; do not reinterpret service failures as reward zero.

Periodic validation gives each user history one vote: a history is an interest
hit when any generated interest retrieves its target SID. W&B logs overall
history HR at K=20/50/100, format-valid rate, mean query count, and interest-only
incremental coverage against constrained SID beam@10 at the same cutoffs.
Derivable intersections/unions and exploit/explore or novel/repeat breakdowns
are intentionally omitted.

Malformed parser output is not a service failure: it generates no rank request,
records block rank `-1`, and assigns raw interest reward `0` without stopping
training. Its future-interest mask is excluded from the auxiliary advantage, so
it receives neither a positive nor negative interest-token update. An
empty/unlocatable interest token mask also zeros that sample's interest score
instead of raising.

W&B uses a strict allowlist rather than forwarding every VERL metric. The
dashboard keeps recommendation outcomes (HR/NDCG at 1, 5, and 10), all process
gate diagnostics, retry-attempt metrics when retry sampling is enabled, final
active/all-wrong rates, actor entropy, policy loss, clip fraction, policy KL,
gradient norm, learning rate, and compact response-length health metrics.
Redundant aliases, prefix-match diagnostics, HR/NDCG@3, prompt-length statistics,
and detailed timing/performance metrics stay available in console logging but are
not uploaded to W&B.

The results below were produced before the V4 process-reward redesign. Keep them
as legacy V3 baselines; rerun both variants before attributing any result to the
V4 reward definition.

Observed legacy final recommendation results:

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
`trainer.experiment_name=Video_Games_stage3_rl_constrained_sid_sampling_process_reward_no_kl_Qwen3-1.7B`
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
