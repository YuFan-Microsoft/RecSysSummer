"""Evaluate Phase-1 checkpoints before and after multi-node training."""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
EVALUATION_DIR = REPO_ROOT / "evaluation"
METRIC_CUTOFFS = (5, 10)

sys.path.insert(0, str(REPO_ROOT))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate epoch_0 and every trained Phase-1 epoch without thinking."
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--cuda-list", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--num-samples", type=int, default=-1)
    parser.add_argument("--num-beams", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--sid-length", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-epoch", type=int, default=0)
    parser.add_argument("--max-epoch", type=int, default=-1)
    parser.add_argument("--report-to", choices=["wandb", "none"], default="wandb")
    parser.add_argument("--wandb-project")
    parser.add_argument("--wandb-run-name")
    parser.add_argument("--wandb-run-id")
    args = parser.parse_args()

    if args.num_beams < max(METRIC_CUTOFFS):
        parser.error(f"--num-beams must be at least {max(METRIC_CUTOFFS)}")
    if args.num_samples == 0 or args.num_samples < -1:
        parser.error("--num-samples must be -1 or a positive integer")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.sid_length != 3:
        parser.error("--sid-length must be 3 for recommendation metrics")
    if args.min_epoch < 0:
        parser.error("--min-epoch must be non-negative")
    if args.max_epoch != -1 and args.max_epoch < args.min_epoch:
        parser.error("--max-epoch must be -1 or at least --min-epoch")
    args.cuda_list = [value.strip() for value in args.cuda_list.split(",") if value.strip()]
    if not args.cuda_list:
        parser.error("--cuda-list must contain at least one GPU")
    if args.report_to == "wandb":
        missing = [
            name for name in ("wandb_project", "wandb_run_name", "wandb_run_id")
            if not getattr(args, name)
        ]
        if missing:
            parser.error(
                "--report-to wandb requires "
                + ", ".join(f"--{name.replace('_', '-')}" for name in missing)
            )
    return args


def data_locators(category):
    return {
        "test": REPO_ROOT / "data" / "Amazon" / "test" / f"{category}_5_2016-10-2018-11.csv",
        "info": REPO_ROOT / "data" / "Amazon" / "info" / f"{category}_5_2016-10-2018-11.txt",
    }


def discover_checkpoints(output_dir, wandb_run_id=None):
    manifest_path = output_dir / "phase1_checkpoint_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"checkpoint manifest not found: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if wandb_run_id and manifest.get("wandb_run_id") != wandb_run_id:
        raise ValueError(
            f"checkpoint manifest belongs to W&B run {manifest.get('wandb_run_id')!r}, "
            f"not {wandb_run_id!r}"
        )

    epochs = manifest.get("epochs", [])
    if not epochs or epochs[0] != 0 or epochs != sorted(set(epochs)):
        raise ValueError(f"invalid checkpoint manifest epochs: {epochs!r}")
    checkpoints = []
    for epoch in epochs:
        path = output_dir / f"epoch_{epoch}"
        if not path.is_dir():
            raise FileNotFoundError(f"checkpoint listed in manifest is missing: {path}")
        checkpoints.append((epoch, path.resolve()))
    return checkpoints


def run_checked(command):
    print("+ " + " ".join(str(value) for value in command), flush=True)
    subprocess.run(command, check=True)


def has_data_row(path):
    if not path.exists():
        return False
    with open(path, "r", encoding="utf-8", newline="") as handle:
        rows = csv.reader(handle)
        next(rows, None)
        return next(rows, None) is not None


