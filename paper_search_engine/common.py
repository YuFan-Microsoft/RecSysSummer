"""Shared utilities: config loading and Markdown paper parsing.

A "paper" is a single ``.md`` file living somewhere under ``data_dir``. The
expected layout is::

    data_dir/
        Apple/
            Apple_arxiv_20260514_Fortress ....md
        Google/
            ....md

Each file starts with a ``# Title`` line followed by an ``**arXiv:** [url](url)``
line and then the body. We extract a small amount of structured metadata
(title, arxiv url, company) and keep the full text for embedding / display.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import yaml

# arxiv URL anywhere in the document, e.g. http://arxiv.org/abs/2605.15299v1
_ARXIV_RE = re.compile(r"https?://arxiv\.org/abs/[^\s\)\]]+")
# first markdown H1 used as the title
_TITLE_RE = re.compile(r"^\s*#\s+(.*\S)\s*$", re.MULTILINE)


def load_config(path: str | Path = None) -> dict[str, Any]:
    """Load the YAML config, defaulting to ``config.yaml`` next to this file."""
    if path is None:
        path = Path(__file__).resolve().parent / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Paper:
    """Structured view of one markdown paper."""

    paper_id: str          # stable id (relative path without extension)
    title: str
    company: str           # top-level folder name (e.g. "Apple")
    arxiv_url: str
    path: str              # absolute path to the .md file
    content: str           # full markdown body

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def embed_text(self) -> str:
        """Text fed to the embedding model (title helps disambiguate)."""
        return f"{self.title}\n\n{self.content}".strip()


def _derive_company(md_path: Path, data_root: Path) -> str:
    """First path component below the data root is treated as the company."""
    try:
        rel = md_path.relative_to(data_root)
        return rel.parts[0] if len(rel.parts) > 1 else "Unknown"
    except ValueError:
        return md_path.parent.name


def parse_paper(md_path: Path, data_root: Path) -> Paper | None:
    """Parse a single markdown file into a :class:`Paper` (or ``None`` if empty)."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    if not text.strip():
        return None

    title_match = _TITLE_RE.search(text)
    title = title_match.group(1).strip() if title_match else md_path.stem

    arxiv_match = _ARXIV_RE.search(text)
    arxiv_url = arxiv_match.group(0) if arxiv_match else ""

    rel = md_path.relative_to(data_root) if _is_relative(md_path, data_root) else md_path
    paper_id = str(rel.with_suffix(""))

    return Paper(
        paper_id=paper_id,
        title=title,
        company=_derive_company(md_path, data_root),
        arxiv_url=arxiv_url,
        path=str(md_path),
        content=text.strip(),
    )


def _is_relative(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def iter_papers(data_dir: str | Path):
    """Yield parsed :class:`Paper` objects for every ``.md`` file under ``data_dir``.

    ``README.md`` files (folder descriptions, not papers) are skipped.
    """
    data_root = Path(data_dir).expanduser().resolve()
    for md_path in sorted(data_root.rglob("*.md")):
        if md_path.name.lower() == "readme.md":
            continue
        paper = parse_paper(md_path, data_root)
        if paper is not None:
            yield paper
