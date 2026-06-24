"""Fill arXiv ids into the DBLP accepted-paper JSON files using the title matcher.

Walks ``papers/<Venue>/<Year>.json`` (the reorganized accepted lists), and for
every record without an ``arxiv_id`` runs the title matcher with the paper title
and its first author. Accepted matches get ``arxiv_id`` / ``arxiv_url`` written
back in place (atomically).

Usage:
    python enrich_accepted.py --papers-dir ../papers
    python enrich_accepted.py --papers-dir ../papers --venues RecSys,SIGIR --years 2024,2025
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from common import first_author
from matcher import ArxivTitleMatcher


def atomic_write(path: Path, data: dict) -> None:
    """Write JSON to a temp file then rename over the target (crash-safe)."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def iter_json_files(papers_dir: Path, venues: set[str] | None, years: set[str] | None):
    """Yield ``<Venue>/<Year>.json`` files matching the venue/year filters."""
    for venue_dir in sorted(p for p in papers_dir.iterdir() if p.is_dir()):
        if venues and venue_dir.name not in venues:
            continue
        for jf in sorted(venue_dir.glob("*.json")):
            if years and jf.stem not in years:
                continue
            yield jf


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill arXiv ids into accepted JSONs.")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--papers-dir", default="../papers",
                        help="Directory holding <Venue>/<Year>.json files")
    parser.add_argument("--venues", default=None, help="Comma-separated venue filter")
    parser.add_argument("--years", default=None, help="Comma-separated year filter")
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-match records that already have an arxiv_id")
    args = parser.parse_args()

    papers_dir = Path(args.papers_dir).expanduser().resolve()
    venues = {v.strip() for v in args.venues.split(",")} if args.venues else None
    years = {y.strip() for y in args.years.split(",")} if args.years else None

    matcher = ArxivTitleMatcher(args.config)

    grand_total = grand_matched = 0
    for jf in iter_json_files(papers_dir, venues, years):
        with open(jf, encoding="utf-8") as f:
            data = json.load(f)
        papers = data[next(iter(data))]  # single top-level key wraps the records

        considered = matched = 0
        for rec in papers.values():
            if rec.get("arxiv_id") and not args.overwrite:
                continue
            considered += 1
            res = matcher.match(rec.get("title", ""), first_author(rec.get("authors", "")))
            if res.matched:
                rec["arxiv_id"] = res.arxiv_id
                rec["arxiv_url"] = res.arxiv_url
                matched += 1
            else:
                rec.setdefault("arxiv_id", None)
                rec.setdefault("arxiv_url", None)

        atomic_write(jf, data)
        grand_total += considered
        grand_matched += matched
        rate = 100 * matched / considered if considered else 0
        print(f"{jf.parent.name}/{jf.name}: matched {matched}/{considered} ({rate:.1f}%)")

    rate = 100 * grand_matched / grand_total if grand_total else 0
    print(f"=== total: matched {grand_matched}/{grand_total} ({rate:.1f}%) ===")


if __name__ == "__main__":
    main()
