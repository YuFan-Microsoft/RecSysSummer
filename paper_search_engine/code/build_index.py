"""Build the semantic search index.

Walks every ``.md`` paper under ``data_dir``, embeds it with Qwen3-Embedding-8B,
and writes the embedding matrix plus paper metadata to ``index_dir``::

    index_dir/
        embeddings.npy     float32  (num_papers, dim)   L2-normalised
        metadata.json      list of paper dicts (same order as embeddings)

Run once (or whenever the paper folder changes)::

    python build_index.py
    python build_index.py --data-dir /path/to/papers --config config.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from common import iter_papers, load_config
from embedder import Qwen3Embedder


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the paper search index.")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--data-dir", default=None, help="Override data_dir from config")
    parser.add_argument("--index-dir", default=None, help="Override index_dir from config")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Only rewrite metadata.json (no re-embedding). The paper set must "
        "match the existing embeddings.npy.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    data_dir = args.data_dir or cfg["data_dir"]
    index_dir = Path(args.index_dir or cfg["index_dir"]).expanduser()
    index_dir.mkdir(parents=True, exist_ok=True)

    print(f"[index] scanning papers under: {data_dir}")
    papers = list(iter_papers(data_dir))
    if not papers:
        raise SystemExit(f"No .md papers found under {data_dir!r}. Check data_dir.")
    print(f"[index] found {len(papers)} papers")

    emb_path = index_dir / "embeddings.npy"
    meta_path = index_dir / "metadata.json"

    if args.metadata_only:
        # Fast path: refresh metadata without touching the GPU / embeddings.
        if not emb_path.exists():
            raise SystemExit(
                f"{emb_path} not found. Run a full build first (without --metadata-only)."
            )
        n_emb = np.load(emb_path, mmap_mode="r").shape[0]
        if n_emb != len(papers):
            raise SystemExit(
                f"Paper count ({len(papers)}) != existing embeddings ({n_emb}). "
                "The paper set changed; run a full rebuild instead."
            )
        metadata = [p.to_dict() for p in papers]
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)
        print(f"[index] metadata-only: rewrote {meta_path} ({len(metadata)} papers)")
        print("[index] done.")
        return

    print(f"[index] loading embedding model: {cfg['embedding_model_path']}")
    embedder = Qwen3Embedder(
        model_path=cfg["embedding_model_path"],
        device=cfg["embedding_device"],
        dtype=cfg["dtype"],
        max_length=cfg["embedding_max_length"],
        use_flash_attention=cfg["use_flash_attention"],
    )

    texts = [p.embed_text() for p in papers]
    print(f"[index] embedding {len(texts)} documents ...")
    embeddings = embedder.encode(
        texts,
        batch_size=cfg["embedding_batch_size"],
        show_progress=True,
    ).numpy().astype(np.float32)

    np.save(emb_path, embeddings)

    metadata = [p.to_dict() for p in papers]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    print(f"[index] saved embeddings -> {emb_path}  shape={embeddings.shape}")
    print(f"[index] saved metadata   -> {meta_path}  ({len(metadata)} papers)")
    print("[index] done.")


if __name__ == "__main__":
    main()
