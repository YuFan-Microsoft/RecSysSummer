"""Step 3 + 4: train the TIGER model on semantic IDs and evaluate it.

Train:
    python train_tiger.py \
        --data.category Beauty_and_Personal_Care \
        --data.semantic_ids outputs/semantic_ids.pt \
        --ckpt.output outputs/tiger.pt \
        --train.epochs 50 --train.batch_size 256

Evaluate an existing checkpoint on the test split:
    python train_tiger.py --eval_only \
        --data.category Beauty_and_Personal_Care \
        --data.semantic_ids outputs/semantic_ids.pt \
        --ckpt.output outputs/tiger.pt
"""

import argparse
import os
import sys
import time

# Make sibling modules importable regardless of how this script is launched.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from common import (WandbLogger, add_wandb_args, get_device, hierarchize,
                    load_interaction_splits, load_item_vocab, load_semantic_ids,
                    save_pt, set_seed)
from dataset import SequenceDataset, Collate
from metrics import compute_metrics
from tiger_model import TigerModel


def build_loader(rows, asin2idx, codes, H, batch_size, max_items, pad_id, shuffle):
    ds = SequenceDataset(rows, asin2idx, codes, H, max_items=max_items)
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle,
                      collate_fn=Collate(pad_id), num_workers=2)


@torch.no_grad()
def evaluate(model, loader, device, beam_size, ks):
    model.eval()
    totals, n = {}, 0
    for input_tokens, mask, target, user_id in tqdm(loader, desc="eval", leave=False):
        input_tokens, mask = input_tokens.to(device), mask.to(device)
        user_id = user_id.to(device)
        beams, _ = model.generate(input_tokens, mask, beam_size=beam_size, user_id=user_id)
        m = compute_metrics(beams.cpu(), target, ks=ks)
        bs = target.shape[0]
        for k, v in m.items():
            totals[k] = totals.get(k, 0.0) + v * bs
        n += bs
    return {k: v / n for k, v in totals.items()}


