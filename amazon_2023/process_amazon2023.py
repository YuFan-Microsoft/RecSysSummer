#!/usr/bin/env python3
"""
process_amazon2023.py
=====================
Data-processing pipeline for **Amazon Reviews 2023**, implementing the protocol
locked in `Amazon-2023_Data_Processing_Protocol.md`, with **item content
features** and **JSON (JSONL) output**.

    download (official 0-core rating_only)  ->  iterative 5-core filtering
      ->  per-user chronological ordering   ->  leave-one-out (last_out) split
      ->  sequential history at maxlen 20 AND 50
      ->  join item metadata (title, images, price, ...)
      ->  everything written as JSONL  +  statistics

All outputs are **JSON Lines** (one JSON object per line) — no CSV/TSV/Excel.

Core filtering / splitting logic is borrowed from the official benchmark scripts
(so our splits reproduce the official 5core/last_out exactly):
    https://github.com/hyp1231/AmazonReviews2023/tree/main/benchmark_scripts
        kcore_filtering.py  (make_inters_in_order, filter_inters)
        last_out_split.py   (leave-one-out test/valid/train)

Data sources (official HF dataset McAuley-Lab/Amazon-Reviews-2023):
    benchmark/0core/rating_only/<Category>.csv     # deduped raw interactions
    benchmark/5core/rating_only/<Category>.csv     # official 5-core (validation / --from-5core)
    raw/meta_categories/meta_<Category>.jsonl      # item metadata (content features)

Output layout (under processed/):
    interactions/<cat>.jsonl                       # 5-core interactions
    last_out/<cat>.{train,valid,test}.jsonl        # leave-one-out, direct
    seq_maxlen20/<cat>.{train,valid,test}.jsonl    # leave-one-out, sequential (history<=20)
    seq_maxlen50/<cat>.{train,valid,test}.jsonl    # leave-one-out, sequential (history<=50)
    item_meta/<cat>.jsonl                          # item content features (5-core items)
    stats.json, stats.md

Usage:
    python process_amazon2023.py                       # 5 categories, maxlen 20 & 50
    python process_amazon2023.py --no-meta             # skip item metadata
    python process_amazon2023.py --categories Video_Games
"""

import argparse
import collections
import json
import os
import subprocess
import sys
import time

try:
    from huggingface_hub import hf_hub_download
except Exception:  # pragma: no cover
    print("ERROR: huggingface_hub is required. pip install huggingface_hub", file=sys.stderr)
    raise

REPO_ID = "McAuley-Lab/Amazon-Reviews-2023"
REPO_TYPE = "dataset"
RESOLVE = f"https://huggingface.co/datasets/{REPO_ID}/resolve/main"

# "Beauty" -> Beauty_and_Personal_Care (All_Beauty is too small after 5-core).
DEFAULT_CATEGORIES = [
    "Video_Games",
    "Industrial_and_Scientific",
    "Beauty_and_Personal_Care",
    "Musical_Instruments",
    "Books",
]

# Item-metadata fields kept (the full Amazon-2023 meta schema minus rarely-used
# `videos` / `bought_together`). `images` retains thumb/large/hi_res URLs.
META_FIELDS = [
    "parent_asin", "title", "main_category", "store", "categories",
    "price", "average_rating", "rating_number", "features", "description",
    "images", "details",
]


# --------------------------------------------------------------------------- #
# Download helpers
# --------------------------------------------------------------------------- #

def robust_download(filename, dest, max_attempts=40):
    """Resumable, stall-resistant download via curl. Aborts a connection that
    stalls (<10 KB/s for 30 s) and reconnects with HTTP Range resume (`-C -`),
    which is far more reliable than a single long-lived connection for the very
    large metadata files (e.g. Books meta = 13.7 GB)."""
    url = f"{RESOLVE}/{filename}"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # expected size (Content-Length) to confirm completeness
    expected = None
    try:
        head = subprocess.run(["curl", "-sIL", url], capture_output=True, text=True, timeout=60)
        for ln in head.stdout.splitlines():
            if ln.lower().startswith("content-length:"):
                expected = int(ln.split(":")[1].strip())
    except Exception:
        pass
    for attempt in range(1, max_attempts + 1):
        have = os.path.getsize(dest) if os.path.exists(dest) else 0
        if expected and have >= expected:
            return dest
        if attempt > 1:
            print(f"      download retry {attempt} (have {have/1048576:.0f} MB"
                  f"{'/%d MB' % (expected/1048576) if expected else ''}) ...")
        rc = subprocess.run([
            "curl", "-L", "-C", "-", "--fail",
            "--retry", "10", "--retry-delay", "5", "--retry-all-errors",
            "--speed-limit", "10000", "--speed-time", "30",
            "-o", dest, url,
        ]).returncode
        if rc == 0 and (not expected or os.path.getsize(dest) >= expected):
            return dest
    raise RuntimeError(f"download failed after {max_attempts} attempts: {filename}")


