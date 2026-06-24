"""Fill empty arxiv_url fields in papers/<Venue>/<Year>.json via the live matcher API.

Each paper JSON is a list of records with an ``arxiv_url`` (may be null) and a
comma-separated ``authors`` string. For every record missing an arxiv_url we call
the Gradio ``do_match`` endpoint with (title, first_author), parse the ranked
candidate table, and accept the top-1 arXiv id when either:

  * the normalized-title edit-distance similarity >= --title-accept, OR
  * the reranker score >= --rerank-accept AND the first-author surname agrees
    (covers preprint -> camera-ready retitling, where the title changed but the
    paper and first author are the same).

Usage:
    python enrich_via_api.py --base https://xxxx.gradio.live
    python enrich_via_api.py --base https://xxxx.gradio.live --venues CIKM --years 2025
    python enrich_via_api.py --base https://xxxx.gradio.live --limit 5 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import time
import urllib.request
from pathlib import Path

from common import first_author, surnames_match

_TITLE_SIM_RE = re.compile(r"title_sim\s+([\d.]+)")
# A markdown table row: | 1 | 1.000 | 0.853 | `2502.12510` | candidate title | Surname |
_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*[\d.]+\s*\|\s*`([^`]+)`\s*\|[^|]*\|\s*([^|]*?)\s*\|"
)


def atomic_write(path: Path, data) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def call_matcher(base: str, title: str, author: str, tries: int = 4) -> str:
    """Call the Gradio do_match endpoint and return the markdown result string."""
    body = json.dumps({"data": [title, author]}).encode()
    for attempt in range(tries):
        try:
            req = urllib.request.Request(
                base + "/gradio_api/call/do_match", data=body,
                headers={"Content-Type": "application/json", "User-Agent": "M"},
            )
            eid = json.loads(urllib.request.urlopen(req, timeout=60).read())["event_id"]
            req2 = urllib.request.Request(
                base + f"/gradio_api/call/do_match/{eid}", headers={"User-Agent": "M"}
            )
            raw = urllib.request.urlopen(req2, timeout=180).read().decode()
            data = None
            for line in raw.splitlines():
                if line.startswith("data:"):
                    data = line[5:].strip()
            out = json.loads(data)
            return out[0] if isinstance(out, list) else out
        except Exception as e:  # transient tunnel/network error -> retry
            wait = 3 * (attempt + 1)
            print(f"    API error ({type(e).__name__}); retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError("matcher API failed after retries")


def parse_result(md: str):
    """Return (title_sim, top1_rerank, top1_id, top1_surname) from the markdown."""
    m = _TITLE_SIM_RE.search(md)
    title_sim = float(m.group(1)) if m else 0.0
    top = None
    for row in _ROW_RE.finditer(md):
        if row.group(1) == "1":
            top = (float(row.group(2)), row.group(3).strip(), row.group(4).strip())
            break
    if top is None:
        return title_sim, 0.0, None, ""
    rerank, aid, surname = top
    return title_sim, rerank, aid, surname


def decide(title_sim, rerank, surname, query_author, title_accept, rerank_accept):
    """Acceptance rule: strong title OR (strong rerank AND real author match)."""
    if title_sim >= title_accept:
        return True
    if rerank >= rerank_accept and surname and surnames_match(query_author, surname):
        return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Fill arxiv_url via the matcher API.")
    ap.add_argument("--base", required=True, help="Gradio app base URL")
    ap.add_argument("--papers-dir", default="../papers")
    ap.add_argument("--venues", default=None, help="Comma-separated venue filter")
    ap.add_argument("--years", default=None, help="Comma-separated year filter")
    ap.add_argument("--title-accept", type=float, default=0.90)
    ap.add_argument("--rerank-accept", type=float, default=0.97)
    ap.add_argument("--limit", type=int, default=0, help="Process at most N records (0=all)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files")
    ap.add_argument("--sleep", type=float, default=0.0, help="Seconds between API calls")
    ap.add_argument("--save-every", type=int, default=10,
                    help="Flush the current file to disk every N processed records")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    papers_dir = Path(args.papers_dir).expanduser().resolve()
    venues = {v.strip() for v in args.venues.split(",")} if args.venues else None
    years = {y.strip() for y in args.years.split(",")} if args.years else None

    files = sorted(papers_dir.glob("*/*.json"))
    grand_seen = grand_filled = 0
    for jf in files:
        if venues and jf.parent.name not in venues:
            continue
        if years and jf.stem not in years:
            continue
        records = json.load(open(jf, encoding="utf-8"))
        if not isinstance(records, list):
            continue
        filled = considered = pending = 0
        for rec in records:
            if rec.get("arxiv_url"):
                continue
            title = (rec.get("title") or "").strip()
            if not title:
                continue
            author = first_author(rec.get("authors", ""))
            considered += 1
            pending += 1
            grand_seen += 1
            try:
                md = call_matcher(base, title, author)
            except Exception as e:
                print(f"  skip (api): {title[:60]} ({e})")
                continue
            title_sim, rerank, aid, surname = parse_result(md)
            if aid and decide(title_sim, rerank, surname, author,
                              args.title_accept, args.rerank_accept):
                rec["arxiv_url"] = f"https://arxiv.org/abs/{aid}"
                filled += 1
                grand_filled += 1
                if args.dry_run:
                    print(f"  + {aid}  ts={title_sim:.2f} rr={rerank:.2f}  {title[:60]}")
            # Flush periodically so progress persists mid-file (resumable).
            if not args.dry_run and args.save_every and pending >= args.save_every:
                atomic_write(jf, records)
                pending = 0
            if args.sleep:
                time.sleep(args.sleep)
            if args.limit and grand_seen >= args.limit:
                break
        if pending and not args.dry_run:
            atomic_write(jf, records)
        print(f"{jf.parent.name}/{jf.name}: filled {filled}/{considered}")
        if args.limit and grand_seen >= args.limit:
            break

    print(f"=== total: filled {grand_filled}/{grand_seen} ===")


if __name__ == "__main__":
    main()
