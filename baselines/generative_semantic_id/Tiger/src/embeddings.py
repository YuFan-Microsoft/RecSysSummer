"""Step 1: turn item text into embeddings with a HuggingFace encoder.

Reads item metadata for a category from yufan/amazon2023-item-metadata, builds
one text string per item (title + features + description + categories), and
mean-pools an encoder's hidden states into one vector per item. Items are
ordered by sorted parent_asin so every later step agrees on the index.

Example:
    python embeddings.py \
        --data.category Beauty_and_Personal_Care \
        --data.output outputs/embeddings.pt \
        --model.name sentence-transformers/sentence-t5-base
"""

import argparse
import os
import sys

# Make sibling modules importable regardless of how this script is launched.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

from common import get_device, hierarchize, load_item_vocab, mean_pool, save_pt, set_seed


@torch.no_grad()
def generate_embeddings(args):
    set_seed(args.seed)
    device = get_device(args.device)

    asins, _, texts = load_item_vocab(args.data.category)
    print(f"Loaded {len(texts)} items for {args.data.category}")

    tokenizer = AutoTokenizer.from_pretrained(args.model.name)
    # Force float32: some checkpoints are stored in fp16, and fused (apex)
    # LayerNorm/RMSNorm kernels reject half-precision inputs.
    model = AutoModel.from_pretrained(args.model.name, torch_dtype=torch.float32).to(device).eval()
    # T5 ships an encoder-decoder; we only need the encoder for embeddings.
    if hasattr(model, "get_encoder"):
        model = model.get_encoder()

    all_embeddings = []
    for start in tqdm(range(0, len(texts), args.infer.batch_size), desc="Embedding"):
        batch = texts[start : start + args.infer.batch_size]
        enc = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=args.model.max_length,
            return_tensors="pt",
        ).to(device)
        out = model(**enc).last_hidden_state
        emb = mean_pool(out, enc["attention_mask"]).float().cpu()
        all_embeddings.append(emb)

    embeddings = torch.cat(all_embeddings, dim=0)
    save_pt(embeddings, args.data.output)
    print(f"Saved embeddings {tuple(embeddings.shape)} -> {args.data.output}")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data.category", type=str, required=True,
                   help="e.g. Beauty_and_Personal_Care, Video_Games, Books, ...")
    p.add_argument("--data.output", type=str, required=True)
    p.add_argument("--model.name", type=str, default="sentence-transformers/sentence-t5-base")
    p.add_argument("--model.max_length", type=int, default=128)
    p.add_argument("--infer.batch_size", type=int, default=64)
    p.add_argument("--device", type=str, default="auto")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


if __name__ == "__main__":
    generate_embeddings(hierarchize(parse_args()))
