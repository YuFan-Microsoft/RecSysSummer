#!/usr/bin/env python3
"""Create a paper-reading-note markdown skeleton from an arXiv id/URL.

Pulls structured metadata from the arXiv Atom API (title, authors, abs/pdf
links, venue from the comment field, categories, published/updated dates) and
writes a markdown file whose header holds that metadata and whose body is an
empty placeholder for the reader's reflections (感悟).

Usage:
  python3 scaffold_note.py <arxiv-id-or-url> [--dir DIR] [--force] [--print]

  <arxiv-id-or-url>  e.g. 2603.23183, 2603.23183v2, or any arxiv.org/abs|pdf URL
  --dir DIR          output directory (default: ./paper_reading_notes)
  --force            overwrite an existing note file
  --print            print the markdown to stdout instead of writing a file

Prints the path of the file written (or NOOP:<path> if it already exists).
Uses only the Python standard library.
"""
import argparse
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

PLACEHOLDER = "<!-- Reflections / reading notes go here -->"


def find_arxiv_id(s):
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", s)
    if not m:
        sys.exit(f"ERROR: could not find an arXiv id in {s!r}")
    return m.group(1), (m.group(2) or "")


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def fetch_meta(base_id):
    url = f"https://export.arxiv.org/api/query?id_list={base_id}"
    feed = ET.fromstring(http_get(url))
    entry = feed.find(f"{ATOM}entry")
    if entry is None:
        sys.exit(f"ERROR: no arXiv entry found for {base_id}")
    # arXiv sometimes returns an error entry with no published date.
    if entry.find(f"{ATOM}published") is None:
        sys.exit(f"ERROR: arXiv returned no metadata for {base_id} "
                 "(is the id correct?)")

    def text(tag):
        el = entry.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    title = re.sub(r"\s+", " ", text(f"{ATOM}title")).strip()
    authors = [re.sub(r"\s+", " ", (a.findtext(f"{ATOM}name") or "").strip())
               for a in entry.findall(f"{ATOM}author")]
    authors = [a for a in authors if a]

    full_id = text(f"{ATOM}id")  # e.g. http://arxiv.org/abs/2603.23183v2
    vm = re.search(r"(v\d+)$", full_id)
    version = vm.group(1) if vm else ""

    comment = text(f"{ARXIV}comment")
    primary = entry.find(f"{ARXIV}primary_category")
    primary = primary.get("term") if primary is not None else ""
    cats = [c.get("term") for c in entry.findall(f"{ATOM}category")]
    ordered = ([primary] if primary else []) + [c for c in cats if c != primary]

    return {
        "id": base_id,
        "version": version,
        "title": title,
        "authors": authors,
        "published": text(f"{ATOM}published")[:10],
        "updated": text(f"{ATOM}updated")[:10],
        "comment": comment,
        "primary": primary,
        "categories": ordered,
    }


def build_markdown(m):
    dash = "\u2014"  # em dash for missing fields
    ver = f" ({m['version']})" if m["version"] else ""
    authors = ", ".join(m["authors"]) if m["authors"] else dash
    venue = m["comment"] or dash

    cat_line = dash
    if m["categories"]:
        head = f"{m['categories'][0]} (primary)" if m["primary"] else m["categories"][0]
        rest = [c for c in m["categories"][1:]]
        cat_line = ", ".join([head] + rest)

    dates = m["published"] or dash
    if m["updated"] and m["updated"] != m["published"]:
        dates += f" \u00b7 **Updated:** {m['updated']}"

    return (
        f"# {m['title'] or dash}\n\n"
        f"**Authors:** {authors}\n\n"
        f"**arXiv:** https://arxiv.org/abs/{m['id']}{ver}\n\n"
        f"**PDF:** https://arxiv.org/pdf/{m['id']}\n\n"
        f"**Venue:** {venue}\n\n"
        f"**Categories:** {cat_line}\n\n"
        f"**Published:** {dates}\n\n"
        f"---\n\n"
        f"{PLACEHOLDER}\n"
    )


def safe_filename(title, base_id):
    name = title or base_id
    name = name.replace("/", "-").replace(":", " -")
    name = re.sub(r'[<>:"\\|?*\n\r\t]', " ", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(".")
    return (name or base_id) + ".md"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="arXiv id or URL")
    ap.add_argument("--dir", default="paper_reading_notes")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--print", dest="to_stdout", action="store_true")
    args = ap.parse_args()

    base_id, _ = find_arxiv_id(args.source.strip())
    meta = fetch_meta(base_id)
    md = build_markdown(meta)

    if args.to_stdout:
        sys.stdout.write(md)
        return

    os.makedirs(args.dir, exist_ok=True)
    path = os.path.join(args.dir, safe_filename(meta["title"], base_id))
    if os.path.exists(path) and not args.force:
        print(f"NOOP:{path} (already exists; use --force to overwrite)")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    print(path)


if __name__ == "__main__":
    main()
