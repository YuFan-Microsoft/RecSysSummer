"""Apple-styled Gradio front-end for the arXiv search engine.

Type a research topic, pick a single domain, optionally narrow to some years,
and choose whether to order the results by relevance or by citation count.
Results are produced by embedding recall -> reranker, then flipped through one
card at a time from the left-hand list.

    python app.py
"""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from common import load_config
from search import SORT_CITATION, SORT_RELEVANCE, SearchEngine

CFG = load_config()
ENGINE = SearchEngine()  # loads both models once at startup

DOMAIN_LABELS = CFG.get("domain_labels", {})
YEARS = [int(y) for y in CFG["years"]]


def _available_domains() -> list[str]:
    """Domains whose shard has actually been built (fall back to config order).

    build_index.py covers every domain, but a user may have only built some of
    them. Serving only offers domains that are actually searchable.
    """
    index_dir = Path(CFG["index_dir"]).expanduser()
    built = [d for d in CFG["domains"] if (index_dir / d / "embeddings.npy").exists()]
    return built or list(CFG["domains"])


DOMAINS = _available_domains()

# Choices are (label, value) pairs so the UI can show pretty names.
DOMAIN_CHOICES = [(DOMAIN_LABELS.get(d, d), d) for d in DOMAINS]
SORT_CHOICES = [("Relevance", SORT_RELEVANCE), ("Citations", SORT_CITATION)]

# --------------------------------------------------------------------------
# Apple-flavoured styling
# --------------------------------------------------------------------------
CSS = """
:root {
  --bg: #f5f5f7;
  --card: #ffffff;
  --ink: #1d1d1f;
  --sub: #6e6e73;
  --accent: #0071e3;
  --accent-press: #0060c0;
  --line: #e5e5ea;
}
* { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
    "Helvetica Neue", Helvetica, Arial, sans-serif !important; }
html, body, gradio-app, .gradio-container {
    background: linear-gradient(180deg, #fbfbfd 0%, #f5f5f7 100%) !important; }
.gradio-container { max-width: 100% !important; width: 100% !important;
    margin: 0 auto !important; padding: 0 28px 48px !important; }
.gradio-container .main, .gradio-container .wrap, .gradio-container .contain,
.gradio-container > div, .app, .fillable { max-width: 100% !important; width: 100% !important; }
footer { display: none !important; }

#hero { text-align: center; padding: 40px 0 6px; }
#hero h1 { font-size: 42px; font-weight: 600; letter-spacing: -0.02em;
    color: var(--ink); margin: 0; }
#hero p { font-size: 18px; color: var(--sub); margin: 8px 0 0; }

#searchbar { background: var(--card); border: 1px solid var(--line);
    border-radius: 18px; padding: 10px; box-shadow: 0 6px 24px rgba(0,0,0,0.05);
    margin-top: 16px; }
#searchbar textarea, #searchbar input { font-size: 17px !important;
    border: none !important; background: transparent !important; box-shadow: none !important; }

button.primary, #go-btn { background: var(--accent) !important; color: #fff !important;
    border: none !important; border-radius: 980px !important; font-weight: 500 !important;
    font-size: 16px !important; }
button.primary:hover, #go-btn:hover { background: var(--accent-press) !important; }

/* ---- filter panel ---- */
#filters { background: var(--card); border: 1px solid var(--line);
    border-radius: 18px; padding: 14px 18px; margin-top: 12px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.05); }
#filters .gr-form, #filters fieldset { background: transparent !important;
    border: none !important; }
#filters label { font-size: 14px !important; }

/* ---- left results list ---- */
#result-list { background: var(--card); border: 1px solid var(--line);
    border-radius: 18px; padding: 8px; box-shadow: 0 6px 24px rgba(0,0,0,0.05);
    max-height: 78vh; overflow-y: auto; }
#result-list span[data-testid="block-info"], #result-list .head { display: none !important; }
#result-list fieldset { gap: 2px !important; }
#result-list label { display: flex !important; align-items: flex-start !important;
    border: none !important; border-radius: 12px !important; padding: 10px 12px !important;
    margin: 1px 0 !important; cursor: pointer; font-size: 13.5px !important;
    line-height: 1.4 !important; color: var(--ink) !important;
    background: transparent !important; transition: background .15s ease; }
#result-list label:hover { background: #f0f0f4 !important; }
#result-list label.selected, #result-list label:has(input:checked) {
    background: rgba(0,113,227,0.10) !important; color: var(--accent) !important;
    font-weight: 500 !important; }
#result-list input { accent-color: var(--accent); margin-top: 2px; }

#paper-card { background: var(--card); border: 1px solid var(--line);
    border-radius: 22px; padding: 30px 38px; margin-top: 4px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.06); min-height: 70vh; }
#paper-card h1 { font-size: 27px; letter-spacing: -0.01em; line-height: 1.25; }
#paper-card h2 { font-size: 20px; margin-top: 22px; color: var(--ink); }
#paper-card p, #paper-card li { font-size: 16px; line-height: 1.7; color: #2b2b2f; }
#paper-card a { color: var(--accent); text-decoration: none; }

.meta-badge { display: inline-block; background: #f0f0f4; color: var(--sub);
    border-radius: 980px; padding: 4px 12px; font-size: 13px; font-weight: 500;
    margin-right: 8px; }
.meta-accent { background: rgba(0,113,227,0.12); color: var(--accent); }
.meta-cite { background: rgba(52,199,89,0.14); color: #1d8a3f; }
"""

