#!/usr/bin/env python3
"""Warm one node's Hugging Face dataset and model caches for Phase-1."""

import argparse
import os


DEFAULT_DATASET_REPO = "yufan/recsys-genrec-dataset"
CATEGORIES = (
    "Video_Games",
    "Office_Products",
    "Industrial_and_Scientific",
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prefetch SIDReasoner Phase-1 data and model on one node."
    )
    parser.add_argument("--category", required=True, choices=CATEGORIES)
    parser.add_argument("--base_model", default="Qwen/Qwen3-1.7B")
    parser.add_argument(
        "--dataset_repo",
        default=os.environ.get("SIDR_HF_REPO", DEFAULT_DATASET_REPO),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any requested dataset split or model is missing.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Prefetch is deliberately online even when the parent shell trained offline.
    os.environ.pop("HF_HUB_OFFLINE", None)
    os.environ.pop("HF_DATASETS_OFFLINE", None)
    os.environ.pop("TRANSFORMERS_OFFLINE", None)
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")

    from datasets import load_dataset
    from huggingface_hub import snapshot_download

    dataset_splits = {
        f"{args.category}_seqrec": ("train", "validation", "test"),
        f"{args.category}_catalog": ("train",),
        f"{args.category}_reasoning": ("train",),
        "general_reasoning": ("train",),
    }

    failures = []
    for config, splits in dataset_splits.items():
        for split in splits:
            try:
                dataset = load_dataset(
                    args.dataset_repo,
                    config,
                    split=split,
                )
                print(
                    f"[OK] dataset {args.dataset_repo}/{config}:{split} "
                    f"({len(dataset)} rows)",
                    flush=True,
                )
            except Exception as exc:
                failures.append(f"dataset {config}:{split}")
                print(f"[SKIP] dataset {config}:{split}: {exc}", flush=True)

    try:
        snapshot_path = snapshot_download(repo_id=args.base_model)
        print(f"[OK] model {args.base_model} -> {snapshot_path}", flush=True)
    except Exception as exc:
        failures.append(f"model {args.base_model}")
        print(f"[SKIP] model {args.base_model}: {exc}", flush=True)

    if failures:
        print(
            "[WARN] Prefetch completed with missing cache entries: "
            + ", ".join(failures),
            flush=True,
        )
        if args.strict:
            raise SystemExit(1)
    else:
        print("[OK] Prefetch completed with all requested cache entries.", flush=True)


if __name__ == "__main__":
    main()
