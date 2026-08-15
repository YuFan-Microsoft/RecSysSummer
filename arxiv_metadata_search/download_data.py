#!/usr/bin/env python3
"""Download the arXiv metadata corpus from Hugging Face into ``data_dir``.

The dataset lives at
`yufan/arxiv-metadata-2020-2026 <https://huggingface.co/datasets/yufan/arxiv-metadata-2020-2026>`_
and is stored as ``<Domain>/<year>/metadata.jsonl`` (one JSON paper per line).
This script pulls those ``metadata.jsonl`` files into the local ``data_dir`` set
in ``config.yaml`` so ``build_index.py`` can read them.

Only the ``metadata.jsonl`` files are downloaded (READMEs / git files are
skipped). By default it grabs **all domains and all years** (~2.3 GB).

Examples::

    python download_data.py                       # everything (all domains/years)
    python download_data.py --domain Physics      # one domain, all years
    python download_data.py --domain Medicine --years 2024 2025
    python download_data.py --data-dir /data/arxiv_hf
"""

from __future__ import annotations

import argparse
from pathlib import Path

from common import load_config


def build_patterns(domains: list[str] | None, years: list[int] | None) -> list[str]:
    """Glob patterns selecting the metadata.jsonl files to download.

    Patterns follow the HF layout ``<Domain>/<year>/metadata.jsonl``. When
    ``domains`` or ``years`` is empty we use ``*`` to match all of them.
    """
    doms = domains or ["*"]
    yrs = [str(y) for y in years] if years else ["*"]
    return [f"{d}/{y}/metadata.jsonl" for d in doms for y in yrs]


def domain_has_data(data_dir: str | Path, domain: str, years: list[int]) -> bool:
    """True if at least one ``metadata.jsonl`` exists for this domain on disk.

    Accepts either the HF layout (``<Domain>/<year>/``) or the legacy local
    layout (``<year>/<Domain>/``), matching what ``common._jsonl_path`` reads.
    """
    root = Path(data_dir).expanduser()
    for y in years:
        hf = root / domain / str(y) / "metadata.jsonl"
        legacy = root / str(y) / domain / "metadata.jsonl"
        if hf.exists() or legacy.exists():
            return True
    return False


def download(
    repo_id: str,
    data_dir: str | Path,
    domains: list[str] | None = None,
    years: list[int] | None = None,
) -> None:
    """Download the selected metadata.jsonl files from Hugging Face into ``data_dir``."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise SystemExit(
            "huggingface_hub is not installed. Run: pip install huggingface_hub"
        )

    data_dir = Path(data_dir).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    patterns = build_patterns(domains, years)
    print(f"[download] repo:      {repo_id}")
    print(f"[download] into:      {data_dir.resolve()}")
    print(f"[download] patterns:  {patterns}")

    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=str(data_dir),
        allow_patterns=patterns,
    )
    print("[download] done.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Download arXiv metadata from Hugging Face.")
    ap.add_argument("--config", default=None, help="Path to config.yaml")
    ap.add_argument("--repo", default=None, help="Override hf_repo_id from config")
    ap.add_argument("--data-dir", default=None, help="Override data_dir from config")
    ap.add_argument(
        "--domain",
        action="append",
        default=None,
        help="Download only this domain (repeatable). Default: all domains.",
    )
    ap.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=None,
        help="Download only these years, e.g. --years 2024 2025. Default: all.",
    )
    args = ap.parse_args()

    cfg = load_config(args.config)
    repo_id = args.repo or cfg.get("hf_repo_id", "yufan/arxiv-metadata-2020-2026")
    data_dir = args.data_dir or cfg["data_dir"]
    download(repo_id, data_dir, domains=args.domain, years=args.years)


if __name__ == "__main__":
    main()
