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
# expandable segments. This avoids mid-epoch OOM on the long (3072-token)
# general-reasoning batches without touching micro_batch_size / LR / global batch.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# TEMP: point Phase-1 at the refreshed GPT-5.4 dataset (revert to yufan/recsys-genrec-dataset).
export SIDR_HF_REPO="${SIDR_HF_REPO:-yufan/recsys-genrec-dataset-refresh-gpt5.4}"

BASE_MODEL="Qwen/Qwen3-1.7B"
NUM_GPUS=8
MASTER_PORT=12340

# The three independent domains, each with its own SID codebook. --category is the
# single data knob: train/eval/catalog/reasoning are loaded directly from the matching
# Hugging Face configs. Train ONE domain at a time.
#
# Default: run all three, in sequence. To train a subset, pass category names, e.g.
#   bash phase1_alignment_sft/sft_Qwen3_enrich.sh Video_Games
#   bash phase1_alignment_sft/sft_Qwen3_enrich.sh Office_Products Industrial_and_Scientific
DEFAULT_CATEGORIES=(Video_Games Office_Products Industrial_and_Scientific)
if [ "$#" -gt 0 ]; then
    CATEGORIES=("$@")
else
    CATEGORIES=("${DEFAULT_CATEGORIES[@]}")
fi

mkdir -p ./logs ./output_dir

for CATEGORY in "${CATEGORIES[@]}"; do
    RUN_NAME="${CATEGORY}_stage1_sft_Qwen3-1.7B"
    OUTPUT_DIR="./output_dir/${RUN_NAME}"
    LOG_FILE="./logs/${RUN_NAME}.txt"

    echo "==== [Stage-1] START domain=${CATEGORY} -> ${OUTPUT_DIR} (log: ${LOG_FILE}) ===="

    {
    echo "category=${CATEGORY} | base_model=${BASE_MODEL} (all data pulled from the HF dataset by --category)"

    # Explicit DeepSpeed launch (no HF Trainer): the training loop lives in sft_Qwen3.py::main.
    CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 deepspeed --num_gpus ${NUM_GPUS} --master_port ${MASTER_PORT} \
        "$SCRIPT_DIR/sft_Qwen3.py" \
        --base_model "${BASE_MODEL}" \
        --micro_batch_size 8 \
        --num_epochs 5 \
        --early_stopping_patience 2 \
        --learning_rate 2e-5 \
        --cutoff_len 1024 \
        --output_dir "${OUTPUT_DIR}" \
        --report_to wandb \
        --wandb_project SIDReasoner_Phase1 \
        --wandb_run_name "${RUN_NAME}" \
        --category "${CATEGORY}" \
        --seed 42 \
        --mask_assistant True \
        --zero_stage 2 \
        --dtype bf16 \
        --gradient_checkpointing \
        --deepspeed
    } > "${LOG_FILE}" 2>&1

    echo "==== [Stage-1] DONE  domain=${CATEGORY} ===="
done

echo "==== [Stage-1] all domains finished: ${CATEGORIES[*]} ===="

