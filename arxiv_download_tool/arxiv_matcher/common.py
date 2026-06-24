"""Shared utilities for the arXiv title matcher.

The corpus is the local arXiv title index TSV (one paper per line)::

    <arxiv_id>\\t<normalized_title>\\t<first_author_surname>

The titles are already normalized (lowercased, alphanumeric, single-spaced) by
the harvester, so queries are normalized the same way before embedding / edit
distance, keeping query and document representations comparable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Lowercase + collapse non-alphanumerics to single spaces (matches the TSV norm).
_NORM_RE = re.compile(r"[^a-z0-9]+")


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the YAML config, defaulting to ``config.yaml`` next to this file."""
    if path is None:
        path = Path(__file__).resolve().parent / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_title(title: str) -> str:
    """Lowercase and strip to alphanumerics; identical to the arXiv index norm."""
    return _NORM_RE.sub(" ", (title or "").lower()).strip()


def surname_of(author: str) -> str:
    """Lowercase surname (last token) of a single author name.

    ``"Shashank Gupta 0001"`` -> ``"gupta"``; ``"Maarten de Rijke"`` -> ``"rijke"``.
    """
    name = re.sub(r"\s+\d{4}$", "", (author or "").strip())  # drop dblp homonym id
    tokens = normalize_title(name).split()
    return tokens[-1] if tokens else ""


def first_author(authors: str) -> str:
    """First author from a comma-separated author string."""
    return (authors or "").split(",")[0].strip()


def surnames_match(query_author: str, cand_surname: str) -> bool:
    """Whether a query author and a candidate surname plausibly refer to one person.

    ``cand_surname`` is the lowercased surname stored in the TSV. When the
    candidate surname is missing we do not block on it (title decides).
    """
    cand = (cand_surname or "").strip().lower()
    if not cand:
        return True
    qs = surname_of(query_author)
    if not qs:
        return True
    cand_last = cand.split()[-1]
    return qs == cand or qs == cand_last or qs in cand or cand_last in qs


def edit_distance(a: str, b: str) -> int:
    """Levenshtein distance between two strings (iterative, O(len(a)*len(b)))."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i]
        for j, cb in enumerate(b, start=1):
            cur.append(min(
                prev[j] + 1,        # deletion
                cur[j - 1] + 1,     # insertion
                prev[j - 1] + (ca != cb),  # substitution
            ))
        prev = cur
    return prev[-1]


def title_similarity(a: str, b: str) -> float:
    """Normalized title similarity in ``[0, 1]`` via edit distance ratio."""
    na, nb = normalize_title(a), normalize_title(b)
    if not na and not nb:
        return 1.0
    longest = max(len(na), len(nb))
    if longest == 0:
        return 0.0
    return 1.0 - edit_distance(na, nb) / longest


@dataclass
class CorpusEntry:
    arxiv_id: str
    title: str       # normalized title (as stored in the TSV)
    surname: str     # lowercased first-author surname


def load_corpus(tsv_path: str | Path) -> list[CorpusEntry]:
    """Load the arXiv title index TSV into a list of :class:`CorpusEntry`."""
    path = Path(tsv_path).expanduser()
    entries: list[CorpusEntry] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2 or not parts[1]:
                continue
            entries.append(CorpusEntry(
                arxiv_id=parts[0],
                title=parts[1],
                surname=parts[2] if len(parts) > 2 else "",
            ))
    return entries
