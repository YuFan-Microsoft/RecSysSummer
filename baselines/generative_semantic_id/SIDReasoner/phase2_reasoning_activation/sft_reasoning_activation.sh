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
NUM_EPOCHS=1
EVAL_CUDA_LIST="0,1,2,3,4,5,6,7"
EVAL_OUTPUT_DIR="${OUTPUT_DIR}/recsys_eval"
EVAL_NUM_SAMPLES=-1
WANDB_PROJECT="SIDReasoner_Phase2"
WANDB_RUN_ID="${RUN_NAME}-$(date -u +%Y%m%dT%H%M%SZ)"
PRETRAIN_METRICS="${EVAL_OUTPUT_DIR}/pretrain/metrics.json"

mkdir -p ./logs ./output_dir

run_recsys_eval() {
    local checkpoint="$1"
    local stage="$2"
    local wandb_args=()
    if [[ "${stage}" == "posttrain" ]]; then
        wandb_args=(
            --upload-to-wandb
            --wandb-project "${WANDB_PROJECT}"
            --wandb-run-name "${RUN_NAME}"
            --wandb-run-id "${WANDB_RUN_ID}"
        )
    fi
    echo "Running ${stage} recommendation evaluation for ${checkpoint}"
    python "$REPO_ROOT/evaluation/evaluate_phase2_checkpoint.py" \
        --checkpoint "${checkpoint}" \
        --category "${CATEGORY}" \
        --stage "${stage}" \
        --output-dir "${EVAL_OUTPUT_DIR}" \
        --cuda-list "${EVAL_CUDA_LIST}" \
        --num-samples "${EVAL_NUM_SAMPLES}" \
        --num-beams 10 \
        "${wandb_args[@]}"
}

{
echo "category=${CATEGORY} | base_model=${BASE_MODEL} (Stage-1 checkpoint; all data pulled from the HF dataset by --category)"
    echo "wandb_project=${WANDB_PROJECT} | wandb_run_id=${WANDB_RUN_ID}"

run_recsys_eval "${BASE_MODEL}" pretrain

# Explicit DeepSpeed launch (no HF Trainer): the training loop lives in sft_reasoning_activation.py::main.
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 deepspeed --num_gpus ${NUM_GPUS} --master_port ${MASTER_PORT} \
    "$SCRIPT_DIR/sft_reasoning_activation.py" \
    --base_model "${BASE_MODEL}" \
    --micro_batch_size 8 \
    --num_epochs "${NUM_EPOCHS}" \
    --learning_rate 1e-5 \
    --cutoff_len 1024 \
    --output_dir "${OUTPUT_DIR}" \
    --report_to wandb \
    --wandb_project "${WANDB_PROJECT}" \
    --wandb_run_name "${RUN_NAME}" \
    --wandb_run_id "${WANDB_RUN_ID}" \
    --pretrain_eval_metrics "${PRETRAIN_METRICS}" \
    --category "${CATEGORY}" \
    --seed 42 \
    --zero_stage 2 \
    --dtype bf16 \
    --deepspeed

# epoch_N is the actual model state at the end of training; final_checkpoint is
# the loss-best convenience copy and may point to an earlier epoch.
POSTTRAIN_MODEL="${OUTPUT_DIR}/epoch_${NUM_EPOCHS}"
if [[ ! -d "${POSTTRAIN_MODEL}" ]]; then
    echo "Error: post-training checkpoint not found at ${POSTTRAIN_MODEL}"
    exit 1
fi
run_recsys_eval "${POSTTRAIN_MODEL}" posttrain
} > "${LOG_FILE}" 2>&1