def run(args):
    set_seed(args.seed)
    device = get_device(args.device)
    ks = tuple(int(k) for k in args.eval.ks.split(","))

    splits = load_interaction_splits(args.data.category, maxlen=args.data.maxlen)
    _, asin2idx, _ = load_item_vocab(args.data.category)
    codes, codebook_width, H = load_semantic_ids(args.data.semantic_ids)
    if codes.shape[0] != len(asin2idx):
        raise ValueError(f"semantic_ids has {codes.shape[0]} items but vocab has "
                         f"{len(asin2idx)}; re-run steps 1-2 for {args.data.category}.")
    print(f"{args.data.category}: {codes.shape[0]} items, H={H}, V={codebook_width}")

    model = TigerModel(
        num_hierarchies=H, codebook_width=codebook_width,
        d_model=args.model.d_model, num_layers=args.model.num_layers,
        num_heads=args.model.num_heads, d_ff=args.model.d_ff,
        d_kv=args.model.d_kv, dropout=args.model.dropout,
        mlp_layers=args.model.mlp_layers, add_sep_token=args.model.add_sep_token,
        num_user_bins=args.model.num_user_bins,
    ).to(device)
    pad_id = 0  # padded positions are masked out; the value is irrelevant

    test_loader = build_loader(splits["test"], asin2idx, codes, H, args.eval.batch_size,
                               args.data.maxlen, pad_id, shuffle=False)

    if args.eval_only:
        model.load_state_dict(torch.load(args.ckpt.output, map_location=device)["model"])
        print("test:", evaluate(model, test_loader, device, args.eval.test_beam_size, ks))
        return

    train_loader = build_loader(splits["train"], asin2idx, codes, H, args.train.batch_size,
                                args.data.maxlen, pad_id, shuffle=True)
    valid_loader = build_loader(splits["valid"], asin2idx, codes, H, args.eval.batch_size,
                                args.data.maxlen, pad_id, shuffle=False)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.train.lr,
                                 weight_decay=args.train.weight_decay)
    wandb = WandbLogger(args)

    best_metric = -1.0
    global_step = 0
    for epoch in range(args.train.epochs):
        model.train()
        total_loss = 0.0
        t0, seen = time.time(), 0
        bar = tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.train.epochs}")
        for input_tokens, mask, target, user_id in bar:
            input_tokens, mask, target = input_tokens.to(device), mask.to(device), target.to(device)
            user_id = user_id.to(device)
            loss = model(input_tokens, mask, target, user_id=user_id)
            optimizer.zero_grad()
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.train.max_norm)
            optimizer.step()
            global_step += 1
            total_loss += loss.item()
            seen += target.shape[0]
            bar.set_postfix(loss=loss.item())
            if global_step % args.logger.logging_steps == 0:
                dt = max(time.time() - t0, 1e-6)
                wandb.log({
                    "train/loss": loss.item(),
                    "train/lr": optimizer.param_groups[0]["lr"],
                    "train/grad_norm": float(grad_norm),
                    "train/epoch": epoch + 1,
                    "train/examples_per_sec": seen / dt,
                    "train/global_step": global_step,
                })
        epoch_loss = total_loss / len(train_loader)
        print(f"epoch {epoch + 1}: train_loss={epoch_loss:.4f}")
        wandb.log({"train/epoch_loss": epoch_loss, "train/epoch": epoch + 1,
                   "train/global_step": global_step})

        if (epoch + 1) % args.eval.every == 0:
            metrics = evaluate(model, valid_loader, device, args.eval.beam_size, ks)
            print(f"  valid: {metrics}")
            key = f"recall@{ks[0]}"
            if metrics[key] > best_metric:
                best_metric = metrics[key]
                save_pt({"model": model.state_dict(), "codebook_width": codebook_width,
                         "num_hierarchies": H}, args.ckpt.output)
                print(f"  saved best ({key}={best_metric:.4f}) -> {args.ckpt.output}")
            wandb.log({**{f"eval/{k}": v for k, v in metrics.items()},
                       f"eval/best_{key}": best_metric,
                       "eval/epoch": epoch + 1, "eval/global_step": global_step})

    # Make sure a checkpoint exists even if no validation ran (e.g. epochs < eval.every).
    if not os.path.exists(args.ckpt.output):
        save_pt({"model": model.state_dict(), "codebook_width": codebook_width,
                 "num_hierarchies": H}, args.ckpt.output)

    # final test with the best checkpoint (report at the larger test-time beam)
    model.load_state_dict(torch.load(args.ckpt.output, map_location=device)["model"])
    test_metrics = evaluate(model, test_loader, device, args.eval.test_beam_size, ks)
    print("test:", test_metrics)
    wandb.log({f"test/{k}": v for k, v in test_metrics.items()})
    wandb.finish()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data.category", type=str, required=True,
                   help="e.g. Beauty_and_Personal_Care, Video_Games, Books, ...")
    p.add_argument("--data.semantic_ids", type=str, required=True)
    p.add_argument("--ckpt.output", type=str, default="outputs/tiger.pt")
    p.add_argument("--eval_only", action="store_true")

    p.add_argument("--model.d_model", type=int, default=128)
    p.add_argument("--model.num_layers", type=int, default=4)
    p.add_argument("--model.num_heads", type=int, default=6)
    p.add_argument("--model.d_ff", type=int, default=1024)
    p.add_argument("--model.d_kv", type=int, default=64)
    p.add_argument("--model.dropout", type=float, default=0.10)
    p.add_argument("--data.maxlen", type=int, default=20, choices=[20, 50],
                   help="history length; picks the seq_maxlen{20,50} HF config")
    p.add_argument("--model.mlp_layers", type=int, default=2, help="FF bloating depth; 0 disables")
    p.add_argument("--model.add_sep_token", type=int, default=1, help="1=add item separator token")
    p.add_argument("--model.num_user_bins", type=int, default=None, help="None=no user embedding")

    p.add_argument("--train.epochs", type=int, default=50)
    p.add_argument("--train.batch_size", type=int, default=256)
    p.add_argument("--train.lr", type=float, default=5e-4)
    p.add_argument("--train.weight_decay", type=float, default=1e-6)
    p.add_argument("--train.max_norm", type=float, default=1.0)

    p.add_argument("--eval.batch_size", type=int, default=128)
    p.add_argument("--eval.beam_size", type=int, default=10,
                   help="beam size for validation/model-selection (fast)")
    p.add_argument("--eval.test_beam_size", type=int, default=50,
                   help="beam size for the final test / eval_only (paper standard)")
    p.add_argument("--eval.every", type=int, default=5)
    p.add_argument("--eval.ks", type=str, default="5,10")

    p.add_argument("--logger.logging_steps", type=int, default=50)
    add_wandb_args(p)

    p.add_argument("--device", type=str, default="auto")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


if __name__ == "__main__":
    run(hierarchize(parse_args()))
