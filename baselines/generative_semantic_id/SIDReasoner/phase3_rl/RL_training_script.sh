#!/bin/bash

# ============================================================================
# Phase-3 RL training — uses verl v0.6.0 (+ SID Reasoner patches).
#
# Referencing model:
#   `verl` is a top-level package dir at the repo root, so the standard
#   `cd $REPO_ROOT` + `python -m verl.trainer.main_ppo` picks it up.
# ============================================================================

# Tested target image family: verlai/verl:base-verl0.6-cu128-...-torch2.8.0 + vllm 0.10.2
# export NCCL_P2P_DISABLE=1       # 禁用 NVLink
# export NCCL_IB_DISABLE=1        # 禁用 InfiniBand
# export NCCL_NET_GDR_LEVEL=0     # 禁用 GDR（GPU直连）
# export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7

set -euo pipefail
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# NOTE: do NOT set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True here.
# vLLM's sleep/wake (free_cache_engine=True) uses the CuMemAllocator (CUDA VMM),
# which is incompatible with expandable_segments and crashes rollout. Leave the
# default caching allocator for the vLLM-backed training.

# W&B auth. Use the env var (NOT `wandb.login(key=...)`): verl runs rollout in
# Ray workers / subprocesses, so a main-process wandb.login() won't propagate.
# WANDB_API_KEY is auto-picked-up by wandb and forwarded to workers by Ray.
export WANDB_API_KEY=3f14084582ffbf0986b305f813aea34ca59c77c5

# ================================
# Note: please change the number of GPUs and nodes according to your setup.
# ================================
n_gpus_per_node=8
nnodes=1
experiment_name="Video_Games_stage3_rl_Qwen3-1.7B"
stage2_checkpoint="./output_dir/Video_Games_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint"
# Keep Phase-3 checkpoints alongside Phase-1/2 under ./output_dir. verl otherwise
# defaults to ./checkpoints/${project_name}/${experiment_name}; overriding
# trainer.default_local_dir below unifies all three stages under output_dir/.
checkpoint_dir="./output_dir/${experiment_name}"
log_file="./logs/${experiment_name}.log"
# ================================

mkdir -p ./logs

{
python3 -m verl.trainer.main_ppo \
    algorithm.adv_estimator=grpo \
    data.train_files=./data/Amazon/rec_reasoning_verl/Video_Games/train.parquet \
    data.val_files=./data/Amazon/rec_reasoning_verl/Video_Games/test.parquet \
    data.train_batch_size=256 \
    data.max_prompt_length=1024 \
    data.max_response_length=1024 \
    data.filter_overlong_prompts=True \
    data.truncation='error' \
    actor_rollout_ref.model.path="${stage2_checkpoint}" \
    actor_rollout_ref.actor.optim.lr=5e-7 \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.actor.ppo_mini_batch_size=256 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=8 \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.kl_loss_coef=0.001 \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.actor.entropy_coeff=0 \
    actor_rollout_ref.model.enable_gradient_checkpointing=True \
    actor_rollout_ref.actor.fsdp_config.param_offload=False \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=False \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=8 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.8 \
    actor_rollout_ref.rollout.n=16 \
    +actor_rollout_ref.rollout.sid_constrained_beam_size=10 \
    +actor_rollout_ref.rollout.sid_category=Video_Games \
    +actor_rollout_ref.rollout.sid_length=3 \
    actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=8 \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    algorithm.use_kl_in_reward=False \
    trainer.critic_warmup=0 \
    trainer.logger=['console','wandb'] \
    custom_reward_function.path="./verl/utils/reward_score/direct_recommendation_StepRule_Games.py" \
    custom_reward_function.name="rule_base_reward" \
    trainer.project_name='SIDReasoner_Phase3_MetricsV2' \
    trainer.experiment_name="${experiment_name}" \
    trainer.default_local_dir="${checkpoint_dir}" \
    trainer.n_gpus_per_node=$n_gpus_per_node \
    trainer.nnodes=$nnodes \
    trainer.save_freq=100 \
    trainer.test_freq=50 \
    trainer.total_epochs=10 "$@"
} > "${log_file}" 2>&1
