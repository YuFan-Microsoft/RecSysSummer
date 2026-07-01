"""Shared utilities: config loading and arXiv metadata parsing.

The corpus lives under ``data_dir`` in this layout::

    data_dir/
        2020/
            Computer_Science/metadata.jsonl
            Physics/metadata.jsonl
            ...
        2021/
            ...

Every line of a ``metadata.jsonl`` file is one paper, a JSON object with (at
least) these fields::

    {
      "arxiv_id": "2512.25075",
      "title": "SpaceTimePilot: Generative Rendering of Dynamic Scenes ...",
      "authors": "Zhening Huang; Hyeonho Jeong; ...",
      "year": 2025,
      "publicationDate": "2025-12-31",
      "citationCount": 2,
      "influentialCitationCount": 1,
      "fieldsOfStudy": "Computer Science",
      "abstract": "We present SpaceTimePilot, a video diffusion model ..."
    }

We index the **title + abstract** of each paper and keep the rest of the fields
(year, citation count, ...) so the search can filter by year/domain and sort by
citation count.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterator

import yaml


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the YAML config, defaulting to ``config.yaml`` next to this file."""
    if path is None:
        path = Path(__file__).resolve().parent / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------------------------------------------------------
# Paper record
# --------------------------------------------------------------------------
@dataclass
class ArxivPaper:
    """A single arXiv paper, as parsed from one JSONL line."""

    arxiv_id: str
    title: str
    abstract: str
    authors: str
    year: int
    publication_date: str
    citation_count: int
    influential_citation_count: int
    domain: str  # the on-disk folder name, e.g. "Computer_Science"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def arxiv_url(self) -> str:
        return f"https://arxiv.org/abs/{self.arxiv_id}" if self.arxiv_id else ""

    def index_text(self) -> str:
        """Text fed to the embedder / reranker: title first, then abstract."""
        title = (self.title or "").strip()
        abstract = (self.abstract or "").strip()
        if abstract:
            return f"{title}\n\n{abstract}".strip()
        return title


def _to_int(value: Any, default: int = 0) -> int:
    """Best-effort int conversion (handles None / floats / numeric strings)."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_record(obj: dict[str, Any], domain: str) -> ArxivPaper | None:
    """Turn one JSON object into an :class:`ArxivPaper` (or ``None`` if unusable).

    A record is skipped only when it has no title AND no abstract, since there
    would be nothing to index.
    """
    title = (obj.get("title") or "").strip()
    abstract = (obj.get("abstract") or "").strip()
    if not title and not abstract:
        return None

    return ArxivPaper(
        arxiv_id=str(obj.get("arxiv_id") or "").strip(),
        title=title,
        abstract=abstract,
        authors=(obj.get("authors") or "").strip(),
        year=_to_int(obj.get("year"), default=0),
        publication_date=str(obj.get("publicationDate") or "").strip(),
        citation_count=_to_int(obj.get("citationCount"), default=0),
        influential_citation_count=_to_int(obj.get("influentialCitationCount"), default=0),
        domain=domain,
    )


def _jsonl_path(data_dir: Path, year: int, domain: str) -> Path:
    """Locate a domain's per-year JSONL, supporting both on-disk layouts.

    Hugging Face layout (default):  ``<Domain>/<year>/metadata.jsonl``
    Legacy local layout:            ``<year>/<Domain>/metadata.jsonl``

    Returns the first path that exists; if neither does, returns the HF path so
    callers can simply check ``.exists()``.
    """
    hf = data_dir / domain / str(year) / "metadata.jsonl"
    if hf.exists():
        return hf
    legacy = data_dir / str(year) / domain / "metadata.jsonl"
    if legacy.exists():
        return legacy
    return hf


def iter_domain_papers(
    data_dir: str | Path,
    domain: str,
    years: list[int],
) -> Iterator[ArxivPaper]:
    """Yield every paper of one ``domain`` across the requested ``years``.

    Missing ``<year>/<domain>/metadata.jsonl`` files are simply skipped, so it
    is safe to pass years that do not exist on disk for a given domain.
    """
    data_root = Path(data_dir).expanduser().resolve()
    for year in years:
        path = _jsonl_path(data_root, year, domain)
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                paper = parse_record(obj, domain)
                if paper is not None:
                    yield paper


def count_domain_papers(data_dir: str | Path, domain: str, years: list[int]) -> int:
    """Fast line-count of a domain's papers (for progress bars / sanity checks)."""
    data_root = Path(data_dir).expanduser().resolve()
    total = 0
    for year in years:
        path = _jsonl_path(data_root, year, domain)
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            total += sum(1 for line in f if line.strip())
    return total
