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
import glob
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
# The index may live as one monolithic arxiv_title_index.tsv or as year-split
# shards (arxiv_title_index_2015-2021.tsv, ...) kept under GitHub's per-file size
# limit. Reads merge every shard; appends go to the newest (last) shard.
INDEX_GLOB = os.path.join(METADATA_DIR, "arxiv_title_index*.tsv")


def index_shards():
    """Sorted list of all index files (monolithic and/or year shards)."""
    return sorted(glob.glob(INDEX_GLOB))


def append_path():
    """File harvest appends new records to: the newest shard, else the
    monolithic path (created on demand)."""
    shards = index_shards()
    return shards[-1] if shards else INDEX_PATH


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
    if restart:
        for shard in index_shards():
            os.remove(shard)

    # dedup: remember every arxiv id already in the index so we never write it
    # twice (e.g. when resuming over an overlapping date window).
    seen = set()
    for shard in index_shards():
        with open(shard, encoding="utf-8") as fh:
            for line in fh:
                i = line.find("\t")
                if i > 0:
                    seen.add(line[:i])
    if seen:
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

    idx = open(append_path(), "a", encoding="utf-8")
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
    shards = index_shards()
    if not shards:
        log("no index file; run harvest first")
        return by_title
    for shard in shards:
        with open(shard, encoding="utf-8") as fh:
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


def extract_arxiv_id(s):
    s = (s or "").strip()
    s = s.rsplit("/abs/", 1)[-1]
    m = re.search(r"(\d{4}\.\d{4,5}|[a-z\-]+(?:\.[A-Z]{2})?/\d{7})", s)
    return m.group(1) if m else None


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


def _ascii_lower(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    return s.lower()


def same_first_author(a, b):
    """True if two first-author names plausibly refer to the same person:
    surname identical AND forename equal or matching initial."""
    ta = [t for t in re.split(r"[^a-z]+", _ascii_lower(a)) if t]
    tb = [t for t in re.split(r"[^a-z]+", _ascii_lower(b)) if t]
    if not ta or not tb or ta[-1] != tb[-1]:
        return False
    return ta[0] == tb[0] or ta[0][:1] == tb[0][:1]


def fuzzy_fill(files, threshold=0.93):
    """Second pass: for papers still missing a link, accept a candidate only
    when the first author matches (surname + forename/initial) AND the title is
    >= `threshold` similar. Blocks by surname, prunes by word-set overlap."""
    from difflib import SequenceMatcher

    # collect still-missing papers and the surnames we need
    missing = []  # (file_idx, paper_ref, title, first_author)
    datas = []
    used_ids = set()
    for fi, path in enumerate(files):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        datas.append((path, data))
        for p in data[next(iter(data))].values():
            if p.get("arxiv_url") or p.get("arxiv_id"):
                aid = extract_arxiv_id(p.get("arxiv_id") or p.get("arxiv_url"))
                if aid:
                    used_ids.add(aid)
                continue
            authors = p.get("authors", "") or ""
            missing.append((fi, p, p.get("title") or "",
                            authors.split(",")[0].strip()))
    need = {first_author_surname(fa) for _, _, _, fa in missing}
    need.discard("")

    # index restricted to needed surnames: surname -> [(wordset, ntitle, id, author)]
    by_sur = {}
    for shard in index_shards():
        with open(shard, encoding="utf-8") as fh:
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 3:
                    continue
                sur = first_author_surname(parts[2])
                if sur not in need:
                    continue
                nt = norm(parts[1])
                if not nt:
                    continue
                by_sur.setdefault(sur, []).append(
                    (frozenset(nt.split()), nt, parts[0], parts[2]))
    log("fuzzy: %d still-missing, index blocks for %d surnames"
        % (len(missing), len(by_sur)))

    filled = 0
    per_file = {}
    for fi, p, title, fa in missing:
        nt = norm(title)
        tws = set(nt.split())
        if not tws:
            continue
        sur = first_author_surname(fa)
        best_r, best_id = 0.0, None
        for ws, cnt, aid, iauth in by_sur.get(sur, []):
            inter = len(tws & ws)
            if not inter or inter / len(tws | ws) < 0.6:
                continue
            r = SequenceMatcher(None, cnt, nt).ratio()
            if r > best_r and r >= threshold and same_first_author(fa, iauth):
                best_r, best_id = r, aid
        if best_id and best_id not in used_ids:
            p["arxiv_id"] = best_id
            p["arxiv_url"] = "https://arxiv.org/abs/" + best_id
            used_ids.add(best_id)
            filled += 1
            per_file[fi] = per_file.get(fi, 0) + 1

    for fi, (path, data) in enumerate(datas):
        if per_file.get(fi):
            atomic_write(path, data)
            log("  %-16s +%d (fuzzy)"
                % (os.path.relpath(path, HERE), per_file[fi]))
    log("### fuzzy done: +%d new links (threshold %.2f) ###"
        % (filled, threshold))
    return filled


def match_files(files):
    by_title = load_index()
    if not by_title:
        return
    tot_papers = tot_missing0 = tot_filled = 0
    log("--- per-file: total | was-missing | +filled | still-missing | rate ---")
    for path in files:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        papers = data[next(iter(data))]
        total = len(papers)
        missing0 = filled = 0
        for p in papers.values():
            if p.get("arxiv_url") or p.get("arxiv_id"):
                continue
            missing0 += 1
            cands = by_title.get(norm(p.get("title") or ""))
            if not cands:
                continue
            aid = choose(cands, first_author_surname(p.get("authors", "")))
            if aid:
                p["arxiv_id"] = aid
                p["arxiv_url"] = "https://arxiv.org/abs/" + aid
                filled += 1
        atomic_write(path, data)
        still = missing0 - filled
        rate = (100.0 * filled / missing0) if missing0 else 0.0
        rel = os.path.relpath(path, HERE)
        tot_papers += total
        tot_missing0 += missing0
        tot_filled += filled
        log("  %-16s %5d | %5d | +%5d | %5d | %5.1f%%"
            % (rel, total, missing0, filled, still, rate))
    tot_still = tot_missing0 - tot_filled
    tot_rate = (100.0 * tot_filled / tot_missing0) if tot_missing0 else 0.0
    log("### match done ###")
    log("  papers=%d  was-missing=%d  filled=%d  still-missing=%d  match-rate=%.1f%%"
        % (tot_papers, tot_missing0, tot_filled, tot_still, tot_rate))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["harvest", "match", "fuzzy", "all"])
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
        import glob as _glob
        files = sorted(_glob.glob(os.path.join(HERE, "*", "*.json")))

    if args.phase in ("harvest", "all"):
        harvest(args.from_date, args.until_date, args.polite, args.restart)
    if args.phase in ("match", "all"):
        match_files(files)
    if args.phase in ("fuzzy", "all"):
        fuzzy_fill(files)


if __name__ == "__main__":
    main()
