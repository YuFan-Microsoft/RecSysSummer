"""Build the arXiv semantic-search index, one shard per domain.

For every domain in the config we walk its ``metadata.jsonl`` files across all
configured years, embed each paper's **title + abstract** with the embedding
model, and write two files::

    index_dir/<Domain>/embeddings.npy   float32  (num_papers, dim)  L2-normalised
    index_dir/<Domain>/metadata.json    list of paper dicts (same order as rows)

Sharding by domain matters because the domain filter is single-select: a search
only ever loads the one shard it needs, so even the large domains
(Computer_Science has ~650k papers) stay fast to query.

Multi-GPU: index building fans the embedding model out across every GPU listed
in ``index_gpus`` (2-7 by default). Each GPU runs one worker process on its own
contiguous slice of the papers; the main process then stitches the slices back
together in order. This makes the heavy embedding step several times faster.

Examples::

    python build_index.py                       # build every configured domain
    python build_index.py --domain Physics      # build just one domain
    python build_index.py --domain Medicine --limit 500   # quick smoke test
    python build_index.py --gpus 2 3            # override the GPUs to use
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from common import iter_domain_papers, load_config
from download_data import domain_has_data, download


# --------------------------------------------------------------------------
# Multi-GPU embedding
# --------------------------------------------------------------------------
def _embed_worker(
    gpu_id: int,
    model_path: str,
    cfg: dict,
    in_path: str,
    out_path: str,
    show_progress: bool,
) -> None:
    """Run in a fresh process: embed one slice of texts on a single GPU.

    Reads the slice from ``in_path`` (a JSON list of strings), writes the
    L2-normalised float32 embeddings to ``out_path`` (a .npy file).
    """
    # Imported inside the worker so each process initialises CUDA on its own.
    import numpy as np  # noqa: F811
    from embedder import Qwen3Embedder

    with open(in_path, "r", encoding="utf-8") as f:
        texts = json.load(f)

    embedder = Qwen3Embedder(
        model_path=model_path,
        device=f"cuda:{gpu_id}",
        dtype=cfg["dtype"],
        max_length=cfg["embedding_max_length"],
        use_flash_attention=cfg["use_flash_attention"],
    )
    emb = embedder.encode(
        texts,
        batch_size=int(cfg["embedding_batch_size"]),
        show_progress=show_progress,
    ).numpy().astype(np.float32)
    np.save(out_path, emb)


def embed_texts_multi_gpu(
    texts: list[str],
    model_path: str,
    cfg: dict,
    gpus: list[int],
) -> np.ndarray:
    """Embed ``texts`` across several GPUs and return one (N, dim) matrix.

    The texts are split into ``len(gpus)`` contiguous slices (one per GPU). Each
    slice is embedded in its own process; the results are concatenated back in
    the original order, so row i of the output matches ``texts[i]``.
    """
    import torch.multiprocessing as mp

    n_workers = min(len(gpus), len(texts))
    if n_workers <= 1:
        # Single-GPU fallback: no need to spawn processes.
        from embedder import Qwen3Embedder

        embedder = Qwen3Embedder(
            model_path=model_path,
            device=f"cuda:{gpus[0]}",
            dtype=cfg["dtype"],
            max_length=cfg["embedding_max_length"],
            use_flash_attention=cfg["use_flash_attention"],
        )
        return embedder.encode(
            texts,
            batch_size=int(cfg["embedding_batch_size"]),
            show_progress=True,
        ).numpy().astype(np.float32)

    # Contiguous, order-preserving slices of the text indices.
    slices = [s for s in np.array_split(np.arange(len(texts)), n_workers) if len(s) > 0]

    tmp_dir = Path(tempfile.mkdtemp(prefix="arxiv_embed_"))
    ctx = mp.get_context("spawn")
    procs = []
    out_paths: list[str] = []
    try:
        for rank, idx in enumerate(slices):
            in_path = tmp_dir / f"in_{rank}.json"
            out_path = tmp_dir / f"out_{rank}.npy"
            with open(in_path, "w", encoding="utf-8") as f:
                json.dump([texts[i] for i in idx], f, ensure_ascii=False)

            gpu_id = gpus[rank]
            print(f"[index]   worker {rank}: GPU {gpu_id}, {len(idx)} papers")
            p = ctx.Process(
                target=_embed_worker,
                args=(gpu_id, model_path, cfg, str(in_path), str(out_path), rank == 0),
            )
            p.start()
            procs.append(p)
            out_paths.append(str(out_path))

        for p in procs:
            p.join()
        failed = [i for i, p in enumerate(procs) if p.exitcode != 0]
        if failed:
            raise RuntimeError(f"embedding worker(s) {failed} failed (see logs above)")

        parts = [np.load(op) for op in out_paths]
        return np.concatenate(parts, axis=0)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --------------------------------------------------------------------------
# Per-domain build
# --------------------------------------------------------------------------
def build_domain(
    cfg: dict,
    domain: str,
    years: list[int],
    out_dir: Path,
    gpus: list[int],
    limit: int | None = None,
) -> int:
    """Embed one domain and write its shard. Returns the number of papers indexed."""
    print(f"\n[index] === domain: {domain} ===")
    print(f"[index] reading papers from years: {years}")

    papers = list(iter_domain_papers(cfg["data_dir"], domain, years))
    if limit:
        papers = papers[:limit]
    if not papers:
        print(f"[index] no papers found for {domain}; skipping.")
        return 0
    print(f"[index] found {len(papers)} papers; embedding title + abstract "
          f"across GPUs {gpus} ...")

    texts = [p.index_text() for p in papers]
    embeddings = embed_texts_multi_gpu(texts, cfg["embedding_model_path"], cfg, gpus)

    out_dir.mkdir(parents=True, exist_ok=True)
    emb_path = out_dir / "embeddings.npy"
    meta_path = out_dir / "metadata.json"

    np.save(emb_path, embeddings)
    metadata = [p.to_dict() for p in papers]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    print(f"[index] saved embeddings -> {emb_path}  shape={embeddings.shape}")
    print(f"[index] saved metadata   -> {meta_path}  ({len(metadata)} papers)")
    return len(papers)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the arXiv search index.")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument(
        "--domain",
        default=None,
        help="Build only this domain (default: every domain in config).",
    )
    parser.add_argument(
        "--gpus",
        nargs="*",
        type=int,
        default=None,
        help="GPU ids to fan out over (default: index_gpus from config).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only index the first N papers of each domain (for quick tests).",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not auto-download missing data from Hugging Face; fail instead.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config)
    index_dir = Path(cfg["index_dir"]).expanduser()
    years = [int(y) for y in cfg["years"]]
    gpus = args.gpus if args.gpus else [int(g) for g in cfg.get("index_gpus", [2])]
    if not gpus:
        raise SystemExit("No GPUs configured. Set index_gpus in config or pass --gpus.")

    all_domains = list(cfg["domains"])
    if args.domain:
        if args.domain not in all_domains:
            raise SystemExit(
                f"--domain {args.domain!r} is not in config domains: {all_domains}"
            )
        domains = [args.domain]
    else:
        domains = all_domains

    # Ensure the corpus is present locally, pulling any missing domains from HF.
    data_dir = Path(cfg["data_dir"]).expanduser()
    missing = [d for d in domains if not domain_has_data(data_dir, d, years)]
    if missing:
        if args.no_download:
            raise SystemExit(
                f"[index] ERROR: no local data for {missing} under {data_dir.resolve()} "
                f"and --no-download was set. Run `python download_data.py` first."
            )
        repo_id = cfg.get("hf_repo_id", "yufan/arxiv-metadata-2020-2026")
        print(f"[index] {len(missing)} domain(s) missing locally -> downloading from HF: {missing}")
        download(repo_id, data_dir, domains=missing, years=years)

    print(f"[index] embedding model: {cfg['embedding_model_path']}")
    print(f"[index] fanning out over GPUs: {gpus}")

    total = 0
    for domain in domains:
        total += build_domain(
            cfg=cfg,
            domain=domain,
            years=years,
            out_dir=index_dir / domain,
            gpus=gpus,
            limit=args.limit,
        )

    if total == 0:
        raise SystemExit(
            f"[index] ERROR: indexed 0 papers. Checked data_dir = {data_dir.resolve()} "
            f"(exists={data_dir.exists()}). Make sure the corpus is downloaded there "
            f"(`python download_data.py`) and that hf_repo_id / data_dir are correct."
        )

    print(f"\n[index] done. indexed {total} papers across {len(domains)} domain(s).")


if __name__ == "__main__":
    main()