def split_test_data(test_locator, shard_dir, cuda_list, num_samples):
    shard_dir.mkdir(parents=True, exist_ok=True)
    for path in shard_dir.glob("*.csv"):
        path.unlink()
    run_checked([
        sys.executable,
        str(EVALUATION_DIR / "split.py"),
        "--input_path", str(test_locator),
        "--output_path", str(shard_dir),
        "--cuda_list", ",".join(cuda_list),
        "--num_samples", str(num_samples),
    ])
    active_gpus = [
        gpu for gpu in cuda_list
        if has_data_row(shard_dir / f"{gpu}.csv")
    ]
    if not active_gpus:
        raise RuntimeError("evaluation split produced no non-empty GPU shards")
    return active_gpus


def _normalize_item(value):
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).strip(' \n"')


def calculate_metrics(path, item_path):
    import hf_data

    known_sids = {
        line.split("\t")[0].strip()
        for line in hf_data.load_info_lines(item_path)
    }
    with open(path, "r", encoding="utf-8") as handle:
        test_data = json.load(handle)

    max_beams = max((len(sample.get("predict", [])) for sample in test_data), default=0)
    if max_beams < max(METRIC_CUTOFFS):
        raise ValueError(f"predictions contain only {max_beams} beams; need at least 10")
    hits = {cutoff: 0.0 for cutoff in METRIC_CUTOFFS}
    ndcg = {cutoff: 0.0 for cutoff in METRIC_CUTOFFS}

    for sample in test_data:
        predictions = [_normalize_item(value) for value in sample.get("predict", [])]
        target = _normalize_item(sample.get("output", ""))
        try:
            rank = predictions.index(target)
        except ValueError:
            continue
        for cutoff in METRIC_CUTOFFS:
            if rank < cutoff:
                hits[cutoff] += 1.0
                ndcg[cutoff] += 1.0 / math.log2(rank + 2)

    denominator = len(test_data)
    return {
        "rows": denominator,
        "num_beams": max_beams,
        "hr": {
            str(cutoff): hits[cutoff] / denominator if denominator else 0.0
            for cutoff in METRIC_CUTOFFS
        },
        "ndcg": {
            str(cutoff): ndcg[cutoff] / denominator if denominator else 0.0
            for cutoff in METRIC_CUTOFFS
        },
    }


def evaluator_command(args, checkpoint, gpu, paths, shard_dir, result_dir):
    return [
        sys.executable,
        str(EVALUATION_DIR / "evaluate_Qwen3.py"),
        "--base_model", str(checkpoint),
        "--info_file", str(paths["info"]),
        "--category", args.category,
        "--test_data_path", str(shard_dir / f"{gpu}.csv"),
        "--result_json_data", str(result_dir / f"{gpu}.json"),
        "--batch_size", str(args.batch_size),
        "--num_beams", str(args.num_beams),
        "--sid_length", str(args.sid_length),
        "--length_penalty", "0.0",
        "--seed", str(args.seed),
    ]


