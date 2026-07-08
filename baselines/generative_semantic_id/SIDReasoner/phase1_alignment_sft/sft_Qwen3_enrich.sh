#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

export NCCL_P2P_DISABLE=1
export NCCL_IB_DISABLE=1
export NCCL_NET_GDR_LEVEL=0

CATEGORY="Office_Products"
BASE_MODEL="Qwen/Qwen3-1.7B"
TRAIN_FILE="./data/Amazon/train/Office_Products_5_2016-10-2018-11.csv"
EVAL_FILE="./data/Amazon/valid/Office_Products_5_2016-10-2018-11.csv"
TEST_FILE="./data/Amazon/test/Office_Products_5_2016-10-2018-11.csv"
INFO_FILE="./data/Amazon/info/Office_Products_5_2016-10-2018-11.txt"
OUTPUT_DIR="./output_dir/Office_Products_stage1_sft_Qwen3-1.7B"
RUN_NAME="Office_Products_stage1_sft_Qwen3-1.7B"
LOG_FILE="./logs/${RUN_NAME}.txt"

mkdir -p ./logs ./output_dir

{
echo "${TRAIN_FILE} ${EVAL_FILE} ${INFO_FILE} ${TEST_FILE}"

CUDA_VISIBLE_DEVICES=0,1,2,3 torchrun --nproc_per_node 4 \
    --master_port 12340 \
    "$SCRIPT_DIR/sft_Qwen3.py" \
    --base_model "${BASE_MODEL}" \
    --batch_size 1024 \
    --micro_batch_size 1 \
    --train_file "${TRAIN_FILE}" \
    --eval_file "${EVAL_FILE}" \
    --output_dir "${OUTPUT_DIR}" \
    --wandb_project MiniOneRec \
    --wandb_run_name "${RUN_NAME}" \
    --category "${CATEGORY}" \
    --train_from_scratch False \
    --seed 42 \
    --sid_index_path "./data/Amazon/index/${CATEGORY}.index.json" \
    --item_meta_path "./data/Amazon/index/${CATEGORY}.item.json" \
    --llm_generated_data_path "./data/Amazon/index/${CATEGORY}.item_enhanced_v2.json" \
    --llm_generated_sequence_path "./data/Amazon/index/${CATEGORY}.integrated_narrative.csv" \
    --general_reasoning_path "./data/Amazon/general/sampled_data.arrow" \
    --mask_assistant True
} > "${LOG_FILE}" 2>&1
