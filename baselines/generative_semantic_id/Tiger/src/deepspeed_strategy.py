"""A lean DeepSpeed strategy for single-node multi-GPU training.

Stripped down from a larger reference: ZeRO (stage 2 by default) + bf16 + a
DistributedSampler. No ring attention, no Muon, no tensor parallel — the TIGER
model is tiny and the sequences are short, so plain data-parallel ZeRO is all we
need.

The strategy hides the few distributed bits the training loop cares about:
build the DeepSpeed engine, backward/step, shard the dataloader, all-reduce
metrics, and save on rank 0.
"""

import os

import deepspeed
import torch
import torch.distributed as dist
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler


def get_ds_config(stage, param_dtype, max_norm, lr, weight_decay,
                  micro_batch_size, grad_accum, world_size):
    return {
        "train_micro_batch_size_per_gpu": micro_batch_size,
        "gradient_accumulation_steps": grad_accum,
        "train_batch_size": micro_batch_size * grad_accum * world_size,
        "gradient_clipping": max_norm,
        "steps_per_print": 1_000_000_000,
        "bf16": {"enabled": param_dtype == "bf16"},
        "fp16": {"enabled": param_dtype == "fp16"},
        "zero_optimization": {
            "stage": stage,
            "offload_optimizer": {"device": "none"},
            "offload_param": {"device": "none"},
            "reduce_bucket_size": "auto",
        },
        "optimizer": {
            "type": "AdamW",
            "params": {"lr": lr, "betas": [0.9, 0.999], "eps": 1e-8,
                       "weight_decay": weight_decay},
        },
    }


class DeepspeedStrategy:
    def __init__(self, args):
        self.args = args
        self.seed = args.seed
        self.stage = args.ds.zero_stage
        self.param_dtype = args.ds.param_dtype
        self.world_size = 1

    # ----------------------------------------------------------------- setup
    def setup_distributed(self):
        torch.manual_seed(self.seed)
        local_rank = int(os.environ.get("LOCAL_RANK", "-1"))
        if local_rank != -1:
            torch.cuda.set_device(local_rank)
        deepspeed.init_distributed()
        self.world_size = dist.get_world_size() if dist.is_initialized() else 1

    def prepare(self, model, lr, weight_decay, max_norm, micro_batch_size, grad_accum):
        ds_config = get_ds_config(
            stage=self.stage, param_dtype=self.param_dtype, max_norm=max_norm,
            lr=lr, weight_decay=weight_decay, micro_batch_size=micro_batch_size,
            grad_accum=grad_accum, world_size=self.world_size,
        )
        engine, optimizer, _, _ = deepspeed.initialize(
            model=model,
            model_parameters=model.parameters(),
            config=ds_config,
        )
        return engine, optimizer

    # --------------------------------------------------------------- training
    def backward(self, engine, loss):
        engine.backward(loss)

    def step(self, engine):
        engine.step()

    def get_grad_norm(self, engine):
        """Global grad norm from the DeepSpeed engine (0.0 if unavailable)."""
        if hasattr(engine, "get_global_grad_norm"):
            gn = engine.get_global_grad_norm()
            if gn is None:
                return 0.0
            return gn.item() if isinstance(gn, torch.Tensor) else float(gn)
        return 0.0

    # ------------------------------------------------------------- dataloader
    def setup_dataloader(self, dataset, batch_size, collate_fn, shuffle, drop_last):
        sampler = None
        if dist.is_initialized():
            sampler = DistributedSampler(
                dataset, num_replicas=self.world_size, rank=dist.get_rank(),
                shuffle=shuffle, seed=self.seed, drop_last=drop_last,
            )
        loader = DataLoader(
            dataset, batch_size=batch_size, sampler=sampler,
            shuffle=shuffle if sampler is None else False,
            drop_last=drop_last, collate_fn=collate_fn,
            num_workers=2, pin_memory=True,
        )
        return loader, sampler

    # --------------------------------------------------------------- reduction
    def all_reduce(self, data, op="mean"):
        if isinstance(data, dict):
            return {k: self.all_reduce(v, op) for k, v in data.items()}
        tensor = torch.tensor(data, device=torch.cuda.current_device(), dtype=torch.float32)
        if dist.is_initialized():
            dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
            if op == "mean":
                tensor /= self.world_size
        return tensor.item()

    # ------------------------------------------------------------------- utils
    def is_rank_0(self):
        return (not dist.is_initialized()) or dist.get_rank() == 0

    def print(self, *msg):
        if self.is_rank_0():
            print(*msg, flush=True)

    def barrier(self):
        if dist.is_initialized():
            dist.barrier()

    def broadcast(self, value, src=0):
        """Broadcast a python float from `src` to every rank."""
        tensor = torch.tensor(float(value), device=torch.cuda.current_device())
        if dist.is_initialized():
            dist.broadcast(tensor, src=src)
        return tensor.item()

    def save_model(self, engine, blob, path):
        """Save the unwrapped model state dict on rank 0 (works for ZeRO-1/2)."""
        if self.is_rank_0():
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            state = {k: v.float().cpu() for k, v in engine.module.state_dict().items()}
            torch.save({"model": state, **blob}, path)
        self.barrier()