def evaluate_checkpoint(args, epoch, checkpoint, paths, shard_dir, active_gpus, eval_root):
    result_dir = eval_root / f"epoch_{epoch}"
    result_dir.mkdir(parents=True, exist_ok=True)
    for path in result_dir.glob("*.json"):
        path.unlink()

    processes = []
    for gpu in active_gpus:
        cache_root = result_dir / ".cache" / f"gpu{gpu}"
        cache_root.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update({
            "CUDA_VISIBLE_DEVICES": gpu,
            "TRITON_CACHE_DIR": str(cache_root / "triton"),
            "TORCHINDUCTOR_CACHE_DIR": str(cache_root / "inductor"),
            "VLLM_CACHE_ROOT": str(cache_root / "vllm"),
        })
        command = evaluator_command(args, checkpoint, gpu, paths, shard_dir, result_dir)
        print("+ " + " ".join(command), flush=True)
        processes.append((gpu, subprocess.Popen(command, env=env)))

    failures = []
    for gpu, process in processes:
        return_code = process.wait()
        if return_code != 0:
            failures.append(f"GPU {gpu}: exit {return_code}")
    if failures:
        raise RuntimeError(f"epoch {epoch} evaluation failed ({', '.join(failures)})")

    merged_path = result_dir / f"final_result_{args.category}.json"
    merged = []
    for gpu in active_gpus:
        with open(result_dir / f"{gpu}.json", "r", encoding="utf-8") as handle:
            merged.extend(json.load(handle))
    with open(merged_path, "w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2)

    metrics = calculate_metrics(merged_path, paths["info"])
    metrics.update({"epoch": epoch, "checkpoint": str(checkpoint), "predictions": str(merged_path)})
    print(
        f"[epoch {epoch}] HR@5={metrics['hr']['5']:.6f} "
        f"HR@10={metrics['hr']['10']:.6f} | "
        f"NDCG@5={metrics['ndcg']['5']:.6f} "
        f"NDCG@10={metrics['ndcg']['10']:.6f}",
        flush=True,
    )
    return metrics


def init_wandb(args):
    if args.report_to != "wandb":
        return None
    import wandb

    run = wandb.init(
        project=args.wandb_project,
        name=args.wandb_run_name,
        id=args.wandb_run_id,
        resume="allow" if args.min_epoch == 0 else "must",
    )
    wandb.define_metric("recsys_eval_step")
    wandb.define_metric(
        "recsys_eval_nothinking/*", step_metric="recsys_eval_step"
    )
    return run


def log_wandb(run, metrics):
    if run is None:
        return
    payload = {"recsys_eval_step": metrics["epoch"]}
    for cutoff in METRIC_CUTOFFS:
        payload[f"recsys_eval_nothinking/hr_at_{cutoff}"] = metrics["hr"][str(cutoff)]
        payload[f"recsys_eval_nothinking/ndcg_at_{cutoff}"] = metrics["ndcg"][str(cutoff)]
    run.log(payload)


def main():
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    checkpoints = [
        (epoch, checkpoint)
        for epoch, checkpoint in discover_checkpoints(output_dir, args.wandb_run_id)
        if epoch >= args.min_epoch and (args.max_epoch == -1 or epoch <= args.max_epoch)
    ]
    if not checkpoints:
        raise RuntimeError(
            f"no checkpoints found in requested epoch range "
            f"[{args.min_epoch}, {args.max_epoch}]"
        )
    eval_root = output_dir / "recsys_eval_nothinking"
    eval_root.mkdir(parents=True, exist_ok=True)
    metrics_path = eval_root / "metrics.json"
    paths = data_locators(args.category)
    shard_dir = eval_root / "shards"
    active_gpus = split_test_data(paths["test"], shard_dir, args.cuda_list, args.num_samples)

    if args.min_epoch == 0:
        report = {
            "category": args.category,
            "wandb_run_id": args.wandb_run_id,
            "num_beams": args.num_beams,
            "num_samples": args.num_samples,
            "checkpoints": [],
        }
    else:
        if not metrics_path.is_file():
            raise FileNotFoundError(f"pre-training metrics not found: {metrics_path}")
        with open(metrics_path, "r", encoding="utf-8") as handle:
            report = json.load(handle)
        if report.get("category") != args.category:
            raise ValueError("pre-training metrics category does not match")
        if report.get("wandb_run_id") != args.wandb_run_id:
            raise ValueError("pre-training metrics W&B run ID does not match")

    run = init_wandb(args)
    try:
        for epoch, checkpoint in checkpoints:
            metrics = evaluate_checkpoint(
                args, epoch, checkpoint, paths, shard_dir, active_gpus, eval_root
            )
            report["checkpoints"] = [
                existing
                for existing in report["checkpoints"]
                if existing.get("epoch") != epoch
            ]
            report["checkpoints"].append(metrics)
            report["checkpoints"].sort(key=lambda item: item["epoch"])
            log_wandb(run, metrics)
            with open(metrics_path, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2)
    finally:
        if run is not None:
            run.finish()

    print(f"Wrote Phase-1 recommendation metrics to {metrics_path}")


if __name__ == "__main__":
    main()