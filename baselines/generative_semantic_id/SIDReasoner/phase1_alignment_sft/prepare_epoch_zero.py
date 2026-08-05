"""Create the SID-extended Phase-1 epoch-0 checkpoint before training."""

import argparse
import json
import os
import random
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare the untrained SID-extended Phase-1 checkpoint."
    )
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--wandb-run-id", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dtype", choices=["fp16", "bf16", "fp32"], default="bf16")
    return parser.parse_args()


def set_seed(seed):
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def torch_dtype_from(dtype):
    import torch

    return {
        "fp16": torch.float16,
        "bf16": torch.bfloat16,
        "fp32": torch.float32,
    }[dtype]


def write_manifest(output_dir, wandb_run_id):
    path = output_dir / "phase1_checkpoint_manifest.json"
    temp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump({"wandb_run_id": wandb_run_id, "epochs": [0]}, handle, indent=2)
    os.replace(temp_path, path)


def main():
    args = parse_args()
    from transformers import AutoModelForCausalLM, AutoTokenizer

    import hf_data

    set_seed(args.seed)

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch_dtype_from(args.dtype),
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenizer.padding_side = "left"

    new_tokens = hf_data.load_sid_tokens(args.category)
    existing_vocab = set(tokenizer.get_vocab().keys())
    tokens_to_add = [token for token in new_tokens if token not in existing_vocab]
    if tokens_to_add:
        tokenizer.add_tokens(tokens_to_add)
        model.resize_token_embeddings(len(tokenizer))

    output_dir = Path(args.output_dir).resolve()
    checkpoint_dir = output_dir / "epoch_0"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(checkpoint_dir)
    tokenizer.save_pretrained(checkpoint_dir)
    write_manifest(output_dir, args.wandb_run_id)
    print(
        f"Prepared Phase-1 epoch_0 at {checkpoint_dir} "
        f"with {len(tokens_to_add)} added SID tokens",
        flush=True,
    )


if __name__ == "__main__":
    main()