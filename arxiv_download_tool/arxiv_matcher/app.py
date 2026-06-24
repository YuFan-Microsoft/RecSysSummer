"""Apple-styled Gradio front-end for the arXiv title matcher.

Type a paper title and its first author; the app runs embedding recall ->
reranker -> edit-distance/author adjudication and tells you the matched arXiv
id/url (or that no confident match was found), plus the ranked candidates.

    python app.py
"""

from __future__ import annotations

import gradio as gr

from common import load_config
from matcher import ArxivTitleMatcher

CFG = load_config()
MATCHER = ArxivTitleMatcher()  # loads index + both 0.6B models once at startup

CSS = """
:root {
  --bg: #f5f5f7; --card: #ffffff; --ink: #1d1d1f; --sub: #6e6e73;
  --accent: #0071e3; --accent-press: #0060c0; --line: #e5e5ea;
  --ok: #1d8a3f; --bad: #c0392b;
}
* { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
    "Helvetica Neue", Helvetica, Arial, sans-serif !important; }
html, body, gradio-app, .gradio-container {
    background: linear-gradient(180deg, #fbfbfd 0%, #f5f5f7 100%) !important; }
.gradio-container { max-width: 1100px !important; margin: 0 auto !important;
    padding: 0 28px 48px !important; }
footer { display: none !important; }

#hero { text-align: center; padding: 40px 0 6px; }
#hero h1 { font-size: 40px; font-weight: 600; letter-spacing: -0.02em;
    color: var(--ink); margin: 0; }
#hero p { font-size: 17px; color: var(--sub); margin: 8px 0 0; }

#searchbar { background: var(--card); border: 1px solid var(--line);
    border-radius: 18px; padding: 12px; box-shadow: 0 6px 24px rgba(0,0,0,0.05);
    margin-top: 16px; }
#searchbar textarea, #searchbar input { font-size: 16px !important;
    border: none !important; background: transparent !important; box-shadow: none !important; }

button.primary, #go-btn { background: var(--accent) !important; color: #fff !important;
    border: none !important; border-radius: 980px !important; font-weight: 500 !important;
    font-size: 16px !important; }
button.primary:hover, #go-btn:hover { background: var(--accent-press) !important; }

#result-card { background: var(--card); border: 1px solid var(--line);
    border-radius: 22px; padding: 26px 32px; margin-top: 18px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.06); }
#result-card h1 { font-size: 24px; }
#result-card a { color: var(--accent); text-decoration: none; }
.meta-badge { display: inline-block; background: #f0f0f4; color: var(--sub);
    border-radius: 980px; padding: 4px 12px; font-size: 13px; font-weight: 500;
    margin: 0 8px 8px 0; }
.meta-ok { background: rgba(52,199,89,0.16); color: var(--ok); }
.meta-bad { background: rgba(192,57,43,0.12); color: var(--bad); }
.meta-accent { background: rgba(0,113,227,0.12); color: var(--accent); }
"""

INTRO = """
<div id="hero">
  <h1>arXiv Title Matcher</h1>
  <p>Find the arXiv paper that matches a title, and get its arXiv id / url.</p>
</div>
"""


def _render(res) -> str:
    if res is None:
        return "_Enter a title and first author, then press Match._"

    if res.matched:
        head = (
            f"<span class='meta-badge meta-ok'>MATCH</span>"
            f"<span class='meta-badge meta-accent'>{res.arxiv_id}</span>"
        )
        link = f"\n\n### [{res.arxiv_url}]({res.arxiv_url})"
    else:
        head = "<span class='meta-badge meta-bad'>NO CONFIDENT MATCH</span>"
        link = ""

    author_badge = "meta-ok" if res.author_ok else "meta-bad"
    badges = (
        head
        + f"<span class='meta-badge'>title_sim {res.title_sim:.3f}</span>"
        + f"<span class='meta-badge'>rerank {res.rerank_score:.3f}</span>"
        + f"<span class='meta-badge'>recall {res.recall_score:.3f}</span>"
        + f"<span class='meta-badge {author_badge}'>"
        + f"author {'ok' if res.author_ok else 'mismatch'}</span>"
    )

    lines = [badges, link, "", f"**Best candidate title:** {res.matched_title}", ""]
    lines.append("| # | rerank | recall | arXiv id | candidate title | surname |")
    lines.append("|---|--------|--------|----------|-----------------|---------|")
    for i, c in enumerate(res.candidates or [], start=1):
        title = c["title"] if len(c["title"]) <= 70 else c["title"][:69] + "…"
        lines.append(
            f"| {i} | {c['rerank']:.3f} | {c['recall']:.3f} | "
            f"`{c['arxiv_id']}` | {title} | {c['surname']} |"
        )
    return "\n".join(lines)


def do_match(title: str, author: str):
    title = (title or "").strip()
    if not title:
        return _render(None)
    res = MATCHER.match(title, (author or "").strip())
    return _render(res)


def build_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="arXiv Title Matcher", theme=gr.themes.Soft()) as demo:
        gr.HTML(INTRO)

        with gr.Column(elem_id="searchbar"):
            title_box = gr.Textbox(
                placeholder="Paper title, e.g. Optimal Baseline Corrections for Off-Policy Contextual Bandits",
                label="Title",
                lines=1,
            )
            with gr.Row():
                author_box = gr.Textbox(
                    placeholder="First author, e.g. Shashank Gupta",
                    label="First author",
                    lines=1,
                    scale=8,
                )
                go_btn = gr.Button("Match", elem_id="go-btn", scale=1, variant="primary")

        card = gr.Markdown(_render(None), elem_id="result-card")

        go_btn.click(do_match, inputs=[title_box, author_box], outputs=card)
        title_box.submit(do_match, inputs=[title_box, author_box], outputs=card)
        author_box.submit(do_match, inputs=[title_box, author_box], outputs=card)
    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.queue().launch(
        share=bool(CFG.get("share", True)),
        server_name="0.0.0.0",
        server_port=int(CFG.get("server_port", 7860)),
    )
