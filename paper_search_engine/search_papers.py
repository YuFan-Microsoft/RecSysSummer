#!/usr/bin/env python3
"""CLI client for the **Paper Idea Search** service (``app.py``).

Describe a research idea in free text and get back the most relevant papers,
ranked by the running Gradio app (Qwen3-Embedding-8B recall -> Qwen3-Reranker-8B
rerank). This is a thin, dependency-free wrapper around the app's existing HTTP
API -- it does **not** require any change to the Gradio app.

Endpoint URL resolution order (first hit wins):
  1. ``--url`` argument
  2. ``PAPER_SEARCH_URL`` environment variable
  3. ``search_endpoint.txt`` next to this file (first non-comment, non-empty line)

The live URL is a Gradio ``*.gradio.live`` share link that rotates every few
days -- update it by editing ``search_endpoint.txt`` (or exporting the env var).

The app exposes ``do_search(query, top_k)``. Its full result objects live in a
``gr.State`` (not sent over the API), so the API returns the ranked list of
papers plus the fully-rendered text of the top hit -- which is exactly what an
idea search needs.

Usage:
    python3 search_papers.py "generative retrieval with semantic IDs"
    python3 search_papers.py "LLM-based CTR prediction" -k 10
    python3 search_papers.py "cold-start sequential rec" --list-only --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENDPOINT_FILE = HERE / "search_endpoint.txt"
API_PREFIX = "/gradio_api"  # Gradio 5/6 default; 4.x uses "" (both tried below)
TIMEOUT = 240


# --------------------------------------------------------------------------
# Endpoint URL resolution
# --------------------------------------------------------------------------
def resolve_url(cli_url: str | None) -> str:
    url = cli_url or os.environ.get("PAPER_SEARCH_URL")
    if not url and ENDPOINT_FILE.exists():
        for line in ENDPOINT_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                url = line
                break
    if not url:
        sys.exit(
            "No endpoint URL. Pass --url, set PAPER_SEARCH_URL, or put the "
            f"gradio.live link in {ENDPOINT_FILE}"
        )
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


# --------------------------------------------------------------------------
# Gradio call protocol:  POST /call/<fn> -> event_id ; GET stream -> outputs
# --------------------------------------------------------------------------
def _post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _stream_result(url: str):
    """Read a Gradio SSE event stream, return the payload of the final event."""
    req = urllib.request.Request(url, method="GET")
    last_event = None
    data_buf: list[str] = []
    final = None
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        for raw in resp:
            line = raw.decode("utf-8").rstrip("\n")
            if line.startswith("event:"):
                last_event = line[6:].strip()
                data_buf = []
            elif line.startswith("data:"):
                data_buf.append(line[5:].lstrip())
            elif line == "":  # blank line terminates one SSE message
                if last_event in ("complete", "error") and data_buf:
                    final = ("\n".join(data_buf), last_event)
                    if last_event == "complete":
                        break
    if final is None:
        raise RuntimeError("no terminal event in stream")
    payload, event = final
    if event == "error":
        raise RuntimeError(f"server error: {payload}")
    return json.loads(payload)


def call_fn(base: str, api_name: str, data: list) -> list:
    """Invoke one named Gradio endpoint, return its list of outputs."""
    last_err: Exception | None = None
    for prefix in (API_PREFIX, ""):  # try v5/6 prefix, then bare (v4)
        post_url = f"{base}{prefix}/call/{api_name}"
        try:
            event_id = _post_json(post_url, {"data": data}).get("event_id")
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 404:
                continue
            raise
        if not event_id:
            continue
        return _stream_result(f"{post_url}/{event_id}")
    raise last_err or RuntimeError(f"could not call {api_name!r}")


# --------------------------------------------------------------------------
# Idea search
# --------------------------------------------------------------------------
def search(base: str, idea: str, top_k: int) -> dict:
    """Run an idea search via ``do_search``.

    do_search outputs = [state(None), state(None), radio_update, top_markdown];
    the two ``gr.State`` slots are null over the API, so we read the ranked list
    from the radio update and the full text of the #1 paper from the markdown.
    """
    out = call_fn(base, "do_search", [idea, top_k])
    choices, top_md = [], None
    for item in out:
        if isinstance(item, dict) and "choices" in item:
            choices = item["choices"]
        elif isinstance(item, str):
            top_md = item
    results = [{"rank": idx + 1, "label": label} for label, idx in choices]
    return {"idea": idea, "results": results, "top_markdown": top_md}


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Search papers by research idea.")
    ap.add_argument("idea", nargs="+", help="research idea / free-text query")
    ap.add_argument("-k", "--top-k", type=int, default=15, help="number of papers")
    ap.add_argument("--url", default=None, help="override endpoint URL")
    ap.add_argument("--list-only", action="store_true",
                    help="hide the full text of the top paper")
    ap.add_argument("--json", action="store_true", help="emit raw JSON")
    args = ap.parse_args()

    base = resolve_url(args.url)
    idea = " ".join(args.idea)
    res = search(base, idea, args.top_k)
    if args.list_only:
        res = {**res, "top_markdown": None}

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    print(f"idea: {idea}\nendpoint: {base}\n")
    if not res["results"]:
        print("(no results)")
        return
    for r in res["results"]:
        print(r["label"])
    if res.get("top_markdown"):
        print("\n--- top result (full text) ---\n" + res["top_markdown"])


if __name__ == "__main__":
    main()
