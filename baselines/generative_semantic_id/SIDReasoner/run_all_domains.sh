#!/bin/bash
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

# Reuse fragmented "reserved but unallocated" CUDA memory to avoid fragmentation OOM.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
D="/scratch/azureml/cr/j/3ef1a555d23d4aebbab1bbf3ab85d238/exe/wd/Amazon"
CKROOT="/yufan/open_source_models/Research_Models/SIDReasoner"
CUDA_LIST="0 1 2 3 4 5 6 7"
CUDA_CSV="0,1,2,3,4,5,6,7"

# domain | category | checkpoint-subdir | file-stem
declare -a ROWS=(
  "Video_Games|Video_Games|Games_Checkpoint|Video_Games_5_2016-10-2018-11"
  "Office_Products|Office_Products|Office_Checkpoint|Office_Products_5_2016-10-2018-11"
  "Industrial_and_Scientific|Industrial_and_Scientific|Industrial_Checkpoint|Industrial_and_Scientific_5_2016-10-2018-11"
)

for row in "${ROWS[@]}"; do
  IFS='|' read -r NAME CAT CKDIR STEM <<< "$row"
  CK="$CKROOT/$CKDIR/actor_merged"
  TEST="$D/test/${STEM}.csv"
  INFO="$D/info/${STEM}.txt"
  ITEM="$D/index/${CAT}.item.json"
  INDEX="$D/index/${CAT}.index.json"
  TMP="./temp/eval_${NAME}"
  OUT="./results/eval_${NAME}"
  mkdir -p "$TMP" "$OUT"
  echo "############ DOMAIN $NAME ############"
  date
  echo ">>> split"
  python evaluation/split.py --input_path "$TEST" --output_path "$TMP" --cuda_list "$CUDA_CSV"
  echo ">>> launch 8 GPU eval"
  for i in $CUDA_LIST; do
    if [[ -f "$TMP/$i.csv" ]]; then
      # Per-GPU compile caches: parallel GPU procs must NOT share one torch
      # inductor / triton (flash-attn) cache dir, or concurrent compiles race
      # (FileNotFoundError / AssertionError: os.path.exists(subdir)) and crash.
      mkdir -p "$TMP/.cache/gpu$i"
      CUDA_VISIBLE_DEVICES=$i \
      TRITON_CACHE_DIR="$TMP/.cache/gpu$i/triton" \
      TORCHINDUCTOR_CACHE_DIR="$TMP/.cache/gpu$i/inductor" \
      VLLM_CACHE_ROOT="$TMP/.cache/gpu$i/vllm" \
      python -u evaluation/evaluate_Qwen3_think.py \
        --base_model "$CK" --info_file "$INFO" --category "$CAT" \
        --test_data_path "$TMP/$i.csv" --item_file "$ITEM" --index_file "$INDEX" \
        --result_json_data "$TMP/$i.json" \
        --batch_size 4 --num_beams 10 --max_new_tokens 1024 --length_penalty 0.0 \
        > "$TMP/$i.log" 2>&1 &
    fi
  done
  wait
  echo ">>> merge"
  python evaluation/merge.py --input_path "$TMP" --output_path "$OUT/final_result_${NAME}.json" --cuda_list "$CUDA_CSV"
  echo ">>> calc [$NAME]"
  python evaluation/calc.py --path "$OUT/final_result_${NAME}.json" --item_path "$INFO" 2>&1 | tee "$OUT/metrics_${NAME}.txt"
  echo "############ DONE $NAME ############"
  date
done
echo "ALL DOMAINS DONE"
