#!/usr/bin/env python3
"""Fetch Semantic Scholar metadata for every arXiv id in the title-index shards.

Walks the arXiv ids newest -> oldest (today backwards), sends them to the
Semantic Scholar ``POST /graph/v1/paper/batch`` endpoint 500 at a time, and
appends one JSON object per paper to a sharded JSONL tree laid out as
``<out_dir>/<year>/<Subject>/metadata.jsonl`` (year from the arXiv id, subject
from the paper's primary S2 fieldsOfStudy; not-found papers go to ``Unknown``).

- No API key required, but if the ``S2_API_KEY`` environment variable is set it
  is sent in the ``x-api-key`` header (higher, more reliable rate limit).
- Resumable: arXiv ids already present in any shard are skipped, so you can stop
  (Ctrl-C) and rerun any time.
- Honors 429/503 flow control with exponential backoff + Retry-After.

Usage::

    # trial: just the 3 newest batches (~1500 papers)
    python3 fetch_s2_metadata.py --limit 3

    # full run, newest -> oldest, resumable
    python3 fetch_s2_metadata.py

    # with a key
    S2_API_KEY=xxxxx python3 fetch_s2_metadata.py
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX_GLOB = os.path.join(HERE, "arxiv_index", "arxiv_title_index*.tsv")
# Records are sharded as <out_dir>/<year>/<Subject>/metadata.jsonl
OUT_DIR_DEFAULT = os.path.join(HERE, "arxiv_full_metadata")
SHARD_GLOB = os.path.join("*", "*", "metadata.jsonl")

S2_BATCH_URL = "https://api.semanticscholar.org/graph/v1/paper/batch"
# Only the fields we keep. List-heavy fields (citations/references/embedding)
# are excluded so a 500-id batch stays well under the 10 MB cap.
FIELDS = ",".join([
    "corpusId", "title", "authors", "year", "publicationDate",
    "citationCount", "influentialCitationCount", "fieldsOfStudy", "abstract",
])
UA = "recsys-s2-meta/1.0 (citation enrichment)"


def flatten(rec, aid, now):
    """Project an S2 paper object to our flat, scalar-only record."""
    authors = "; ".join(a.get("name", "") for a in (rec.get("authors") or []))
    fos = "; ".join(rec.get("fieldsOfStudy") or [])
    return {
        "arxiv_id": aid,
        "corpusId": rec.get("corpusId"),
        "title": rec.get("title"),
        "authors": authors,
        "year": rec.get("year"),
        "publicationDate": rec.get("publicationDate"),
        "citationCount": rec.get("citationCount"),
        "influentialCitationCount": rec.get("influentialCitationCount"),
        "fieldsOfStudy": fos,
        "abstract": rec.get("abstract"),
        "fetched_at": now,
    }


def _read_key_file():
    """Read the S2 API key from a local, git-ignored .s2_api_key file."""
    p = os.path.join(HERE, ".s2_api_key")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return fh.read().strip() or None
    return None


def chrono_key(aid: str):
    """Sort key giving (year, month, seq); newest sorts largest."""
    m = re.match(r"^(\d{2})(\d{2})\.(\d+)$", aid)
    if m:
        return (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"^[A-Za-z\-]+(?:\.[A-Z]{2})?/(\d{2})(\d{2})(\d+)$", aid)
    if m:
        yy = int(m.group(1))
        return (1900 + yy if yy >= 91 else 2000 + yy, int(m.group(2)), int(m.group(3)))
    return (0, 0, 0)


def year_of(aid: str) -> str:
    """Calendar-year folder name derived from the arXiv id (e.g. '2025')."""
    m = re.match(r"^(\d{2})(\d{2})\.", aid)
    if m:
        return str(2000 + int(m.group(1)))
    m = re.match(r"^[A-Za-z\-]+(?:\.[A-Z]{2})?/(\d{2})(\d{2})\d+", aid)
    if m:
        yy = int(m.group(1))
        return str(1900 + yy if yy >= 91 else 2000 + yy)
    return "unknown_year"


def subject_of(rec: dict) -> str:
    """Primary discipline folder name from S2 fieldsOfStudy (first listed).

    Spaces/punctuation are collapsed to underscores so the value is a safe
    folder name (e.g. 'Computer Science' -> 'Computer_Science'). Records with
    no field of study (incl. not-found papers) bucket into 'Unknown'.
    """
    fos = rec.get("fieldsOfStudy")
    if not fos:
        return "Unknown"
    first = fos.split(";")[0].strip()
    if not first:
        return "Unknown"
    return re.sub(r"[^A-Za-z0-9]+", "_", first).strip("_") or "Unknown"


def shard_writer(handles: dict, out_dir: str, year: str, subject: str):
    """Return a cached append handle for <out_dir>/<year>/<subject>/metadata.jsonl."""
    key = (year, subject)
    fh = handles.get(key)
    if fh is None:
        d = os.path.join(out_dir, year, subject)
        os.makedirs(d, exist_ok=True)
        fh = open(os.path.join(d, "metadata.jsonl"), "a", encoding="utf-8")
        handles[key] = fh
    return fh


def load_all_ids() -> list[str]:
    """Every arXiv id across the shards, newest -> oldest."""
    ids = []
    for shard in sorted(glob.glob(INDEX_GLOB)):
        with open(shard, encoding="utf-8") as fh:
            for line in fh:
                i = line.find("\t")
                if i > 0:
                    ids.append(line[:i])
    ids.sort(key=chrono_key, reverse=True)
    return ids


def load_done(out_dir: str) -> set[str]:
    """arXiv ids already attempted (present in any year/subject shard)."""
    done = set()
    for path in glob.glob(os.path.join(out_dir, SHARD_GLOB)):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                aid = rec.get("arxiv_id")
                if aid:
                    done.add(aid)
    return done


def _retry_after(headers) -> float | None:
    if not headers:
        return None
    ra = headers.get("Retry-After")
    if ra and ra.strip().isdigit():
        return float(ra.strip())
    return None


def fetch_batch(ids: list[str], api_key: str | None, tries: int = 6):
    """POST one batch; return the aligned list (entries may be None) or None
    if the batch failed after retries."""
    url = S2_BATCH_URL + "?" + urllib.parse.urlencode({"fields": FIELDS})
    body = json.dumps({"ids": ["ARXIV:" + i for i in ids]}).encode()
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if api_key:
        headers["x-api-key"] = api_key
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                wait = _retry_after(e.headers) or min(60, 2 ** attempt * 2)
                print(f"  {e.code} flow-control -> wait {wait:.0f}s", flush=True)
                time.sleep(wait)
                continue
            if e.code == 400:
                print(f"  400 bad request (skipping batch): {e.read()[:200]!r}", flush=True)
                return None
            print(f"  HTTP {e.code} -> retry in {2 ** attempt}s", flush=True)
            time.sleep(2 ** attempt)
        except Exception as e:  # noqa: BLE001 transient network
            print(f"  net error ({type(e).__name__}) -> retry in {2 ** attempt}s", flush=True)
            time.sleep(2 ** attempt)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=OUT_DIR_DEFAULT,
                    help="root dir for <year>/<Subject>/metadata.jsonl shards")
    ap.add_argument("--batch-size", type=int, default=500, help="ids per request (max 500)")
    ap.add_argument("--limit", type=int, default=0, help="max batches this run (0 = all)")
    ap.add_argument("--sleep", type=float, default=1.1, help="seconds between batches")
    args = ap.parse_args()

    api_key = os.environ.get("S2_API_KEY") or _read_key_file()
    batch_size = max(1, min(500, args.batch_size))
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    print(f"[s2] key: {'yes' if api_key else 'no (unauthenticated, slower)'}")
    print("[s2] loading arXiv ids from shards ...", flush=True)
    all_ids = load_all_ids()
    done = load_done(out_dir)
    todo = [i for i in all_ids if i not in done]
    print(f"[s2] total={len(all_ids)}  done={len(done)}  todo={len(todo)}", flush=True)
    if not todo:
        print("[s2] nothing to do.")
        return

    handles: dict = {}
    fetched = found = 0
    batches = 0
    try:
        for start in range(0, len(todo), batch_size):
            if args.limit and batches >= args.limit:
                print(f"[s2] reached --limit {args.limit}, stopping.")
                break
            batch = todo[start:start + batch_size]
            results = fetch_batch(batch, api_key)
            batches += 1
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if results is None:
                print(f"[s2] batch {batches} FAILED ({batch[0]}..{batch[-1]}), will retry next run", flush=True)
                time.sleep(args.sleep)
                continue
            b_found = 0
            touched = set()
            for aid, rec in zip(batch, results):
                if rec is None:
                    record = {"arxiv_id": aid, "found": False, "fetched_at": now}
                    subject = "Unknown"
                else:
                    record = flatten(rec, aid, now)
                    subject = subject_of(record)
                    b_found += 1
                fh = shard_writer(handles, out_dir, year_of(aid), subject)
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                touched.add(fh)
            for fh in touched:
                fh.flush()
            fetched += len(batch)
            found += b_found
            print(f"[s2] batch {batches}: {batch[0]} .. {batch[-1]}  "
                  f"found {b_found}/{len(batch)}  (cum found {found}/{fetched})", flush=True)
            time.sleep(args.sleep)
    except KeyboardInterrupt:
        print("\n[s2] interrupted; progress saved (resume by rerunning).")
    finally:
        for fh in handles.values():
            fh.close()
    print(f"[s2] done this run: {batches} batches, {found}/{fetched} found -> {out_dir}")


if __name__ == "__main__":
    main()
