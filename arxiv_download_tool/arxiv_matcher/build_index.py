"""Build the arXiv title search index.

Loads the arXiv title index TSV, embeds every title with Qwen3-Embedding, and
writes the embedding matrix plus aligned metadata to ``index_dir``::

    index_dir/
        embeddings.npy     float32  (num_titles, dim)   L2-normalised
        metadata.jsonl     one {"arxiv_id","title","surname"} per line

Run once (or whenever the TSV changes)::

    python build_index.py
    python build_index.py --corpus ./arxiv_title_index.tsv --config config.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from common import load_config, load_corpus
from embedder import Qwen3Embedder


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the arXiv title search index.")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--corpus", default=None, help="Override corpus_path from config")
    parser.add_argument("--index-dir", default=None, help="Override index_dir from config")
    args = parser.parse_args()

    cfg = load_config(args.config)
    corpus_path = args.corpus or cfg["corpus_path"]
    index_dir = Path(args.index_dir or cfg["index_dir"]).expanduser()
    index_dir.mkdir(parents=True, exist_ok=True)

    print(f"[index] loading corpus: {corpus_path}")
    entries = load_corpus(corpus_path)
    if not entries:
        raise SystemExit(f"No titles loaded from {corpus_path!r}. Check corpus_path.")
    print(f"[index] loaded {len(entries)} titles")

    print(f"[index] loading embedding model: {cfg['embedding_model_path']}")
    embedder = Qwen3Embedder(
        model_path=cfg["embedding_model_path"],
        device=cfg["embedding_device"],
        dtype=cfg["dtype"],
        max_length=cfg["embedding_max_length"],
        use_flash_attention=cfg["use_flash_attention"],
    )

    titles = [e.title for e in entries]
    print(f"[index] embedding {len(titles)} titles ...")
    embeddings = embedder.encode(
        titles,
        batch_size=cfg["embedding_batch_size"],
        show_progress=True,
    ).numpy().astype(np.float32)

    emb_path = index_dir / "embeddings.npy"
    meta_path = index_dir / "metadata.jsonl"
    np.save(emb_path, embeddings)
    with open(meta_path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(
                {"arxiv_id": e.arxiv_id, "title": e.title, "surname": e.surname},
                ensure_ascii=False,
            ) + "\n")

    print(f"[index] saved embeddings -> {emb_path}  shape={embeddings.shape}")
    print(f"[index] saved metadata   -> {meta_path}  ({len(entries)} titles)")
    print("[index] done.")


if __name__ == "__main__":
    main()
