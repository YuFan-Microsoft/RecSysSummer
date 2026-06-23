"""Authoritative venue lists from OpenReview, enriched with arXiv links.

For a venue/year, this pulls the *full* accepted-paper list from OpenReview
(which already includes title/authors/abstract and the decision type, e.g.
poster/spotlight/oral) and then attaches an arXiv id/url when the paper can be
matched (by normalized title) against a local arXiv dump.

Why OpenReview: arXiv only sees papers whose authors uploaded *and* noted the
venue in the free-text comment (~40-60% coverage). OpenReview is the authoritative
accept list (100%). arXiv is used only to supplement a PDF/abstract link.

Usage:
    python3 fetch_openreview.py --venue ICLR --years 2024,2025,2026
"""
import argparse
import collections
import json
import re
import time
import urllib.request
from pathlib import Path

# OpenReview group id template per venue. Accepted papers carry
# content.venueid == "<Group>.cc/<year>/Conference".
OPENREVIEW_GROUP = {
    "ICLR": "ICLR.cc/{year}/Conference",
    "NeurIPS": "NeurIPS.cc/{year}/Conference",
    "ICML": "ICML.cc/{year}/Conference",
}


def _value(content: dict, key: str):
    """OpenReview API v2 wraps each field as {'value': ...}; unwrap it."""
    v = content.get(key)
    return v.get("value") if isinstance(v, dict) else v


def fetch_accepted(venueid: str) -> list:
    """Page through every accepted note for an OpenReview venueid."""
    notes, offset = [], 0
    while True:
        url = (
            f"https://api2.openreview.net/notes?content.venueid={venueid}"
            f"&limit=1000&offset={offset}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        batch = json.load(urllib.request.urlopen(req, timeout=60)).get("notes", [])
        if not batch:
            break
        notes += batch
        offset += len(batch)
        if len(batch) < 1000:
            break
        time.sleep(1)  # be polite to the API
    return notes


def normalize_title(title: str) -> str:
    """Lowercase and strip to alphanumerics for robust title matching."""
    return re.sub(r"[^a-z0-9]+", " ", (title or "").lower()).strip()


def build_arxiv_index(dump_path: Path) -> dict:
    """Map normalized title -> (arxiv_id, paper) from a local arXiv dump."""
    index = {}
    if not dump_path.exists():
        return index
    data = json.load(open(dump_path, encoding="utf-8"))
    for topic_papers in data.values():
        for arxiv_id, paper in topic_papers.items():
            index[normalize_title(paper.get("title"))] = (arxiv_id, paper)
    return index


def main():
    parser = argparse.ArgumentParser(description="OpenReview accepted lists + arXiv links.")
    parser.add_argument("--venue", required=True, choices=sorted(OPENREVIEW_GROUP))
    parser.add_argument("--years", default="2024,2025,2026", help="Comma-separated years.")
    parser.add_argument("--arxiv-dump", type=Path, default=Path("papers/top_venues_papers.json"))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    years = [int(y) for y in args.years.split(",")]
    output = args.output or Path(f"papers/{args.venue.lower()}_accepted.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    arxiv_index = build_arxiv_index(args.arxiv_dump)
    print(f"Loaded arXiv index: {len(arxiv_index)} titles from {args.arxiv_dump}")

    records = {}
    for year in years:
        venueid = OPENREVIEW_GROUP[args.venue].format(year=year)
        notes = fetch_accepted(venueid)
        matched = 0
        for note in notes:
            content = note["content"]
            title = _value(content, "title")
            venue_str = _value(content, "venue") or ""
            hit = arxiv_index.get(normalize_title(title))
            if hit:
                matched += 1
                arxiv_id, _ = hit
            else:
                arxiv_id = None
            records[note["id"]] = {
                "title": title,
                "authors": ", ".join(_value(content, "authors") or []),
                "abstract": (_value(content, "abstract") or "").replace("\n", " "),
                "venue": venue_str,                       # e.g. "ICLR 2024 poster"
                "venue_short": f"{args.venue}{year}",
                "decision": venue_str.split()[-1] if venue_str else None,  # poster/spotlight/oral
                "openreview_url": f"https://openreview.net/forum?id={note['id']}",
                "arxiv_id": arxiv_id,
                "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
            }
        rate = 100 * matched / len(notes) if notes else 0
        print(f"{args.venue} {year}: {len(notes)} accepted, arXiv matched {matched} ({rate:.1f}%)")

    with open(output, "w", encoding="utf-8") as f:
        json.dump({args.venue: records}, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(records)} records to {output}")


if __name__ == "__main__":
    main()
