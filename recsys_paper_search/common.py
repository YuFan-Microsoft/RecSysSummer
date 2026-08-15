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
# filename layout: {Company}_{venue}_{YYYYMMDD}_{Title}.md
_FNAME_RE = re.compile(r"^(?P<company>[^_]+)_(?P<venue>[^_]+)_(?P<date>\d{8})_")

# A paper body is organised into numbered sections, e.g.
#   "## § 5 - Method and full pipeline"
# The separator may be a hyphen, en-dash or em-dash and the casing varies.
_SECTION_RE = re.compile(
    r"^##\s+§\s*\d+\s*[-–—]\s*(?P<name>.+?)\s*$",
    re.MULTILINE,
)

# pretty display names for the venue token in the filename
_VENUE_NAMES = {
    "arxiv": "arXiv", "sigir": "SIGIR", "kdd": "KDD", "www": "WWW",
    "recsys": "RecSys", "aaai": "AAAI", "cikm": "CIKM", "wsdm": "WSDM",
    "neurips": "NeurIPS", "iclr": "ICLR", "umap": "UMAP", "icml": "ICML",
    "acmmm": "ACM MM", "tors": "TORS", "tois": "TOIS", "tmlr": "TMLR",
    "tkde": "TKDE", "sigmod": "SIGMOD", "ijcai": "IJCAI", "acl": "ACL",
}


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
    venue: str = ""        # display venue from filename (e.g. "SIGIR", "arXiv")
    is_preprint: bool = False  # True when the venue is arXiv (not yet accepted)
    pub_date: str = ""     # ISO date from filename, e.g. "2025-04-06"
    pub_year: str = ""     # year only, e.g. "2025"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def index_text(self, selected_sections: list[str] | None = None) -> str:
        """Text fed to the embedder / reranker.

        When ``selected_sections`` is given, only those sections of the paper
        are kept (the title is always prepended); otherwise the full body is
        used. This lets the search engine index the signal-bearing sections
        (problem / intuition / method / ...) and ignore noise such as the
        speculative "thought process", critique, or "future work" sections.
        """
        if selected_sections:
            return select_sections_text(self.title, self.content, selected_sections)
        return f"{self.title}\n\n{self.content}".strip()


def _normalize_section(name: str) -> str:
    """Lower-case a section name and strip punctuation / extra whitespace."""
    name = name.replace("\u2019", "'").strip().rstrip(".")
    return re.sub(r"\s+", " ", name).lower()


def extract_sections(content: str) -> list[tuple[str, str]]:
    """Split a paper body into ``(normalized_name, body_text)`` pairs, in order."""
    matches = list(_SECTION_RE.finditer(content))
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append((_normalize_section(m.group("name")), body))
    return sections


def select_sections_text(title: str, content: str, selected: list[str]) -> str:
    """Build indexing/reranking text from a curated subset of sections.

    Only sections whose (normalized) names appear in ``selected`` are kept; they
    are emitted in document order with the title prepended. Falls back to the
    full body when none of the configured sections are found, so the engine
    stays robust to occasional format drift.
    """
    wanted = {_normalize_section(s) for s in selected}
    parts = [body for name, body in extract_sections(content) if name in wanted and body]
    joined = "\n\n".join(parts).strip() or content.strip()
    return f"{title}\n\n{joined}".strip()


def _parse_filename_meta(stem: str) -> tuple[str, bool, str, str]:
    """Extract (venue, is_preprint, pub_date, pub_year) from the file stem.

    Returns empty strings when the filename does not match the expected
    ``Company_venue_YYYYMMDD_Title`` layout.
    """
    m = _FNAME_RE.match(stem)
    if not m:
        return "", False, "", ""
    token = m.group("venue").lower()
    venue = _VENUE_NAMES.get(token, m.group("venue").upper())
    is_preprint = token == "arxiv"
    d = m.group("date")
    pub_date = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
    return venue, is_preprint, pub_date, d[0:4]


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

    venue, is_preprint, pub_date, pub_year = _parse_filename_meta(md_path.stem)

    return Paper(
        paper_id=paper_id,
        title=title,
        company=_derive_company(md_path, data_root),
        arxiv_url=arxiv_url,
        path=str(md_path),
        content=text.strip(),
        venue=venue,
        is_preprint=is_preprint,
        pub_date=pub_date,
        pub_year=pub_year,
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
