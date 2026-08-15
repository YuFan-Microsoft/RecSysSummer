"""Build the arXiv semantic-search index, one shard per domain.

For every domain in the config we walk its ``metadata.jsonl`` files across all
configured years, embed each paper's **title + abstract** with the embedding
model, and write two files::

    index_dir/<Domain>/embeddings.npy   float32  (num_papers, dim)  L2-normalised
    index_dir/<Domain>/metadata.json    list of paper dicts (same order as rows)

Sharding by domain matters because the domain filter is single-select: a search
only ever loads the one shard it needs, so even the large domains
(Computer_Science has ~650k papers) stay fast to query.

Multi-GPU: with ``index_gpus: auto`` (the default) the build probes which GPUs
are currently IDLE (via nvidia-smi) and fans the embedding model out across ALL
of them; you can still force an explicit list in the config or with ``--gpus``.
Each GPU runs one worker process on its own contiguous slice of the papers; the
main process then stitches the slices back together in order. This makes the
heavy embedding step several times faster.

Examples::

    python build_index.py                       # build every configured domain
    python build_index.py --incremental         # embed only unseen arXiv IDs
    python build_index.py --domain Physics      # build just one domain
    python build_index.py --domain Medicine --limit 500   # quick smoke test
    python build_index.py --gpus 2 3            # override the idle-GPU autodetect
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from common import ArxivPaper, iter_domain_papers, load_config
from download_data import domain_has_data, download
from gpu_utils import describe_gpus, free_gpus


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
    incremental: bool = False,
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

    emb_path = out_dir / "embeddings.npy"
    meta_path = out_dir / "metadata.json"
    if incremental:
        if emb_path.exists() != meta_path.exists():
            raise RuntimeError(
                f"{domain}: incremental build requires both {emb_path.name} and "
                f"{meta_path.name}, but only one exists. Rebuild this shard without "
                "--incremental."
            )
        if emb_path.exists():
            return append_new_papers(
                cfg=cfg,
                domain=domain,
                papers=papers,
                emb_path=emb_path,
                meta_path=meta_path,
                gpus=gpus,
            )
        print("[index] no existing shard; building it in full.")

    print(f"[index] found {len(papers)} papers; embedding title + abstract "
          f"across GPUs {gpus} ...")

    texts = [p.index_text() for p in papers]
    embeddings = embed_texts_multi_gpu(texts, cfg["embedding_model_path"], cfg, gpus)

    out_dir.mkdir(parents=True, exist_ok=True)

    np.save(emb_path, embeddings)
    metadata = [p.to_dict() for p in papers]
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    print(f"[index] saved embeddings -> {emb_path}  shape={embeddings.shape}")
    print(f"[index] saved metadata   -> {meta_path}  ({len(metadata)} papers)")
    return len(papers)


def append_new_papers(
    cfg: dict,
    domain: str,
    papers: list[ArxivPaper],
    emb_path: Path,
    meta_path: Path,
    gpus: list[int],
) -> int:
    """Embed unseen arXiv IDs and append them to a validated existing shard."""
    with open(meta_path, "r", encoding="utf-8") as f:
        old_metadata = json.load(f)
    if not isinstance(old_metadata, list):
        raise RuntimeError(f"{domain}: {meta_path} must contain a JSON list")

    old_embeddings = np.load(emb_path, mmap_mode="r")
    if old_embeddings.ndim != 2:
        raise RuntimeError(
            f"{domain}: expected a 2-D embedding matrix, got shape {old_embeddings.shape}"
        )
    if old_embeddings.shape[0] != len(old_metadata):
        raise RuntimeError(
            f"{domain}: embeddings rows ({old_embeddings.shape[0]}) do not match "
            f"metadata rows ({len(old_metadata)})"
        )

    old_ids: list[str] = []
    for position, item in enumerate(old_metadata):
        if not isinstance(item, dict):
            raise RuntimeError(f"{domain}: metadata row {position} is not an object")
        arxiv_id = str(item.get("arxiv_id") or "").strip()
        if not arxiv_id:
            raise RuntimeError(f"{domain}: metadata row {position} has no arxiv_id")
        old_ids.append(arxiv_id)
    if len(set(old_ids)) != len(old_ids):
        raise RuntimeError(f"{domain}: existing metadata contains duplicate arxiv_id values")

    seen_ids = set(old_ids)
    new_papers: list[ArxivPaper] = []
    for paper in papers:
        arxiv_id = paper.arxiv_id.strip()
        if not arxiv_id:
            raise RuntimeError(f"{domain}: source paper has no arxiv_id: {paper.title!r}")
        if arxiv_id not in seen_ids:
            seen_ids.add(arxiv_id)
            new_papers.append(paper)

    if not new_papers:
        print(f"[index] existing shard is current ({len(old_metadata)} papers).")
        return 0

    print(
        f"[index] existing={len(old_metadata)}, new={len(new_papers)}; "
        f"embedding only new papers across GPUs {gpus} ..."
    )
    new_embeddings = np.asarray(
        embed_texts_multi_gpu(
            [paper.index_text() for paper in new_papers],
            cfg["embedding_model_path"],
            cfg,
            gpus,
        ),
        dtype=np.float32,
    )
    if new_embeddings.ndim != 2 or new_embeddings.shape[0] != len(new_papers):
        raise RuntimeError(
            f"{domain}: expected {len(new_papers)} new embedding rows, "
            f"got shape {new_embeddings.shape}"
        )
    if new_embeddings.shape[1] != old_embeddings.shape[1]:
        raise RuntimeError(
            f"{domain}: new embedding dimension {new_embeddings.shape[1]} does not "
            f"match existing dimension {old_embeddings.shape[1]}"
        )

    out_dir = emb_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    emb_tmp = tempfile.NamedTemporaryFile(
        prefix="embeddings.", suffix=".npy", dir=out_dir, delete=False
    )
    meta_tmp = tempfile.NamedTemporaryFile(
        prefix="metadata.", suffix=".json", dir=out_dir, delete=False
    )
    emb_tmp_path = Path(emb_tmp.name)
    meta_tmp_path = Path(meta_tmp.name)
    emb_tmp.close()
    meta_tmp.close()

    try:
        combined = np.lib.format.open_memmap(
            emb_tmp_path,
            mode="w+",
            dtype=np.float32,
            shape=(
                old_embeddings.shape[0] + new_embeddings.shape[0],
                old_embeddings.shape[1],
            ),
        )
        chunk_size = 10_000
        for start in range(0, old_embeddings.shape[0], chunk_size):
            end = min(start + chunk_size, old_embeddings.shape[0])
            combined[start:end] = old_embeddings[start:end]
        combined[old_embeddings.shape[0]:] = new_embeddings
        combined.flush()
        del combined

        metadata = old_metadata + [paper.to_dict() for paper in new_papers]
        with open(meta_tmp_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)

        os.replace(emb_tmp_path, emb_path)
        os.replace(meta_tmp_path, meta_path)
    finally:
        emb_tmp_path.unlink(missing_ok=True)
        meta_tmp_path.unlink(missing_ok=True)

    final_shape = (len(old_metadata) + len(new_papers), old_embeddings.shape[1])
    print(f"[index] updated embeddings -> {emb_path}  shape={final_shape}")
    print(f"[index] updated metadata   -> {meta_path}  ({final_shape[0]} papers)")
    return len(new_papers)


def _resolve_index_gpus(args, cfg: dict) -> list[int]:
    """Decide which GPUs to fan out over: explicit ``--gpus`` wins; otherwise
    ``index_gpus: auto`` autodetects every idle GPU, or an explicit config list
    is used verbatim."""
    if args.gpus:
        return [int(g) for g in args.gpus]

    reserved = [int(x) for x in cfg.get("reserved_gpus", [])]
    mem_max_pct = float(cfg.get("gpu_free_mem_max_pct", 1))
    util_max_pct = float(cfg.get("gpu_free_util_max_pct", 10))
    setting = cfg.get("index_gpus", "auto")

    if isinstance(setting, str) and setting.strip().lower() == "auto":
        print(f"[index] gpu status: {describe_gpus(reserved)}")
        try:
            gpus = free_gpus(
                reserved=reserved,
                mem_used_max_pct=mem_max_pct,
                util_max_pct=util_max_pct,
            )
        except RuntimeError as exc:
            raise SystemExit(
                f"[index] auto GPU detection failed: {exc}. Set index_gpus to an "
                f"explicit list in the config or pass --gpus."
            )
        if not gpus:
            raise SystemExit(
                "[index] no idle GPUs found (all in use). Wait for one to free up, "
                "loosen gpu_free_mem_max_pct / gpu_free_util_max_pct, or pass --gpus."
            )
        print(f"[index] auto-selected idle GPUs: {gpus}")
        return gpus

    return [int(g) for g in setting]


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
        help="GPU ids to fan out over (default: autodetect idle GPUs / index_gpus).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only index the first N papers of each domain (for quick tests).",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Append only arXiv IDs not already present in each existing shard.",
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
    gpus = _resolve_index_gpus(args, cfg)

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
            incremental=args.incremental,
        )

    if total == 0:
        if args.incremental:
            print("\n[index] done. Existing shards are already current.")
            return
        raise SystemExit(
            f"[index] ERROR: indexed 0 papers. Checked data_dir = {data_dir.resolve()} "
            f"(exists={data_dir.exists()}). Make sure the corpus is downloaded there "
            f"(`python download_data.py`) and that hf_repo_id / data_dir are correct."
        )

    action = "added" if args.incremental else "indexed"
    print(f"\n[index] done. {action} {total} papers across {len(domains)} domain(s).")


if __name__ == "__main__":
    main()
