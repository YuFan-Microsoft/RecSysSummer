"""Step 3 + 4 (DeepSpeed, single-node multi-GPU).

Same TIGER training as `train_tiger.py`, but data-parallel across GPUs with
DeepSpeed ZeRO. Launch it with the `deepspeed` launcher, e.g. 8 GPUs:

    deepspeed --num_gpus 8 src/train_tiger_ds.py \
        --data.category Beauty_and_Personal_Care \
        --data.semantic_ids outputs/semantic_ids.pt \
        --ckpt.output outputs/tiger.pt \
        --train.epochs 50 --train.micro_batch_size 256

See scripts/train_tiger_ds.sh for a ready-to-run example.

Validation/test (beam search) runs on rank 0 only; the result is broadcast so
every rank agrees on which checkpoint is best. The saved checkpoint is a plain
state dict, identical in format to `train_tiger.py`, so you can evaluate it with
either script.
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
from torch.utils.data import DataLoader

from common import (WandbLogger, add_wandb_args, hierarchize, load_interaction_splits,
                    load_item_vocab, load_semantic_ids, set_seed)
from dataset import SequenceDataset, Collate
from deepspeed_strategy import DeepspeedStrategy
from metrics import compute_metrics
from tiger_model import TigerModel


@torch.no_grad()
def evaluate_rank0(model, rows, asin2idx, codes, H, args, ks):
    """Beam-search evaluation on a single rank (rank 0)."""
    model.eval()
    ds = SequenceDataset(rows, asin2idx, codes, H, max_items=args.data.maxlen)
    loader = DataLoader(ds, batch_size=args.eval.batch_size, shuffle=False,
                        collate_fn=Collate(0), num_workers=2)
    device = next(model.parameters()).device
    totals, n = {}, 0
    for input_tokens, mask, target, user_id in loader:
        input_tokens, mask = input_tokens.to(device), mask.to(device)
        user_id = user_id.to(device)
        beams, _ = model.generate(input_tokens, mask, beam_size=args.eval.beam_size, user_id=user_id)
        m = compute_metrics(beams.cpu(), target, ks=ks)
        bs = target.shape[0]
        for k, v in m.items():
            totals[k] = totals.get(k, 0.0) + v * bs
        n += bs
    return {k: v / n for k, v in totals.items()}


def run(args):
    set_seed(args.seed)
    ks = tuple(int(k) for k in args.eval.ks.split(","))

    strategy = DeepspeedStrategy(args)
    strategy.setup_distributed()

    splits = load_interaction_splits(args.data.category, maxlen=args.data.maxlen)
    _, asin2idx, _ = load_item_vocab(args.data.category)
    codes, codebook_width, H = load_semantic_ids(args.data.semantic_ids)
    if codes.shape[0] != len(asin2idx):
        raise ValueError(f"semantic_ids has {codes.shape[0]} items but vocab has "
                         f"{len(asin2idx)}; re-run steps 1-2 for {args.data.category}.")
    strategy.print(f"{args.data.category}: {codes.shape[0]} items, H={H}, "
                   f"V={codebook_width}, world_size={strategy.world_size}")

    model = TigerModel(
        num_hierarchies=H, codebook_width=codebook_width,
        d_model=args.model.d_model, num_layers=args.model.num_layers,
        num_heads=args.model.num_heads, d_ff=args.model.d_ff,
        d_kv=args.model.d_kv, dropout=args.model.dropout,
        mlp_layers=args.model.mlp_layers, add_sep_token=args.model.add_sep_token,
        num_user_bins=args.model.num_user_bins,
    )

    engine, _ = strategy.prepare(
        model, lr=args.train.lr, weight_decay=args.train.weight_decay,
        max_norm=args.train.max_norm, micro_batch_size=args.train.micro_batch_size,
        grad_accum=args.train.grad_accum,
    )
    device = engine.device

    train_ds = SequenceDataset(splits["train"], asin2idx, codes, H, max_items=args.data.maxlen)
    train_loader, sampler = strategy.setup_dataloader(
        train_ds, args.train.micro_batch_size, Collate(0), shuffle=True, drop_last=True)

    blob = {"codebook_width": codebook_width, "num_hierarchies": H}
    wandb = WandbLogger(args, enabled=strategy.is_rank_0())
    best_metric = -1.0
    global_step = 0
    for epoch in range(args.train.epochs):
        engine.train()
        if sampler is not None:
            sampler.set_epoch(epoch)
        running = 0.0
        t0, seen = time.time(), 0
        for step, (input_tokens, mask, target, user_id) in enumerate(train_loader):
            input_tokens, mask, target = input_tokens.to(device), mask.to(device), target.to(device)
            user_id = user_id.to(device)
            loss = engine(input_tokens, mask, target, user_id)
            strategy.backward(engine, loss)
            strategy.step(engine)
            global_step += 1
            running += loss.item()
            seen += target.shape[0]
            if step % args.logger.logging_steps == 0:
                grad_norm = strategy.get_grad_norm(engine)
                if strategy.is_rank_0():
                    dt = max(time.time() - t0, 1e-6)
                    strategy.print(f"epoch {epoch + 1} step {step} loss={loss.item():.4f}")
                    wandb.log({
                        "train/loss": loss.item(),
                        "train/lr": args.train.lr,
                        "train/grad_norm": grad_norm,
                        "train/epoch": epoch + 1,
                        "train/examples_per_sec": seen * strategy.world_size / dt,
                        "train/global_step": global_step,
                    })
        avg = strategy.all_reduce(running / max(1, len(train_loader)), op="mean")
        strategy.print(f"epoch {epoch + 1}: train_loss={avg:.4f}")
        wandb.log({"train/epoch_loss": avg, "train/epoch": epoch + 1,
                   "train/global_step": global_step})

        if (epoch + 1) % args.eval.every == 0:
            metric, m = -1.0, None
            if strategy.is_rank_0():
                m = evaluate_rank0(engine.module, splits["valid"], asin2idx, codes, H, args, ks)
                strategy.print(f"  valid: {m}")
                metric = m[f"recall@{ks[0]}"]
            metric = strategy.broadcast(metric)          # rank 0 -> all ranks
            if metric > best_metric:
                best_metric = metric
                strategy.save_model(engine, blob, args.ckpt.output)
                strategy.print(f"  saved best (recall@{ks[0]}={best_metric:.4f}) -> {args.ckpt.output}")
            if strategy.is_rank_0() and m is not None:
                wandb.log({**{f"eval/{k}": v for k, v in m.items()},
                           f"eval/best_recall@{ks[0]}": best_metric,
                           "eval/epoch": epoch + 1, "eval/global_step": global_step})

    if not os.path.exists(args.ckpt.output):
        strategy.save_model(engine, blob, args.ckpt.output)

    # final test on rank 0 with the best checkpoint
    if strategy.is_rank_0():
        state = torch.load(args.ckpt.output, map_location=device)["model"]
        engine.module.load_state_dict(state)
        test_m = evaluate_rank0(engine.module, splits["test"], asin2idx, codes, H, args, ks)
        print("test:", test_m, flush=True)
        wandb.log({f"test/{k}": v for k, v in test_m.items()})
    wandb.finish()
    strategy.barrier()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data.category", type=str, required=True,
                   help="e.g. Beauty_and_Personal_Care, Video_Games, Books, ...")
    p.add_argument("--data.semantic_ids", type=str, required=True)
    p.add_argument("--ckpt.output", type=str, default="outputs/tiger.pt")

    p.add_argument("--model.d_model", type=int, default=128)
    p.add_argument("--model.num_layers", type=int, default=4)
    p.add_argument("--model.num_heads", type=int, default=6)
    p.add_argument("--model.d_ff", type=int, default=1024)
    p.add_argument("--model.d_kv", type=int, default=64)
    p.add_argument("--model.dropout", type=float, default=0.15)
    p.add_argument("--data.maxlen", type=int, default=20, choices=[20, 50],
                   help="history length; picks the seq_maxlen{20,50} HF config")
    p.add_argument("--model.mlp_layers", type=int, default=2, help="FF bloating depth; 0 disables")
    p.add_argument("--model.add_sep_token", type=int, default=1, help="1=add item separator token")
    p.add_argument("--model.num_user_bins", type=int, default=None, help="None=no user embedding")

    p.add_argument("--train.epochs", type=int, default=50)
    p.add_argument("--train.micro_batch_size", type=int, default=256, help="batch size per GPU")
    p.add_argument("--train.grad_accum", type=int, default=1)
    p.add_argument("--train.lr", type=float, default=1e-3)
    p.add_argument("--train.weight_decay", type=float, default=1e-4)
    p.add_argument("--train.max_norm", type=float, default=1.0)

    p.add_argument("--eval.batch_size", type=int, default=128)
    p.add_argument("--eval.beam_size", type=int, default=10)
    p.add_argument("--eval.every", type=int, default=5)
    p.add_argument("--eval.ks", type=str, default="5,10")

    p.add_argument("--ds.zero_stage", type=int, default=2)
    p.add_argument("--ds.param_dtype", type=str, default="bf16", choices=["bf16", "fp16", "fp32"])
    p.add_argument("--logger.logging_steps", type=int, default=50)
    add_wandb_args(p)

    p.add_argument("--local_rank", type=int, default=-1, help="set by the deepspeed launcher")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


if __name__ == "__main__":
    run(hierarchize(parse_args()))
