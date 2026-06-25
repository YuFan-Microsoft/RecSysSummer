#!/usr/bin/env bash
# Parallel config sweep: one single-GPU run per GPU. One wandb project,
# distinct run name per config. Each row: id|sids|lr|wd|dropout|mlp|gpu
set -u
cd "$(dirname "$0")/.."
export WANDB_API_KEY=$(cat /tmp/wk.txt)
PROJECT=tiger-grid-sweep
CAT=Musical_Instruments
EPOCHS=30
mkdir -p /tmp/sweep outputs/ckpts

# id  sids  lr  wd  dropout  mlp  gpu
CONFIGS=(
 "A1_rqkmeans_3x256_paper  rqkmeans_3x256  5e-4  1e-6  0.15  2  0"
 "A2_rvq_3x256_paper       rvq_3x256       5e-4  1e-6  0.15  2  1"
 "A3_rqvae_3x256_paper     rqvae_3x256     5e-4  1e-6  0.15  2  2"
 "B1_rqkmeans_3x128_paper  rqkmeans_3x128  5e-4  1e-6  0.15  2  3"
 "B2_rqkmeans_4x256_paper  rqkmeans_4x256  5e-4  1e-6  0.15  2  4"
 "C1_rqkmeans_3x256_lr1e-3 rqkmeans_3x256  1e-3  1e-4  0.15  2  5"
 "C2_rqkmeans_3x256_drop01 rqkmeans_3x256  5e-4  1e-6  0.10  2  6"
 "C3_rqkmeans_3x256_mlp0   rqkmeans_3x256  5e-4  1e-6  0.15  0  7"
)

for cfg in "${CONFIGS[@]}"; do
  read -r ID SID LR WD DROP MLP GPU <<< "$cfg"
  echo "launching $ID on GPU $GPU"
  CUDA_VISIBLE_DEVICES=$GPU nohup python src/train_tiger.py \
     --data.category $CAT \
     --data.semantic_ids outputs/sids/${SID}.pt \
     --ckpt.output outputs/ckpts/${ID}.pt \
     --train.epochs $EPOCHS --train.batch_size 256 \
     --train.lr $LR --train.weight_decay $WD \
     --model.dropout $DROP --model.mlp_layers $MLP \
     --eval.every 3 --eval.beam_size 10 --eval.ks 10,5 \
     --logger.wandb.enable 1 --logger.wandb.project $PROJECT \
     --logger.wandb.run_name $ID \
     > /tmp/sweep/${ID}.log 2>&1 &
  echo "  pid $!"
  sleep 8
done
wait
echo "ALL SWEEP RUNS DONE"
