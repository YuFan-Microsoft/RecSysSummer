"""Authoritative ACL main-conference lists from the ACL Anthology, with arXiv links.

ACL does not use OpenReview, so its authoritative record is the ACL Anthology.
This parses the Anthology XML (long + short = main conference; demos/srw/tutorials
are excluded) and attaches an arXiv id/url by matching titles against a local
arXiv dump, mirroring fetch_openreview.py.

Usage:
    python3 fetch_acl_anthology.py --years 2024,2025,2026
"""
import argparse
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from fetch_openreview import build_arxiv_index, normalize_title

ANTHOLOGY_XML = "https://raw.githubusercontent.com/acl-org/acl-anthology/master/data/xml/{year}.acl.xml"
# Only the main-conference volumes; skip demos / student research / tutorials.
MAIN_VOLUMES = {"long", "short"}


def _text(element) -> str:
    """Flatten an XML element's text (handles inline markup like <fixed-case>)."""
    return "".join(element.itertext()).strip() if element is not None else ""


def _author_name(author) -> str:
    first = _text(author.find("first"))
    last = _text(author.find("last"))
    return f"{first} {last}".strip()


def fetch_acl_year(year: int) -> list:
    """Return (anthology_id, paper_dict) for all main-conference ACL papers in a year."""
    url = ANTHOLOGY_XML.format(year=year)
    raw = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
    ).read()
    root = ET.fromstring(raw)
    papers = []
    for volume in root.findall("volume"):
        vid = volume.get("id")
        if vid not in MAIN_VOLUMES:
            continue
        for paper in volume.findall("paper"):
            anth_id = _text(paper.find("url")) or f"{year}.acl-{vid}.{paper.get('id')}"
            papers.append((vid, anth_id, paper))
    return papers


def main():
    parser = argparse.ArgumentParser(description="ACL Anthology main-conference lists + arXiv links.")
    parser.add_argument("--years", default="2024,2025,2026", help="Comma-separated years.")
    parser.add_argument("--arxiv-dump", type=Path, default=Path("papers/top_venues_papers.json"))
    parser.add_argument("--output", type=Path, default=Path("papers/acl_accepted.json"))
    args = parser.parse_args()

    years = [int(y) for y in args.years.split(",")]
    args.output.parent.mkdir(parents=True, exist_ok=True)

    arxiv_index = build_arxiv_index(args.arxiv_dump)
    print(f"Loaded arXiv index: {len(arxiv_index)} titles from {args.arxiv_dump}")

    records = {}
    for year in years:
        try:
            papers = fetch_acl_year(year)
        except Exception as exc:
            print(f"ACL {year}: skipped ({type(exc).__name__}: {exc})")
            continue
        matched = 0
        for vid, anth_id, paper in papers:
            title = _text(paper.find("title"))
            hit = arxiv_index.get(normalize_title(title))
            arxiv_id = hit[0] if hit else None
            if hit:
                matched += 1
            records[anth_id] = {
                "title": title,
                "authors": ", ".join(_author_name(a) for a in paper.findall("author")),
                "abstract": _text(paper.find("abstract")).replace("\n", " "),
                "venue": f"ACL {year} {vid}",
                "venue_short": f"ACL{year}",
                "decision": vid,  # long / short
                "anthology_url": f"https://aclanthology.org/{anth_id}/",
                "arxiv_id": arxiv_id,
                "arxiv_url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
            }
        rate = 100 * matched / len(papers) if papers else 0
        print(f"ACL {year}: {len(papers)} main papers, arXiv matched {matched} ({rate:.1f}%)")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump({"ACL": records}, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
