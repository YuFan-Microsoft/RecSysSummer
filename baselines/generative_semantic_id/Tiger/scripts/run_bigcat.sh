#!/usr/bin/env bash
# Full pipeline for one (large) category: embeddings -> semantic IDs ->
# 50-epoch DeepSpeed train -> beam-50 final test.
# Usage: run_bigcat.sh <HF_category> <tag>
set -u
cd "$(dirname "$0")/.."
export WANDB_API_KEY=$(cat /tmp/wk.txt)
CAT=$1; TAG=$2
EMB=outputs/cat/${TAG}_emb.pt
SID=outputs/cat/${TAG}_sid.pt

echo "######## [$TAG] STEP1 embeddings ($CAT) ########"
CUDA_VISIBLE_DEVICES=0 python src/embeddings.py --data.category $CAT \
  --data.output $EMB --model.name sentence-transformers/sentence-t5-base \
  --infer.batch_size 256

echo "######## [$TAG] STEP2 quantize rqkmeans 3x256 ########"
CUDA_VISIBLE_DEVICES=0 python src/quantize.py --data.embeddings $EMB \
  --data.output $SID --method rqkmeans --num_hierarchies 3 --codebook_width 256

echo "######## [$TAG] STEP3 train + STEP4 beam-50 test ########"
EPOCHS=50 EVAL_EVERY=10 bash scripts/run_category.sh $CAT $SID $TAG