def hf_csv(category, core, kind, cache_dir, split=None):
    name = category if split is None else f"{category}.{split}"
    filename = f"benchmark/{core}/{kind}/{name}.csv"
    return hf_hub_download(repo_id=REPO_ID, repo_type=REPO_TYPE,
                           filename=filename, local_dir=cache_dir)


def hf_meta(category, cache_dir):
    filename = f"raw/meta_categories/meta_{category}.jsonl"
    dest = os.path.join(cache_dir, filename)
    return robust_download(filename, dest)


def load_rating_only(path):
    """Yield (user, item, rating, timestamp) from a rating_only CSV (official input)."""
    inters = []
    with open(path, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if parts[0] == "user_id":  # header
                continue
            inters.append((parts[0], parts[1], float(parts[2]), int(parts[3])))
    return inters


# --------------------------------------------------------------------------- #
# Core logic — borrowed from the official benchmark scripts
# --------------------------------------------------------------------------- #

def make_inters_in_order(inters):
    """Group by user, sort by timestamp, keep earliest of each (user,item). (official)"""
    user2inters, new_inters = collections.defaultdict(list), []
    for inter in inters:
        user2inters[inter[0]].append(inter)
    for user in user2inters:
        seq = user2inters[user]
        seq.sort(key=lambda d: d[3])
        seen = set()
        for it in seq:
            if it[1] in seen:
                continue
            seen.add(it[1])
            new_inters.append(it)
    return new_inters


def _count(inters, idx):
    c = collections.defaultdict(int)
    for unit in inters:
        c[unit[idx]] += 1
    return c


def _candidates(unit2count, threshold):
    cans = set(u for u, n in unit2count.items() if n >= threshold)
    return cans, len(unit2count) - len(cans)


def filter_kcore(inters, k=5):
    """Iterative k-core filtering on users AND items to a fixed point. (official)"""
    user2count, item2count = _count(inters, 0), _count(inters, 1)
    idx = 0
    while True:
        users, n_fu = _candidates(user2count, k)
        items, n_fi = _candidates(item2count, k)
        if n_fu == 0 and n_fi == 0:
            break
        new_inters = []
        nu, ni = collections.defaultdict(int), collections.defaultdict(int)
        for unit in inters:
            if unit[0] in users and unit[1] in items:
                new_inters.append(unit)
                nu[unit[0]] += 1
                ni[unit[1]] += 1
        inters, user2count, item2count = new_inters, nu, ni
        idx += 1
        print(f"      kcore epoch {idx}: inters={len(inters):,} "
              f"users={len(user2count):,} items={len(item2count):,}")
    return inters


def group_ordered(inters):
    user2inters = collections.defaultdict(list)
    for inter in inters:
        user2inters[inter[0]].append(inter)
    for user in user2inters:
        user2inters[user].sort(key=lambda d: d[3])
        seen, ordered = set(), []
        for it in user2inters[user]:
            if it[1] in seen:
                continue
            seen.add(it[1])
            ordered.append(it)
        user2inters[user] = ordered
    return user2inters


# --------------------------------------------------------------------------- #
# JSONL writers
# --------------------------------------------------------------------------- #

def _inter_obj(rec):
    return {"user_id": rec[0], "parent_asin": rec[1],
            "rating": rec[2], "timestamp": rec[3]}


def write_interactions(inters5, out_dir, category):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{category}.jsonl"), "w") as f:
        for rec in inters5:
            f.write(json.dumps(_inter_obj(rec)) + "\n")


def write_last_out_direct(user2inters, out_dir, category):
    """Leave-one-out DIRECT split as JSONL. (official last_out semantics)"""
    os.makedirs(out_dir, exist_ok=True)
    n_tr = n_va = n_te = 0
    with open(os.path.join(out_dir, f"{category}.train.jsonl"), "w") as ftr, \
         open(os.path.join(out_dir, f"{category}.valid.jsonl"), "w") as fva, \
         open(os.path.join(out_dir, f"{category}.test.jsonl"), "w") as fte:
        for user, seq in user2inters.items():
            fte.write(json.dumps(_inter_obj(seq[-1])) + "\n"); n_te += 1
            if len(seq) > 1:
                fva.write(json.dumps(_inter_obj(seq[-2])) + "\n"); n_va += 1
            if len(seq) > 2:
                for i in range(len(seq) - 2):
                    ftr.write(json.dumps(_inter_obj(seq[i])) + "\n"); n_tr += 1
    return n_tr, n_va, n_te


def write_seq_w_his(user2inters, out_dir, category, maxlen, min_history=1):
    """Sequential leave-one-out as JSONL. Each row carries the user's prior history
    (list of item ids) truncated to the most recent <=maxlen items. Train uses the
    rolling next-item scheme (one row per target position with non-empty history)."""
    os.makedirs(out_dir, exist_ok=True)
    n_tr = n_va = n_te = 0

    def hist(seq, upto):
        items = [s[1] for s in seq[:upto]]
        if maxlen and len(items) > maxlen:
            items = items[-maxlen:]
        return items

    def row(rec, history):
        o = _inter_obj(rec)
        o["history"] = history
        return json.dumps(o)

    with open(os.path.join(out_dir, f"{category}.train.jsonl"), "w") as ftr, \
         open(os.path.join(out_dir, f"{category}.valid.jsonl"), "w") as fva, \
         open(os.path.join(out_dir, f"{category}.test.jsonl"), "w") as fte:
        for user, seq in user2inters.items():
            n = len(seq)
            fte.write(row(seq[-1], hist(seq, n - 1)) + "\n"); n_te += 1
            if n > 1:
                fva.write(row(seq[-2], hist(seq, n - 2)) + "\n"); n_va += 1
            for i in range(min_history, n - 2):
                ftr.write(row(seq[i], hist(seq, i)) + "\n"); n_tr += 1
    return n_tr, n_va, n_te


# --------------------------------------------------------------------------- #
# Item metadata (content features)
# --------------------------------------------------------------------------- #

def build_item_meta(category, item_set, cache_dir, out_dir):
    """Download raw item metadata and write content features (title, images,
    price, ...) for the 5-core items, as JSONL. Returns (n_items_with_meta)."""
    os.makedirs(out_dir, exist_ok=True)
    path = hf_meta(category, cache_dir)
    out_path = os.path.join(out_dir, f"{category}.jsonl")
    n_written, n_lines = 0, 0
    with open(path, "r") as fin, open(out_path, "w") as fout:
        for line in fin:
            n_lines += 1
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pa = rec.get("parent_asin")
            if pa is None or pa not in item_set:
                continue
            slim = {k: rec.get(k) for k in META_FIELDS}
            fout.write(json.dumps(slim, ensure_ascii=False) + "\n")
            n_written += 1
    return n_written, n_lines


# --------------------------------------------------------------------------- #
# Stats / validation
# --------------------------------------------------------------------------- #

def compute_stats(category, inters5, user2inters):
    items = set(i[1] for i in inters5)
    lens = sorted(len(s) for s in user2inters.values())
    n_user = len(user2inters)
    avg_len = sum(lens) / max(1, len(lens))
    density = len(inters5) / (n_user * len(items)) if n_user and items else 0.0
    return {
        "category": category,
        "n_users": n_user,
        "n_items": len(items),
        "n_interactions": len(inters5),
        "avg_seq_len": round(avg_len, 4),
        "median_seq_len": lens[len(lens) // 2] if lens else 0,
        "min_seq_len": lens[0] if lens else 0,
        "max_seq_len": lens[-1] if lens else 0,
        "sparsity": round(1 - density, 8),
    }


def validate_against_official(category, my_inters5, my_user2inters, cache_dir):
    result = {"category": category}
    try:
        off5 = load_rating_only(hf_csv(category, "5core", "rating_only", cache_dir))
        result["official_5core_interactions"] = len(off5)
        result["my_5core_interactions"] = len(my_inters5)
        result["interactions_match"] = (len(off5) == len(my_inters5))
        off_test = hf_csv(category, "5core", "last_out", cache_dir, split="test")
        with open(off_test) as f:
            n_off_test = sum(1 for ln in f if ln.strip() and not ln.startswith("user_id"))
        result["official_last_out_test_rows"] = n_off_test
        result["my_test_rows"] = len(my_user2inters)
        result["test_rows_match"] = (n_off_test == len(my_user2inters))
    except Exception as e:  # pragma: no cover
        result["error"] = f"{type(e).__name__}: {e}"
    return result


# --------------------------------------------------------------------------- #
# Per-category driver
# --------------------------------------------------------------------------- #

def process_category(category, out_root, cache_dir, maxlens, validate,
                     from_5core=False, with_meta=True):
    print(f"\n=== {category} ===")
    t0 = time.time()
    if from_5core:
        src = hf_csv(category, "5core", "rating_only", cache_dir)
        print(f"  downloaded 5core/rating_only (official pre-filtered; --from-5core)")
        inters5 = make_inters_in_order(load_rating_only(src))
        print(f"  5-core interactions (official): {len(inters5):,}")
    else:
        src = hf_csv(category, "0core", "rating_only", cache_dir)
        print(f"  downloaded 0core/rating_only -> {os.path.basename(src)}")
        raw = load_rating_only(src)
        print(f"  raw (deduped) interactions: {len(raw):,}")
        print("  applying iterative 5-core filtering ...")
        inters5 = filter_kcore(make_inters_in_order(raw), k=5)
        print(f"  after 5-core: {len(inters5):,} interactions")

    write_interactions(inters5, os.path.join(out_root, "interactions"), category)
    user2inters = group_ordered(inters5)

    n_tr, n_va, n_te = write_last_out_direct(
        user2inters, os.path.join(out_root, "last_out"), category)
    print(f"  last_out (direct): train={n_tr:,} valid={n_va:,} test={n_te:,}")

    seq_counts = {}
    for L in maxlens:
        s = write_seq_w_his(user2inters, os.path.join(out_root, f"seq_maxlen{L}"), category, L)
        seq_counts[L] = {"train": s[0], "valid": s[1], "test": s[2]}
        print(f"  seq maxlen={L}: train={s[0]:,} valid={s[1]:,} test={s[2]:,}")

    stats = compute_stats(category, inters5, user2inters)
    stats["source"] = "official 5core/rating_only" if from_5core else "0core -> our iterative 5-core"
    stats["last_out_direct"] = {"train": n_tr, "valid": n_va, "test": n_te}
    stats["seq_w_his"] = seq_counts

    if with_meta:
        item_set = set(i[1] for i in inters5)
        print(f"  joining item metadata ({len(item_set):,} items) ...")
        n_meta, n_lines = build_item_meta(category, item_set,
                                          cache_dir, os.path.join(out_root, "item_meta"))
        cov = n_meta / len(item_set) if item_set else 0.0
        stats["item_meta"] = {"items_with_meta": n_meta, "meta_lines_scanned": n_lines,
                              "coverage": round(cov, 4)}
        print(f"  item_meta: {n_meta:,}/{len(item_set):,} items covered "
              f"({cov*100:.1f}%)")

    if validate:
        v = validate_against_official(category, inters5, user2inters, cache_dir)
        stats["validation"] = v
        ok = v.get("interactions_match") and v.get("test_rows_match")
        print(f"  validation vs official 5core: interactions_match={v.get('interactions_match')} "
              f"test_rows_match={v.get('test_rows_match')} {'OK' if ok else 'CHECK!'}")

    stats["seconds"] = round(time.time() - t0, 1)
    print(f"  done in {stats['seconds']}s")
    return stats


# --------------------------------------------------------------------------- #
# Stats writer
# --------------------------------------------------------------------------- #

def write_stats(all_stats, out_root, maxlens):
    with open(os.path.join(out_root, "stats.json"), "w") as f:
        json.dump(all_stats, f, indent=2)
    L = " & ".join(map(str, maxlens))
    out = [
        "# Amazon Reviews 2023 — Processed Dataset Statistics",
        "",
        f"Protocol: official rating_only -> iterative **5-core** -> **leave-one-out** "
        f"split -> sequential history at maxlen **{L}** -> item metadata join. "
        f"All outputs are **JSONL**.",
        "",
        "| Category | #Users | #Items | #Interactions | Avg len | Median | Sparsity | Items w/ meta |",
        "|----------|-------:|-------:|--------------:|--------:|-------:|---------:|--------------:|",
    ]
    for s in all_stats:
        meta = s.get("item_meta", {})
        mcov = f"{meta.get('items_with_meta','—'):,} ({meta.get('coverage',0)*100:.0f}%)" \
            if "item_meta" in s else "—"
        out.append(
            f"| {s['category']} | {s['n_users']:,} | {s['n_items']:,} | {s['n_interactions']:,} "
            f"| {s['avg_seq_len']} | {s['median_seq_len']} | {s['sparsity']} | {mcov} |")
    out += ["", "## Leave-one-out split row counts", "",
            "| Category | direct train | valid | test | " +
            " | ".join([f"seq{l} train" for l in maxlens]) + " |",
            "|----------|-------------:|------:|-----:|" + "".join("------------:|" for _ in maxlens)]
    for s in all_stats:
        row = (f"| {s['category']} | {s['last_out_direct']['train']:,} | "
               f"{s['last_out_direct']['valid']:,} | {s['last_out_direct']['test']:,} | ")
        row += " | ".join(f"{s['seq_w_his'][l]['train']:,}" for l in maxlens) + " |"
        out.append(row)
    if any("validation" in s for s in all_stats):
        out += ["", "## Validation vs official 5-core", "",
                "| Category | my 5core | official | match | my #test | official #test | match |",
                "|----------|---------:|---------:|:-----:|---------:|---------------:|:-----:|"]
        for s in all_stats:
            v = s.get("validation", {})
            out.append(
                f"| {s['category']} | {v.get('my_5core_interactions','—'):,} | "
                f"{v.get('official_5core_interactions','—'):,} | "
                f"{'OK' if v.get('interactions_match') else 'X'} | "
                f"{v.get('my_test_rows','—'):,} | {v.get('official_last_out_test_rows','—'):,} | "
                f"{'OK' if v.get('test_rows_match') else 'X'} |")
    with open(os.path.join(out_root, "stats.md"), "w") as f:
        f.write("\n".join(out) + "\n")


def parse_args():
    here = os.path.dirname(os.path.abspath(__file__))
    p = argparse.ArgumentParser(description="Amazon Reviews 2023 data processing (JSONL + item meta)")
    p.add_argument("--categories", nargs="+", default=DEFAULT_CATEGORIES)
    p.add_argument("--maxlens", nargs="+", type=int, default=[20, 50])
    p.add_argument("--out", default=os.path.join(here, "processed"))
    p.add_argument("--cache", default=os.path.join(here, "hf_cache"))
    p.add_argument("--no-validate", action="store_true")
    p.add_argument("--no-meta", action="store_true", help="skip item metadata join")
    p.add_argument("--from-5core-cats", nargs="*",
                   default=["Books", "Beauty_and_Personal_Care"],
                   help="categories processed from the official pre-filtered 5-core data "
                        "(memory-light path for very large categories)")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(args.cache, exist_ok=True)
    print(f"Categories: {args.categories}\nMax lengths: {args.maxlens}\nOutput: {args.out}")
    big = set(args.from_5core_cats or [])
    all_stats = []
    for cat in args.categories:
        try:
            all_stats.append(process_category(
                cat, args.out, args.cache, args.maxlens,
                validate=not args.no_validate, from_5core=cat in big,
                with_meta=not args.no_meta))
            write_stats(all_stats, args.out, args.maxlens)
        except Exception as e:
            print(f"  !! FAILED {cat}: {type(e).__name__}: {e}", file=sys.stderr)
    write_stats(all_stats, args.out, args.maxlens)
    print(f"\nAll done. Stats -> {os.path.join(args.out, 'stats.md')}")


if __name__ == "__main__":
    main()
