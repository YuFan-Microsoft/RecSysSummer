"""Authoritative ACM-venue accepted-paper lists from DBLP.

RecSys / KDD / SIGIR / WSDM / CIKM / WWW are ACM conferences: they do not use
OpenReview and are not in the ACL Anthology. Their authoritative accepted-paper
record is DBLP, whose publication API returns a full proceedings table of
contents via the `toc:<bht-key>:` facet. This pulls the raw paper list
(title / authors / venue / pages / doi / links) per venue and year.

DBLP carries no abstract, so abstracts are not included here.

Usage:
    python3 fetch_dblp.py --venues RecSys,KDD,SIGIR,WSDM,CIKM,WWW --years 2023,2024,2025
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# DBLP conf slug per venue. The proceedings table of contents lives at
# db/conf/<slug>/<slug><year>.bht and is queryable via the `toc:` facet.
DBLP_SLUG = {
    "RecSys": "recsys",
    "KDD": "kdd",
    "SIGIR": "sigir",
    "WSDM": "wsdm",
    "CIKM": "cikm",
    "WWW": "www",
}

DBLP_API = "https://dblp.org/search/publ/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (recsys-meta-harvest; DBLP TOC enrichment)"}
# Drop trailing 4-digit homonym disambiguation, e.g. "Wei Wang 0001" -> "Wei Wang".
_HOMONYM = re.compile(r"\s+\d{4}$")


def clean_author(name: str) -> str:
    """Strip DBLP's trailing homonym number from an author name."""
    return _HOMONYM.sub("", name or "").strip()


def _get_json(url: str, tries: int = 8) -> dict:
    """Fetch a DBLP API page, honoring 429/503 rate limiting with backoff."""
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                ra = (e.headers or {}).get("Retry-After")
                wait = int(ra) if ra and str(ra).isdigit() else 30 * (attempt + 1)
                wait = max(15, min(wait, 300))
                print(f"  DBLP {e.code} rate-limited -> wait {wait}s")
                time.sleep(wait)
                continue
            raise
        except Exception as e:  # transient network (reset/timeout) -> retry
            wait = 10 * (attempt + 1)
            print(f"  DBLP net error ({type(e).__name__}) -> retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError("DBLP page failed after retries: " + url)


def fetch_toc(bht_key: str, polite: float = 5.0) -> list:
    """Page through every entry in a DBLP proceedings table of contents."""
    hits, offset = [], 0
    while True:
        params = {
            "q": f"toc:{bht_key}:",
            "h": 1000,
            "f": offset,
            "format": "json",
        }
        url = f"{DBLP_API}?{urllib.parse.urlencode(params)}"
        result = _get_json(url)["result"]
        batch = result.get("hits", {}).get("hit", [])
        if isinstance(batch, dict):  # DBLP returns a bare object for a single hit
            batch = [batch]
        hits += batch
        total = int(result.get("hits", {}).get("@total", 0))
        offset += len(batch)
        if not batch or offset >= total:
            break
        time.sleep(polite)  # be polite between pages
    return hits


def main():
    parser = argparse.ArgumentParser(description="DBLP accepted lists + arXiv links.")
    parser.add_argument("--venues", default=",".join(DBLP_SLUG),
                        help="Comma-separated subset of: " + ", ".join(DBLP_SLUG))
    parser.add_argument("--years", default="2023,2024,2025", help="Comma-separated years.")
    parser.add_argument("--outdir", type=Path, default=Path("papers"))
    parser.add_argument("--polite", type=float, default=5.0,
                        help="seconds to wait between DBLP requests")
    args = parser.parse_args()

    venues = [v.strip() for v in args.venues.split(",") if v.strip()]
    years = [int(y) for y in args.years.split(",")]
    args.outdir.mkdir(parents=True, exist_ok=True)

    first = True
    for venue in venues:
        slug = DBLP_SLUG.get(venue)
        if not slug:
            print(f"{venue}: unknown venue, skipped")
            continue
        for year in years:
            if not first:
                time.sleep(args.polite)  # pace requests across venues/years
            first = False
            # Some venues split a year across multiple proceedings volumes
            # (e.g. KDD 2025 -> kdd2025-1.bht research + kdd2025-2.bht applied).
            # Try the plain key first; if empty, fall back to numbered volumes.
            try:
                hits = fetch_toc(f"db/conf/{slug}/{slug}{year}.bht", polite=args.polite)
            except Exception as exc:
                print(f"{venue} {year}: error ({type(exc).__name__}: {exc})")
                hits = []
            if not hits:
                for v in (1, 2, 3):
                    time.sleep(args.polite)
                    try:
                        part = fetch_toc(f"db/conf/{slug}/{slug}{year}-{v}.bht",
                                         polite=args.polite)
                    except Exception as exc:
                        print(f"{venue} {year} [-{v}]: error "
                              f"({type(exc).__name__}: {exc})")
                        part = []
                    if not part:
                        break  # no more volumes
                    hits += part

            records = {}
            for hit in hits:
                info = hit.get("info", {})
                if info.get("type") == "Editorship":  # skip front matter / proceedings
                    continue
                title = (info.get("title") or "").strip()
                if not title:
                    continue
                authors_field = info.get("authors", {}).get("author", [])
                if isinstance(authors_field, dict):
                    authors_field = [authors_field]
                authors = ", ".join(clean_author(a.get("text", "")) for a in authors_field)

                key = info.get("key") or info.get("url") or title
                records[key] = {
                    "title": title,
                    "authors": authors,
                    "venue": f"{venue} {year}",
                    "venue_short": f"{venue}{year}",
                    "pages": info.get("pages"),
                    "dblp_url": info.get("url"),
                    "doi": info.get("doi"),
                    "ee": info.get("ee"),
                }

            if not records:
                print(f"{venue} {year}: no papers found (TOC may not exist yet)")
                continue
            venue_dir = args.outdir / venue
            venue_dir.mkdir(parents=True, exist_ok=True)
            out = venue_dir / f"{year}.json"
            with open(out, "w", encoding="utf-8") as f:
                json.dump({f"{venue}{year}": records}, f, indent=4, ensure_ascii=False)
            print(f"{venue} {year}: {len(records)} papers -> {out}")


if __name__ == "__main__":
    main()
