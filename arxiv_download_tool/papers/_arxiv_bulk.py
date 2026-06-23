#!/usr/bin/env python3
"""Bulk arXiv-link filler using OAI-PMH (arXiv's recommended bulk method).

Two phases:
  harvest  - stream the arXiv OAI-PMH feed (metadataPrefix=arXiv) and write a
             compact local index: one "<id>\\t<norm_title>\\t<surname>" line per
             paper.  Honors 503/Retry-After flow control, single connection.
  match    - load the index and, for every accepted paper missing an arXiv
             link, assign it by exact normalised-title match (disambiguated by
             first-author surname).  Writes each JSON file atomically.

No credentials required.  `python3 _arxiv_bulk.py all` runs harvest then match.
"""
import argparse
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_metadata_dir():
    for cand in (os.path.join(HERE, "arxiv_metadata"),
                 os.path.join(HERE, "..", "arxiv_metadata"),
                 os.path.join(HERE, "..", "..", "arxiv_metadata")):
        cand = os.path.normpath(cand)
        if os.path.isdir(cand):
            return cand
    return os.path.normpath(os.path.join(HERE, "..", "arxiv_metadata"))


METADATA_DIR = _find_metadata_dir()
INDEX_PATH = os.path.join(METADATA_DIR, "arxiv_title_index.tsv")
STATE_PATH = os.path.join(HERE, "_harvest_state.json")
LOG_PATH = os.path.join(HERE, "_arxiv_bulk.log")

OAI_BASE = "http://export.arxiv.org/oai2"
UA = ("recsys-meta-harvest/1.0 (paper metadata enrichment; "
      "contact: https://github.com/YuFan-Microsoft/RecSysSummer)")
OAI = "{http://www.openarchives.org/OAI/2.0/}"
AX = "{http://arxiv.org/OAI/arXiv/}"

# ---- self-contained normalisation / IO helpers (no external import) ----
_GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
    "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
    "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi", "ο": "omicron",
    "π": "pi", "ρ": "rho", "σ": "sigma", "ς": "sigma", "τ": "tau",
    "υ": "upsilon", "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
    "Δ": "delta", "Σ": "sigma", "Ω": "omega", "Γ": "gamma", "Φ": "phi",
    "Ψ": "psi", "Θ": "theta", "Λ": "lambda", "Π": "pi", "Ξ": "xi",
}


def _translit(s):
    for g, latin in _GREEK.items():
        if g in s:
            s = s.replace(g, latin)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _strip_latex(s):
    for _ in range(3):
        s = re.sub(r"\\[a-zA-Z]+\s*\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+", lambda m: m.group(0)[1:], s)
    return s


def norm(title):
    t = _translit(title)
    t = _strip_latex(t)
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())


def first_author_surname(authors):
    if not authors:
        return ""
    first = _translit(authors.split(",")[0].strip())
    parts = [p for p in re.split(r"\s+", first) if p]
    return parts[-1].lower() if parts else ""


def atomic_write(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=4, ensure_ascii=False)
    os.replace(tmp, path)


def log(msg):
    line = time.strftime("%H:%M:%S") + " " + msg
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


# --------------------------------------------------------------------------
# harvest
# --------------------------------------------------------------------------
def _retry_after_seconds(hdrs):
    if not hdrs:
        return None
    ra = hdrs.get("Retry-After")
    if not ra:
        return None
    ra = ra.strip()
    if ra.isdigit():
        return int(ra)
    try:
        import datetime
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(ra)
        if dt is not None:
            now = datetime.datetime.now(dt.tzinfo)
            return max(0, int((dt - now).total_seconds()))
    except Exception:  # noqa: BLE001
        return None
    return None


def oai_get(url, tries=8):
    """Fetch one OAI page, honoring 503/Retry-After. Returns body bytes."""
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (503, 429):
                wait = _retry_after_seconds(e.headers) or (10 * (attempt + 1))
                wait = max(5, min(wait, 300))
                log("  OAI %d flow-control -> wait %ds" % (e.code, wait))
                time.sleep(wait)
                continue
            raise
        except Exception as e:  # noqa: BLE001 - transient network, retry
            log("  OAI net error (%s) -> retry in %ds"
                % (type(e).__name__, 5 * (attempt + 1)))
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("OAI page failed after retries: " + url)


