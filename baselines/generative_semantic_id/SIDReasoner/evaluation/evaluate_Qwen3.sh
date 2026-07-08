#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Reuse fragmented "reserved but unallocated" CUDA memory to avoid fragmentation OOM.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

CATEGORY="Office_Products"
EXP_NAME="./output_dir/Office_Products_stage1_sft_Qwen3-1.7B/final_checkpoint"
TEST_FILE="./data/Amazon/test/Office_Products_5_2016-10-2018-11.csv"
INFO_FILE="./data/Amazon/info/Office_Products_5_2016-10-2018-11.txt"
CUDA_LIST="0 1"
CUDA_LIST_CSV="0,1"

dir1=$(basename "$(dirname "$EXP_NAME")")
dir2=$(basename "$EXP_NAME")
exp_name_clean="${dir1}__${dir2}"

echo "Processing category: ${CATEGORY} with model: ${exp_name_clean} (STANDARD MODE)"

# Test data is fetched from the Hugging Face dataset (hf_data.py) at runtime,
# so a local TEST_FILE is optional; it is only used as a category locator.
if [[ ! -f "${TEST_FILE}" ]]; then
    echo "Note: local TEST_FILE not found; will stream test data from Hugging Face."
fi
if [[ ! -f "${INFO_FILE}" ]]; then
    echo "Note: local INFO_FILE not found; will build the SID map from Hugging Face."
fi

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
        CUDA_VISIBLE_DEVICES=${i} python -u "$SCRIPT_DIR/evaluate_Qwen3.py" \
            --base_model "${EXP_NAME}" \
            --info_file "${INFO_FILE}" \
            --category "${CATEGORY}" \
            --test_data_path "${temp_dir}/${i}.csv" \
            --result_json_data "${temp_dir}/${i}.json" \
            --batch_size 8 \
            --num_beams 10 \
            --max_new_tokens 256 \
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
    exit 1
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
    --output_path "${output_dir}/final_result_${CATEGORY}.json" \
    --cuda_list "${actual_cuda_list}"

if [[ ! -f "${output_dir}/final_result_${CATEGORY}.json" ]]; then
    echo "Error: Result merging failed for category ${CATEGORY}"
    exit 1
fi

echo "Calculating metrics..."
python "$SCRIPT_DIR/calc.py" \
    --path "${output_dir}/final_result_${CATEGORY}.json" \
    --item_path "${INFO_FILE}"

echo "Completed processing for category: ${CATEGORY}"
echo "Results saved to: ${output_dir}/final_result_${CATEGORY}.json"
echo "All categories processed!"
