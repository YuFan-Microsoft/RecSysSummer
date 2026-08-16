from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

import numpy as np

from .embedder import DEFAULT_MODEL, DEFAULT_QUERY_INSTRUCTION, Qwen3Embedder


DEFAULT_DATASET = "yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV2"
DEFAULT_DATASET_REVISION = "a5eb07115444b128ab7add812e4cee87517a5c41"
DEFAULT_CATEGORY = "Video_Games"
INDEX_TEXT_FIELDS = ("title", "brand", "description", "detailed_description")
DEFAULT_GPU_IDS = tuple(str(index) for index in range(8))
DEFAULT_BUILD_BATCH_SIZE = 128


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"nan", "none"} else text


def item_index_text(item: dict[str, Any]) -> str:
    sections = []
    labels = {
        "title": "Title",
        "brand": "Brand",
        "description": "Description",
        "detailed_description": "Details",
    }
    for field in INDEX_TEXT_FIELDS:
        text = _clean_text(item.get(field))
        if text:
            sections.append(f"{labels[field]}: {text}")
    if not sections:
        raise ValueError(f"catalog item has no indexable metadata: {item.get('sid')}")
    return "\n".join(sections)


def load_catalog(dataset: str, revision: str, category: str) -> list[dict[str, Any]]:
    from datasets import load_dataset

    config = f"{category}_catalog"
    split = load_dataset(dataset, config, split="train", revision=revision)
    required_fields = {"item_id", "sid", *INDEX_TEXT_FIELDS}
    missing_fields = required_fields - set(split.column_names)
    if missing_fields:
        raise ValueError(f"catalog is missing required fields: {sorted(missing_fields)}")

    catalog = []
    for row in split:
        catalog.append(
            {
                "item_id": int(row["item_id"]),
                "sid": _clean_text(row["sid"]),
                "title": _clean_text(row["title"]),
                "brand": _clean_text(row["brand"]),
                "description": _clean_text(row["description"]),
                "detailed_description": _clean_text(row["detailed_description"]),
            }
        )
    return catalog


def parse_gpu_ids(value: str) -> list[str]:
    gpu_ids = [gpu_id.strip() for gpu_id in value.split(",") if gpu_id.strip()]
    if len(gpu_ids) != 8 or len(set(gpu_ids)) != 8:
        raise ValueError("--gpus must contain exactly eight distinct GPU IDs")
    return gpu_ids