INTRO = """
<div id="hero">
  <h1>arXiv Finder</h1>
  <p>Search 5 years of arXiv by title &amp; abstract — filter by domain and year, rank by relevance or citations.</p>
</div>
"""


def _short_title(title: str, limit: int = 60) -> str:
    title = " ".join(title.split())
    return title if len(title) <= limit else title[: limit - 1].rstrip() + "…"


def _list_choices(results: list[dict]):
    """Build (label, index) choices for the left-hand results list."""
    choices = []
    for i, r in enumerate(results):
        year = r.get("year") or ""
        cites = r.get("citation_count", 0)
        tag = f"{year} · {cites} cites"
        choices.append((f"#{r['rank']}  {tag} · {_short_title(r['title'])}", i))
    return choices


def _render(results: list[dict], idx: int) -> str:
    """Render one result as markdown (one paper per page)."""
    if not results:
        return "_No results yet. Enter a topic, pick a domain, and press Search._"
    idx = max(0, min(idx, len(results) - 1))
    r = results[idx]

    badges = [f"<span class='meta-badge meta-accent'>#{r['rank']}</span>"]
    if r.get("year"):
        badges.append(f"<span class='meta-badge'>{r['year']}</span>")
    badges.append(
        f"<span class='meta-badge meta-cite'>{r.get('citation_count', 0)} citations</span>"
    )
    if r.get("influential_citation_count"):
        badges.append(
            f"<span class='meta-badge'>{r['influential_citation_count']} influential</span>"
        )
    badges.append(f"<span class='meta-badge'>rerank {r['rerank_score']:.3f}</span>")
    badges.append(f"<span class='meta-badge'>recall {r['recall_score']:.3f}</span>")
    badges_html = "".join(badges)

    authors = r.get("authors", "")
    abstract = r.get("abstract") or "_(no abstract available)_"
    link = f"\n\n[Open on arXiv]({r['arxiv_url']})" if r.get("arxiv_url") else ""

    parts = [badges_html, f"\n\n# {r['title']}"]
    if authors:
        parts.append(f"\n\n*{authors}*")
    parts.append(f"\n\n## Abstract\n\n{abstract}")
    parts.append(link)
    return "".join(parts)


def do_search(query, domain, years, sort_by, top_k):
    results = [
        r.to_dict()
        for r in ENGINE.search(
            query,
            domain=domain,
            years=[int(y) for y in years] if years else None,
            sort_by=sort_by,
            rerank_k=int(top_k),
        )
    ]
    idx = 0
    value = 0 if results else None
    return (
        results,
        idx,
        gr.update(choices=_list_choices(results), value=value),
        _render(results, idx),
    )


def on_select(results, selected):
    """Jump to the paper picked in the left list."""
    idx = int(selected) if selected is not None else 0
    return idx, _render(results, idx)


def build_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="arXiv Finder", theme=gr.themes.Soft()) as demo:
        results_state = gr.State([])
        idx_state = gr.State(0)

        gr.HTML(INTRO)

        with gr.Row(elem_id="searchbar"):
            query_box = gr.Textbox(
                placeholder="e.g. diffusion models for protein structure prediction",
                show_label=False,
                lines=1,
                scale=8,
                container=False,
            )
            go_btn = gr.Button("Search", elem_id="go-btn", scale=1, variant="primary")

        with gr.Row(elem_id="filters"):
            domain_radio = gr.Dropdown(
                choices=DOMAIN_CHOICES,
                value=DOMAINS[0],
                label="Domain (pick one)",
                filterable=True,
                scale=3,
            )
            year_check = gr.CheckboxGroup(
                choices=YEARS,
                value=[],
                label="Years (empty = all)",
                scale=4,
            )
            sort_radio = gr.Radio(
                choices=SORT_CHOICES,
                value=SORT_RELEVANCE,
                label="Sort by",
                scale=2,
            )
            topk_slider = gr.Slider(
                minimum=1,
                maximum=50,
                value=int(CFG.get("rerank_k", 15)),
                step=1,
                label="Top-K",
                scale=2,
            )

        with gr.Row(equal_height=False):
            with gr.Column(scale=3, min_width=260):
                result_list = gr.Radio(
                    choices=[],
                    value=None,
                    label="Results",
                    elem_id="result-list",
                    container=False,
                )
            with gr.Column(scale=7):
                card = gr.Markdown(_render([], 0), elem_id="paper-card")

        # wiring
        search_inputs = [query_box, domain_radio, year_check, sort_radio, topk_slider]
        search_outputs = [results_state, idx_state, result_list, card]
        go_btn.click(do_search, inputs=search_inputs, outputs=search_outputs)
        query_box.submit(do_search, inputs=search_inputs, outputs=search_outputs)

        result_list.input(
            on_select,
            inputs=[results_state, result_list],
            outputs=[idx_state, card],
        )
    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.queue().launch(
        share=bool(CFG.get("share", True)),
        server_name="0.0.0.0",
        server_port=int(CFG.get("server_port", 7861)),
    )
