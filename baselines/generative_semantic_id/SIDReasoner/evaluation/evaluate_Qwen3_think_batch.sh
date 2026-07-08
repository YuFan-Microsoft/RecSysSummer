#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# ============ CONFIGS ==============
# Please change the configs according to your environment before running this script.
cudalist="4 5 6"      # split by space
cudalist_v2="4,5,6"   # split by comma
# ===================================

exp_list=("/home/yingzhi/rec/MiniOneRec/output_dir/sft_reasoning-activation_Raw_Qwen3-1.7B_Games/final_checkpoint"
          "output_dir/sft_reasoning-activation_OringinalMiniOneRec_Qwen3-1.7B_Games/final_checkpoint"
          "output_dir/sft_reasoning-activation_7Task-General_Qwen3-1.7B_Games/checkpoint-48"
         )


{
for exp_name in "${exp_list[@]}"
do
for category in "Video_Games"
do
    # your model path
    # exp_name="output_dir/sft_reasoning-activation_7Task-End2End-GPTGen_Qwen3-1.7B-EP3_Industrial/checkpoint-72"
    dir1=$(basename "$(dirname "$exp_name")")
    dir2=$(basename "$exp_name")
    dir0=$(basename "$(dirname "$(dirname "$exp_name")")")
    exp_name_clean="${dir0}__${dir1}__${dir2}"

    echo "Processing category: $category with model: $exp_name_clean (STANDARD MODE)"
    
    train_file=$(ls ./data/Amazon/train/${category}*.csv 2>/dev/null | head -1)
    test_file=$(ls ./data/Amazon/test/${category}*.csv 2>/dev/null | head -1)
    info_file=$(ls ./data/Amazon/info/${category}*.txt 2>/dev/null | head -1)
    
    if [[ ! -f "$test_file" ]]; then
        echo "Error: Test file not found for category $category"
        continue
    fi
    if [[ ! -f "$info_file" ]]; then
        echo "Error: Info file not found for category $category"
        continue
    fi
    
    temp_dir="./temp/${category}-${exp_name_clean}"
    echo "Creating temp directory: $temp_dir"
    mkdir -p "$temp_dir"
    
    echo "Splitting test data..."
    python "$SCRIPT_DIR/split.py" --input_path "$test_file" --output_path "$temp_dir" --cuda_list ${cudalist_v2}
    
    # if [[ ! -f "$temp_dir/0.csv" ]]; then
    #     echo "Error: Data splitting failed for category $category"
    #     continue
    # fi
    
    # cudalist="4 5 6 7"  
    echo "Starting parallel evaluation (STANDARD MODE)..."
    for i in ${cudalist}
    do
        if [[ -f "$temp_dir/${i}.csv" ]]; then
            echo "Starting evaluation on GPU $i for category ${category}"
            CUDA_VISIBLE_DEVICES=$i python -u "$SCRIPT_DIR/evaluate_Qwen3_think.py" \
                --base_model "$exp_name" \
                --info_file "$info_file" \
                --category ${category} \
                --test_data_path "$temp_dir/${i}.csv" \
                --item_file ./data/Amazon/index/${category}.item.json \
                --index_file ./data/Amazon/index/${category}.index.json \
                --result_json_data "$temp_dir/${i}.json" \
                --batch_size 4 \
                --num_beams 10 \
                --max_new_tokens 1024 \
                --length_penalty 0.0 &
        else
            echo "Warning: Split file $temp_dir/${i}.csv not found, skipping GPU $i"
        fi
    done
    echo "Waiting for all evaluation processes to complete..."
    wait
    
    result_files=$(ls "$temp_dir"/*.json 2>/dev/null | wc -l)
    if [[ $result_files -eq 0 ]]; then
        echo "Error: No result files generated for category $category"
        continue
    fi
    
    output_dir="./results/${exp_name_clean}"
    echo "Creating output directory: $output_dir"
    mkdir -p "$output_dir"

    actual_cuda_list=""
    for gpu in $cudalist; do
        if [[ -f "$temp_dir/${gpu}.json" ]]; then
            actual_cuda_list="${actual_cuda_list}${gpu},"
        fi
    done
    # eliminate trailing comma
    actual_cuda_list="${actual_cuda_list%,}"

    echo "Merging results from GPUs: $actual_cuda_list"
    
    python "$SCRIPT_DIR/merge.py" \
        --input_path "$temp_dir" \
        --output_path "$output_dir/final_result_thinking_${category}.json" \
        --cuda_list "$actual_cuda_list"
    
    if [[ ! -f "$output_dir/final_result_thinking_${category}.json" ]]; then
        echo "Error: Result merging failed for category $category"
        continue
    fi
    
    echo "Calculating metrics..."
    python "$SCRIPT_DIR/calc.py" \
        --path "$output_dir/final_result_thinking_${category}.json" \
        --item_path "$info_file"
    
    echo "Completed processing for category: $category"
    echo "Results saved to: $output_dir/final_result_thinking_${category}.json"
    echo "----------------------------------------" 
done
done
echo "All categories processed!"
} > ./logs/evaluate_Qwen3_General_CDs_and_Vinyl_think_batch.log 2>&1