#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

CATEGORY="Office_Products"
TEST_FILE="./data/Amazon/test/Office_Products_5_2016-10-2018-11.csv"
INFO_FILE="./data/Amazon/info/Office_Products_5_2016-10-2018-11.txt"
ITEM_FILE="./data/Amazon/index/Office_Products.item.json"
INDEX_FILE="./data/Amazon/index/Office_Products.index.json"
CUDA_LIST="0 1 2 3 4 5 6 7"
CUDA_LIST_CSV="0,1,2,3,4,5,6,7"

STAGE2_MODEL="./output_dir/Office_Products_stage2_reasoning_activation_Qwen3-1.7B/final_checkpoint"
# Stage-3 RL checkpoint to evaluate. Point this at a merged actor_merged/ dir, e.g.
#   ./output_dir/Office_Products_stage3_rl_Qwen3-1.7B/global_step_300/actor_merged
# (merge raw actor/ shards first via phase3_rl/merge_fsdp_ckpt_ALL.sh).
# Leave empty to skip Stage-3 and evaluate only Stage-2.
STAGE3_MODEL=""

exp_list=()

if [[ -d "${STAGE2_MODEL}" ]]; then
    exp_list+=("${STAGE2_MODEL}")
else
    echo "Warning: Stage 2 checkpoint not found at ${STAGE2_MODEL}"
fi

if [[ -n "${STAGE3_MODEL}" ]]; then
    if [[ -d "${STAGE3_MODEL}" ]]; then
        exp_list+=("${STAGE3_MODEL}")
    else
        echo "Warning: Stage 3 checkpoint not found at ${STAGE3_MODEL}"
    fi
fi

if [[ ${#exp_list[@]} -eq 0 ]]; then
    echo "Error: No preset Stage 2 or Stage 3 checkpoint available for evaluation."
    exit 1
fi

# Test data is fetched from the Hugging Face dataset (hf_data.py) at runtime,
# so a local TEST_FILE is optional; it is only used as a category locator.
if [[ ! -f "${TEST_FILE}" ]]; then
    echo "Note: local TEST_FILE not found; will stream test data from Hugging Face."
fi
if [[ ! -f "${INFO_FILE}" ]]; then
    echo "Note: local INFO_FILE not found; will build the SID map from Hugging Face."
fi

for exp_name in "${exp_list[@]}"
do
    dir1=$(basename "$(dirname "$exp_name")")
    dir2=$(basename "$exp_name")
    dir0=$(basename "$(dirname "$(dirname "$exp_name")")")
    exp_name_clean="${dir0}__${dir1}__${dir2}"

    echo "Processing category: ${CATEGORY} with model: ${exp_name_clean} (STANDARD MODE)"

    temp_dir="./temp/${CATEGORY}-${exp_name_clean}"
    echo "Creating temp directory: ${temp_dir}"
    mkdir -p "${temp_dir}"

    echo "Splitting test data..."
    python "$SCRIPT_DIR/split.py" --input_path "${TEST_FILE}" --output_path "${temp_dir}" --cuda_list "${CUDA_LIST_CSV}"

    echo "Starting parallel evaluation (STANDARD MODE)..."
    for i in ${CUDA_LIST}
    do
        if [[ -f "${temp_dir}/${i}.csv" ]]; then
            echo "Starting evaluation on GPU ${i} for category ${CATEGORY}"
            # Per-GPU compile caches: parallel GPU procs must NOT share one torch
            # inductor / triton (flash-attn) cache dir, or concurrent compiles race
            # (FileNotFoundError / AssertionError: os.path.exists(subdir)) and crash.
            mkdir -p "${temp_dir}/.cache/gpu${i}"
            CUDA_VISIBLE_DEVICES=${i} \
            TRITON_CACHE_DIR="${temp_dir}/.cache/gpu${i}/triton" \
            TORCHINDUCTOR_CACHE_DIR="${temp_dir}/.cache/gpu${i}/inductor" \
            VLLM_CACHE_ROOT="${temp_dir}/.cache/gpu${i}/vllm" \
            python -u "$SCRIPT_DIR/evaluate_Qwen3_think.py" \
                --base_model "${exp_name}" \
                --info_file "${INFO_FILE}" \
                --category "${CATEGORY}" \
                --test_data_path "${temp_dir}/${i}.csv" \
                --item_file "${ITEM_FILE}" \
                --index_file "${INDEX_FILE}" \
                --result_json_data "${temp_dir}/${i}.json" \
                --batch_size 32 \
                --num_beams 10 \
                --max_new_tokens 1024 \
                --length_penalty 0.0 &
        else
            echo "Warning: Split file ${temp_dir}/${i}.csv not found, skipping GPU ${i}"
        fi
    done
    echo "Waiting for all evaluation processes to complete..."
    wait

    result_files=$(find "${temp_dir}" -maxdepth 1 -name '*.json' | wc -l)
    if [[ ${result_files} -eq 0 ]]; then
        echo "Error: No result files generated for category ${CATEGORY}"
        continue
    fi

    output_dir="./results/${exp_name_clean}"
    echo "Creating output directory: ${output_dir}"
    mkdir -p "${output_dir}"

    actual_cuda_list=""
    for gpu in ${CUDA_LIST}; do
        if [[ -f "${temp_dir}/${gpu}.json" ]]; then
            actual_cuda_list="${actual_cuda_list}${gpu},"
        fi
    done
    actual_cuda_list="${actual_cuda_list%,}"

    echo "Merging results from GPUs: ${actual_cuda_list}"

    python "$SCRIPT_DIR/merge.py" \
        --input_path "${temp_dir}" \
        --output_path "${output_dir}/final_result_thinking_${CATEGORY}.json" \
        --cuda_list "${actual_cuda_list}"

    if [[ ! -f "${output_dir}/final_result_thinking_${CATEGORY}.json" ]]; then
        echo "Error: Result merging failed for category ${CATEGORY}"
        continue
    fi

    echo "Calculating metrics..."
    python "$SCRIPT_DIR/calc.py" \
        --path "${output_dir}/final_result_thinking_${CATEGORY}.json" \
        --item_path "${INFO_FILE}"

    echo "Completed processing for category: ${CATEGORY}"
    echo "Results saved to: ${output_dir}/final_result_thinking_${CATEGORY}.json"
    echo "----------------------------------------"
done

echo "All categories processed!"
