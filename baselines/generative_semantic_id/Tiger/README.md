# TIGER — Generative Recommendation with Semantic IDs

A small, readable PyTorch reimplementation of TIGER. Data is read straight from
the Hub, so there are no local data files to prepare. Run four steps in order.

## Setup

```bash
pip install -r requirements.txt
```

## Data (from HuggingFace, no download step needed)

- Items: [`yufan/amazon2023-item-metadata`](https://huggingface.co/datasets/yufan/amazon2023-item-metadata)
- Interactions: [`yufan/amazon2023-user-interactions`](https://huggingface.co/datasets/yufan/amazon2023-user-interactions)

Pick a category with `--data.category`, one of:
`Beauty_and_Personal_Care`, `Video_Games`, `Books`,
`Musical_Instruments`, `Industrial_and_Scientific`.

## Run the pipeline (in this order)

**Step 1 — item text → embeddings**

```bash
python src/embeddings.py \
    --data.category Beauty_and_Personal_Care \
    --data.output outputs/embeddings.pt \
    --model.name google/flan-t5-large
```

**Step 2 — embeddings → semantic IDs**

```bash
python src/quantize.py \
    --data.embeddings outputs/embeddings.pt \
    --data.output outputs/semantic_ids.pt \
    --method rqkmeans --num_hierarchies 3 --codebook_width 256
```

**Step 3 — train TIGER (also evaluates on the test set at the end)**

```bash
python src/train_tiger.py \
    --data.category Beauty_and_Personal_Care \
    --data.semantic_ids outputs/semantic_ids.pt \
    --ckpt.output outputs/tiger.pt \
    --train.epochs 50 --train.batch_size 256
```

**Step 4 (optional) — evaluate a saved checkpoint again**

```bash
python src/train_tiger.py --eval_only \
    --data.category Beauty_and_Personal_Care \
    --data.semantic_ids outputs/semantic_ids.pt \
    --ckpt.output outputs/tiger.pt
```

## Multi-GPU (optional)

Step 3 has a DeepSpeed version for one node with several GPUs. Steps 1, 2, and 4 stay the same.

```bash
deepspeed --num_gpus 8 src/train_tiger_ds.py \
    --data.category Beauty_and_Personal_Care \
    --data.semantic_ids outputs/semantic_ids.pt \
    --ckpt.output outputs/tiger.pt \
    --train.epochs 50 --train.micro_batch_size 256
```

## Notes

- Use the **same `--data.category`** in steps 1 and 3 (the item index must match).
- `--method` in step 2 can be `rqkmeans`, `rvq`, or `rqvae`.
- `--data.maxlen` (20 or 50) selects the history length / HF split. Default 20.
- Metrics reported: Recall@K, NDCG@K and MRR@K (default K = 5, 10; set with `--eval.ks`).
- **Weights & Biases**: training logs to wandb if a key is found (set
  `--logger.wandb.key` or `export WANDB_API_KEY=...`). It records loss, lr,
  grad-norm, throughput, and per-epoch eval / final test metrics. Disable with
  `--logger.wandb.enable 0`. Set `--logger.wandb.project` / `--logger.wandb.run_name`
  to organize runs.

## Reference

Rajput et al., *Recommender Systems with Generative Retrieval*, NeurIPS 2023.
https://arxiv.org/abs/2305.05065