def partition_ranges(total: int, world_size: int = 8) -> list[tuple[int, int]]:
    if total < world_size:
        raise ValueError(f"at least {world_size} items are required to use all GPUs")
    return [
        (rank * total // world_size, (rank + 1) * total // world_size)
        for rank in range(world_size)
    ]


def _embed_worker(
    rank: int,
    gpu_id: str,
    input_path: str,
    output_path: str,
    model: str,
    dtype: str,
    max_length: int,
    batch_size: int,
    use_flash_attention: bool,
) -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_id
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    for variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(variable, "1")

    torch = importlib.import_module("torch")

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError(
            f"worker {rank} must see exactly one CUDA GPU; physical GPU={gpu_id}"
        )
    with Path(input_path).open("r", encoding="utf-8") as file:
        texts = json.load(file)
    embedder = Qwen3Embedder(
        model_name_or_path=model,
        device="cuda:0",
        dtype=dtype,
        max_length=max_length,
        use_flash_attention=use_flash_attention,
    )
    embeddings = embedder.encode_documents(texts, batch_size=batch_size)
    np.save(output_path, np.asarray(embeddings, dtype=np.float32))


def embed_documents_eight_gpu(
    texts: list[str],
    model: str,
    gpu_ids: list[str],
    dtype: str,
    max_length: int,
    batch_size: int,
    use_flash_attention: bool,
) -> np.ndarray:
    if len(gpu_ids) != 8 or len(set(gpu_ids)) != 8:
        raise ValueError("eight distinct GPU IDs are required")
    ranges = partition_ranges(len(texts), world_size=8)
    temporary_dir = Path(tempfile.mkdtemp(prefix="sid_interest_index_"))
    context = mp.get_context("spawn")
    processes = []
    output_paths = []
    try:
        for rank, ((start, end), gpu_id) in enumerate(zip(ranges, gpu_ids)):
            input_path = temporary_dir / f"input_{rank}.json"
            output_path = temporary_dir / f"embeddings_{rank}.npy"
            with input_path.open("w", encoding="utf-8") as file:
                json.dump(texts[start:end], file, ensure_ascii=False)
            print(
                f"[index] worker={rank} physical_gpu={gpu_id} items={start}:{end}",
                flush=True,
            )
            process = context.Process(
                target=_embed_worker,
                args=(
                    rank,
                    gpu_id,
                    str(input_path),
                    str(output_path),
                    model,
                    dtype,
                    max_length,
                    batch_size,
                    use_flash_attention,
                ),
            )
            process.start()
            processes.append(process)
            output_paths.append(output_path)

        for process in processes:
            process.join()
        failed_workers = [
            rank for rank, process in enumerate(processes) if process.exitcode != 0
        ]
        if failed_workers:
            raise RuntimeError(f"embedding workers failed: {failed_workers}")
        missing_outputs = [str(path) for path in output_paths if not path.is_file()]
        if missing_outputs:
            raise RuntimeError(f"embedding workers produced no output: {missing_outputs}")

        parts = [np.load(path) for path in output_paths]
        expected_rows = [end - start for start, end in ranges]
        if any(part.ndim != 2 for part in parts):
            raise RuntimeError("every embedding shard must be a two-dimensional matrix")
        if [part.shape[0] for part in parts] != expected_rows:
            raise RuntimeError("embedding shard row counts do not match input partitions")
        embedding_dims = {part.shape[1] for part in parts}
        if len(parts) != 8 or len(embedding_dims) != 1:
            raise RuntimeError("embedding shard dimensions are inconsistent")
        return np.concatenate(parts, axis=0).astype(np.float32, copy=False)
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
        shutil.rmtree(temporary_dir, ignore_errors=True)


def build_index(args: argparse.Namespace) -> None:
    catalog = load_catalog(args.dataset, args.dataset_revision, args.category)
    if args.limit is not None:
        catalog = catalog[: args.limit]
    if not catalog:
        raise ValueError("catalog is empty")

    sids = [item["sid"] for item in catalog]
    if any(not sid for sid in sids):
        raise ValueError("catalog contains an empty SID")

    texts = [item_index_text(item) for item in catalog]
    gpu_ids = parse_gpu_ids(args.gpus)
    print(
        f"Embedding {len(texts)} {args.category} items with {args.model} "
        f"across physical GPUs {','.join(gpu_ids)}...",
        flush=True,
    )
    embeddings = embed_documents_eight_gpu(
        texts=texts,
        model=args.model,
        gpu_ids=gpu_ids,
        dtype=args.dtype,
        max_length=args.max_length,
        batch_size=args.batch_size,
        use_flash_attention=args.use_flash_attention,
    )
    if embeddings.shape[0] != len(catalog):
        raise ValueError("encoder returned the wrong number of embeddings")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / "embeddings.npy", embeddings)
    with (output_dir / "metadata.json").open("w", encoding="utf-8") as file:
        json.dump(catalog, file, ensure_ascii=False)
    manifest = {
        "format_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": args.dataset,
        "dataset_revision": args.dataset_revision,
        "dataset_config": f"{args.category}_catalog",
        "dataset_split": "train",
        "category": args.category,
        "model_name_or_path": args.model,
        "query_instruction": args.query_instruction,
        "index_text_fields": list(INDEX_TEXT_FIELDS),
        "item_count": len(catalog),
        "unique_sid_count": len(set(sids)),
        "embedding_dim": int(embeddings.shape[1]),
        "normalized": True,
        "search": "exact_cosine",
        "build_world_size": 8,
        "build_gpu_ids": gpu_ids,
        "build_batch_size_per_gpu": args.batch_size,
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    print(f"Index written to {output_dir.resolve()}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Phase-3 interest retrieval index.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--dataset-revision", default=DEFAULT_DATASET_REVISION)
    parser.add_argument("--category", default=DEFAULT_CATEGORY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--query-instruction", default=DEFAULT_QUERY_INSTRUCTION)
    parser.add_argument("--output-dir", default="phase3_interest_retriever/indexes/Video_Games")
    parser.add_argument("--gpus", default=",".join(DEFAULT_GPU_IDS))
    parser.add_argument("--dtype", choices=("float32", "float16", "bfloat16"), default="bfloat16")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BUILD_BATCH_SIZE)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--use-flash-attention", action="store_true")
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    try:
        parse_gpu_ids(args.gpus)
    except ValueError as error:
        parser.error(str(error))
    return args


if __name__ == "__main__":
    build_index(parse_args())