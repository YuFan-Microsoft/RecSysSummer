#!/usr/bin/env bash
# Train the best config on one category (8-GPU DeepSpeed), then final beam-50 test.
# Usage: run_category.sh <HF_category> <sid_path> <tag>
set -u
cd "$(dirname "$0")/.."
export WANDB_API_KEY=$(cat /tmp/wk.txt)
CAT=$1; SID=$2; TAG=$3
PROJECT=tiger-allcat
CKPT=outputs/cat/${TAG}_best.pt
EPOCHS=${EPOCHS:-50}
EVAL_EVERY=${EVAL_EVERY:-5}

echo "######## TRAIN $TAG ($CAT) epochs=$EPOCHS ########"
deepspeed --num_gpus 8 src/train_tiger_ds.py \
  --data.category $CAT --data.semantic_ids $SID --ckpt.output $CKPT \
  --train.epochs $EPOCHS --train.micro_batch_size 256 \
  --train.lr 5e-4 --train.weight_decay 1e-6 \
  --model.dropout 0.1 --model.mlp_layers 2 \
  --eval.every $EVAL_EVERY --eval.beam_size 10 --eval.ks 10,5 \
  --logger.wandb.enable 1 --logger.wandb.project $PROJECT --logger.wandb.run_name ${TAG}_train

echo "######## FINAL TEST (beam=50) $TAG ########"
CUDA_VISIBLE_DEVICES=0 python src/train_tiger.py --eval_only \
  --data.category $CAT --data.semantic_ids $SID --ckpt.output $CKPT \
  --model.dropout 0.1 --model.mlp_layers 2 \
  --eval.beam_size 50 --eval.ks 10,5 --logger.wandb.enable 0
echo "######## DONE $TAG ########"
