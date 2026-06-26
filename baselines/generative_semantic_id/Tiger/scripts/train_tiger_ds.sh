#!/usr/bin/env bash
# Single-node 8-GPU TIGER training with DeepSpeed (ZeRO-2 + bf16).
# Run from the Tiger/ directory:  bash scripts/train_tiger_ds.sh
# (Save this file with LF line endings.)
set -e

# ---- wandb ----
# Put your key here, or export WANDB_API_KEY before running this script.
: "${WANDB_API_KEY:=3f14084582ffbf0986b305f813aea34ca59c77c5}"
export WANDB_API_KEY

deepspeed --num_gpus 8 src/train_tiger_ds.py \
    --data.category Beauty_and_Personal_Care \
    --data.semantic_ids outputs/semantic_ids.pt \
    --ckpt.output outputs/tiger.pt \
    --train.epochs 30 \
    --train.micro_batch_size 256 \
    --train.grad_accum 1 \
    --train.lr 5e-4 \
    --train.weight_decay 1e-6 \
    --model.dropout 0.1 \
    --eval.every 5 \
    --eval.beam_size 10 \
    --eval.test_beam_size 50 \
    --eval.ks 5,10 \
    --ds.zero_stage 2 \
    --ds.param_dtype bf16 \
    --logger.logging_steps 50 \
    --logger.wandb.key "${WANDB_API_KEY}" \
    --logger.wandb.project tiger \
    --logger.wandb.run_name tiger_beauty_8gpu