def parse_page(body):
    """Yield (id, title, surname); return resumptionToken (str or '' or None)."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        log("  XML parse error: %s" % e)
        return [], None
    # OAI-level error (e.g., badResumptionToken / noRecordsMatch)
    err = root.find(OAI + "error")
    if err is not None:
        return [], ("ERR:" + (err.get("code") or "unknown"))
    rows = []
    lr = root.find(OAI + "ListRecords")
    if lr is None:
        return [], None
    for rec in lr.findall(OAI + "record"):
        md = rec.find(OAI + "metadata")
        if md is None:
            continue
        ax = md.find(AX + "arXiv")
        if ax is None:
            continue
        aid = (ax.findtext(AX + "id") or "").strip()
        title = " ".join((ax.findtext(AX + "title") or "").split())
        author = ""
        authors = ax.find(AX + "authors")
        if authors is not None:
            a0 = authors.find(AX + "author")
            if a0 is not None:
                kn = " ".join((a0.findtext(AX + "keyname") or "").split())
                fn = " ".join((a0.findtext(AX + "forenames") or "").split())
                author = (fn + " " + kn).strip()
        if aid:
            rows.append((aid, title, author))
    tok_el = lr.find(OAI + "resumptionToken")
    token = tok_el.text if tok_el is not None else None
    return rows, (token or "")


def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            pass
    return {}


def harvest(from_date, until_date, polite=1.0, restart=False):
    os.makedirs(METADATA_DIR, exist_ok=True)
    state = {} if restart else load_state()
    if restart and os.path.exists(INDEX_PATH):
        os.remove(INDEX_PATH)

    # dedup: remember every arxiv id already in the index so we never write it
    # twice (e.g. when resuming over an overlapping date window).
    seen = set()
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as fh:
            for line in fh:
                i = line.find("\t")
                if i > 0:
                    seen.add(line[:i])
        log("dedup: %d ids already in index" % len(seen))

    token = state.get("token")
    pages = state.get("pages", 0)
    records = len(seen)
    written = 0

    if token:
        log("### harvest resume: page %d, %d ids in index ###" % (pages, records))
        url = OAI_BASE + "?verb=ListRecords&resumptionToken=" + \
            urllib.parse.quote(token)
    else:
        log("### harvest start: from=%s until=%s ###" % (from_date, until_date))
        params = {"verb": "ListRecords", "metadataPrefix": "arXiv"}
        if from_date:
            params["from"] = from_date
        if until_date:
            params["until"] = until_date
        url = OAI_BASE + "?" + urllib.parse.urlencode(params)

    idx = open(INDEX_PATH, "a", encoding="utf-8")
    try:
        while True:
            body = oai_get(url)
            rows, token = parse_page(body)
            if isinstance(token, str) and token.startswith("ERR:"):
                code = token[4:]
                # never truncate on an expired token; just stop so we can
                # safely resume later (dedup makes re-running harmless).
                log("  OAI stopped: %s (re-run to continue; dups skipped)" % code)
                break
            new_here = 0
            for aid, title, author in rows:
                if aid in seen:
                    continue
                seen.add(aid)
                idx.write("%s\t%s\t%s\n" % (aid, title, author))
                new_here += 1
            written += new_here
            records += new_here
            pages += 1
            idx.flush()
            atomic_write(STATE_PATH, {"token": token, "pages": pages,
                                      "records": records, "written": written,
                                      "from": from_date})
            if pages % 10 == 0 or not token:
                log("  page %d  (+%d new, %d total ids)"
                    % (pages, new_here, records))
            if not token:
                log("### harvest complete: %d pages, +%d new (index now %d) ###"
                    % (pages, written, records))
                break
            url = OAI_BASE + "?verb=ListRecords&resumptionToken=" + \
                urllib.parse.quote(token)
            time.sleep(polite)
    finally:
        idx.close()
    return records


# --------------------------------------------------------------------------
# match
# --------------------------------------------------------------------------
def load_index():
    by_title = {}
    if not os.path.exists(INDEX_PATH):
        log("no index file; run harvest first")
        return by_title
    with open(INDEX_PATH, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            aid = parts[0]
            nt = norm(parts[1])
            author = parts[2] if len(parts) > 2 else ""
            if not nt:
                continue
            by_title.setdefault(nt, []).append((aid, first_author_surname(author)))
    log("index loaded: %d distinct titles" % len(by_title))
    return by_title


def _arxiv_sort_key(aid):
    # prefer new-style YYMM.NNNNN ids, earliest first
    m = re.match(r"(\d{4})\.(\d{4,5})", aid)
    return (0, aid) if m else (1, aid)


def choose(cands, surname):
    if len(cands) == 1:
        return cands[0][0]
    if surname:
        hit = [c for c in cands if c[1] and c[1] == surname]
        if len(hit) == 1:
            return hit[0][0]
        if hit:
            cands = hit
    ids = sorted({c[0] for c in cands}, key=_arxiv_sort_key)
    if len(ids) == 1:
        return ids[0]
    return None  # genuinely ambiguous duplicate title -> skip (stay safe)


def match_files(files):
    by_title = load_index()
    if not by_title:
        return
    grand = 0
    for path in files:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        papers = data[next(iter(data))]
        found = 0
        for p in papers.values():
            if p.get("arxiv_url") or p.get("arxiv_id"):
                continue
            nt = norm(p.get("title") or "")
            cands = by_title.get(nt)
            if not cands:
                continue
            aid = choose(cands, first_author_surname(p.get("authors", "")))
            if aid:
                p["arxiv_id"] = aid
                p["arxiv_url"] = "https://arxiv.org/abs/" + aid
                found += 1
        atomic_write(path, data)
        grand += found
        log("  %-16s +%d links" % (os.path.basename(path), found))
    log("### match done: %d new links ###" % grand)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["harvest", "match", "all"])
    ap.add_argument("--from", dest="from_date", default="2017-01-01")
    ap.add_argument("--until", dest="until_date",
                    default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--restart", action="store_true",
                    help="ignore saved state and re-harvest from scratch")
    ap.add_argument("--polite", type=float, default=1.0,
                    help="seconds between OAI pages")
    ap.add_argument("--files", nargs="*")
    args = ap.parse_args()

    if args.files:
        files = [os.path.join(HERE, f) for f in args.files]
    else:
        files = sorted(os.path.join(HERE, f) for f in os.listdir(HERE)
                       if f.endswith(".json") and not f.startswith("_"))

    if args.phase in ("harvest", "all"):
        harvest(args.from_date, args.until_date, args.polite, args.restart)
    if args.phase in ("match", "all"):
        match_files(files)


if __name__ == "__main__":
    main()
