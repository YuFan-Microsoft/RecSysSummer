#!/usr/bin/env python3
"""Stage 3 — transpose local S2 shards to the HF layout and upload changed ones.

Local  layout (fetch_s2_metadata.py output):  arxiv_full_metadata/<year>/<Subject>/metadata.jsonl
HF     layout (yufan/arxiv-metadata-2020-2026): <Subject>/<year>/metadata.jsonl

- Uploads only shards modified after --newer's mtime (default: everything, so
  pass --newer to stay incremental). Large jsonl go via LFS per .gitattributes.
- Regenerates the README field x year count table + headline total from the
  authoritative local line counts, and bumps the "→ YYYY-MM" span end.

Token: first valid of $HF_TOKEN, .hf_token, ~/.cache/huggingface/token (whoami).
Usage:
  python3 upload_metadata_hf.py --newer /tmp/s2_marker        # incremental
  python3 upload_metadata_hf.py --dry-run --newer /tmp/s2_marker
"""
import argparse, glob, json, os, re
from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_ROOT = os.path.join(HERE, "arxiv_full_metadata")   # <year>/<Subject>/metadata.jsonl
REPO_ID = "yufan/arxiv-metadata-2020-2026"


def resolve_token():
    cands = []
    for e in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        if os.environ.get(e):
            cands.append((e, os.environ[e].strip()))
    for p in (os.path.join(HERE, ".hf_token"), os.path.expanduser("~/.cache/huggingface/token")):
        if os.path.exists(p):
            t = open(p).read().strip()
            if t:
                cands.append((p, t))
    for src, t in cands:
        try:
            who = HfApi(token=t).whoami(); print(f"token from {src} -> {who.get('name')}"); return t
        except Exception:
            print(f"token from {src}: INVALID")
    raise SystemExit("No valid HF token (set $HF_TOKEN / update .hf_token / huggingface-cli login).")


def count_matrix():
    """matrix[field][year]=lines, plus the newest publicationDate month seen
    (computed accurately from 2025-2026 shards only)."""
    mat, end_month = {}, ""
    for f in glob.glob(os.path.join(LOCAL_ROOT, "*", "*", "metadata.jsonl")):
        parts = f.split(os.sep)
        year, subject = parts[-3], parts[-2]
        n = 0
        recent = year.isdigit() and int(year) >= 2025
        for line in open(f):
            if not line.strip():
                continue
            n += 1
            if recent:
                pd = (json.loads(line).get("publicationDate") or "")[:7]
                if pd:
                    end_month = max(end_month, pd)
        mat.setdefault(subject, {})[year] = n
    return mat, end_month


def render_table(mat):
    years = [str(y) for y in range(2020, 2027)]
    totals = {s: sum(mat[s].get(y, 0) for y in years) for s in mat}
    order = sorted(mat, key=lambda s: -totals[s])
    def cell(v): return f"{v:,}" if v else "–"
    lines = ["| Field (`config`) | " + " | ".join(years) + " | **Total** |",
             "|---|" + "---|" * (len(years) + 1)]
    for s in order:
        row = " | ".join(cell(mat[s].get(y, 0)) for y in years)
        lines.append(f"| `{s}` | {row} | **{totals[s]:,}** |")
    col = {y: sum(mat[s].get(y, 0) for s in mat) for y in years}
    grand = sum(totals.values())
    lines.append("| **all** | " + " | ".join(f"{col[y]:,}" for y in years) + f" | **{grand:,}** |")
    return "\n".join(lines), grand


def update_readme(token, grand, end_month, table, dry):
    p = hf_hub_download(REPO_ID, "README.md", repo_type="dataset", force_download=True)
    t = open(p).read()
    # replace the table block: header row '| Field (`config`) |' .. up to the 'all' row line
    t2 = re.sub(r"\| Field \(`config`\) \|.*?\| \*\*all\*\* \|.*?\n", table + "\n", t, count=1, flags=re.S)
    t2 = re.sub(r"\*\*[\d,]+ arXiv papers\*\*", f"**{grand:,} arXiv papers**", t2)
    m = re.search(r"2020-01 → (\d{4}-\d{2})", t2)
    cur_end = m.group(1) if m else ""
    if end_month and end_month > cur_end:
        t2 = re.sub(r"(2020-01 → )\d{4}-\d{2}", r"\g<1>" + end_month, t2)
    out = os.path.join(LOCAL_ROOT, "_README.md")
    open(out, "w").write(t2)
    print("README changed:", t != t2, "| grand total:", f"{grand:,}", "| end:", end_month)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--newer", default=None, help="only upload shards modified after this file's mtime")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    shards = glob.glob(os.path.join(LOCAL_ROOT, "*", "*", "metadata.jsonl"))
    if args.newer and not os.path.exists(args.newer):
        raise SystemExit(f"--newer marker missing: {args.newer}")
    if args.newer:
        cut = os.path.getmtime(args.newer)
        shards = [s for s in shards if os.path.getmtime(s) > cut]
    mat, end_month = count_matrix()
    # dataset scope is 2020-2026: OAI 'last-modified' harvest can touch revised
    # pre-2020 papers (creating out-of-scope shards) — never upload those.
    def in_scope(s):
        y = s.split(os.sep)[-3]
        return y.isdigit() and 2020 <= int(y) <= 2026
    dropped = [s for s in shards if not in_scope(s)]
    shards = [s for s in shards if in_scope(s)]
    if dropped:
        print(f"skipping {len(dropped)} out-of-scope (pre-2020) shards, e.g. {dropped[0]}")
    ops = []
    for s in sorted(shards):
        parts = s.split(os.sep)
        year, subject = parts[-3], parts[-2]
        pir = f"{subject}/{year}/metadata.jsonl"          # transpose
        ops.append(CommitOperationAdd(path_in_repo=pir, path_or_fileobj=s))
        rows = mat.get(subject, {}).get(year, 0)
        print(f"  upload {year}/{subject} -> {pir}  ({rows:,} rows)")
    print(f"changed shards to upload: {len(ops)}")

    table, grand = render_table(mat)
    token = resolve_token()
    readme = update_readme(token, grand, end_month, table, args.dry_run)
    ops.append(CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=readme))

    if args.dry_run:
        print("DRY RUN — not committing.")
        return
    info = HfApi(token=token).create_commit(
        repo_id=REPO_ID, repo_type="dataset", operations=ops,
        commit_message=f"Refresh: +new arXiv metadata, total {grand:,} (→ {end_month})")
    print("COMMIT OK:", getattr(info, "commit_url", info))


if __name__ == "__main__":
    main()
