#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1
export NCCL_NET_GDR_LEVEL=0

# Let the CUDA allocator reuse fragmented "reserved but unallocated" memory via
# expandable segments (same fix as Stage-1), avoiding mid-epoch OOM on long
# reasoning batches without touching micro_batch_size / LR / global batch.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

CATEGORY="Video_Games"
BASE_MODEL="./output_dir/Video_Games_stage1_sft_Qwen3-1.7B/final_checkpoint"
OUTPUT_DIR="./output_dir/Video_Games_stage2_reasoning_activation_Qwen3-1.7B"
RUN_NAME="Video_Games_stage2_reasoning_activation_Qwen3-1.7B"
LOG_FILE="./logs/${RUN_NAME}.txt"

NUM_GPUS=8
MASTER_PORT=29519

mkdir -p ./logs ./output_dir

{
echo "category=${CATEGORY} | base_model=${BASE_MODEL} (Stage-1 checkpoint; all data pulled from the HF dataset by --category)"

# Explicit DeepSpeed launch (no HF Trainer): the training loop lives in sft_reasoning_activation.py::main.
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 deepspeed --num_gpus ${NUM_GPUS} --master_port ${MASTER_PORT} \
    "$SCRIPT_DIR/sft_reasoning_activation.py" \
    --base_model "${BASE_MODEL}" \
    --micro_batch_size 8 \
    --num_epochs 1 \
    --learning_rate 1e-5 \
    --cutoff_len 1024 \
    --output_dir "${OUTPUT_DIR}" \
    --report_to wandb \
    --wandb_project SIDReasoner_Phase2 \
    --wandb_run_name "${RUN_NAME}" \
    --category "${CATEGORY}" \
    --seed 42 \
    --zero_stage 2 \
    --dtype bf16 \
    --deepspeed
} > "${LOG_FILE}" 2>&1
