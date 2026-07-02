---
name: paper-reading-notes
description: >-
    Use this skill when the user wants to read papers together and keep running
    reading notes / reflections (感悟) as markdown files under a
    `paper_reading_notes/` folder in the current repo. Trigger it when the user
    says things like "我们一起读论文", "读完的感悟写成 md", "建个 paper_reading_notes",
    "帮我记读书笔记", gives an arXiv link/id/title and asks to start a note, or
    asks to record takeaways / 感悟 / reading notes for a paper. Two stages:
    (1) scaffold a markdown file whose header holds the paper metadata (title,
    authors, arXiv/PDF links, venue, categories, dates) pulled from arXiv, with
    an empty body placeholder; (2) after reading, fill that placeholder with the
    user's reflections in English. This is lighter and more personal than the
    full paper-reading 12-section analysis, and unlike paper-to-email it stays
    as local markdown.
---

# Paper Reading Notes

A lightweight, two-stage workflow for reading papers with the user and keeping
personal reflection notes as markdown, one file per paper, under a
`paper_reading_notes/` folder in the current repository.

- Lighter than `paper-reading` (which produces a formal 12-section English
  analysis). Here the body is a personal, honest reflection written in English.
- Unlike `paper-to-email`, the deliverable stays as a local markdown file; no
  email is sent.

## When to use / not use

Use it when the user is reading a specific paper and wants a note saved to
markdown. If the user instead asks for a deep formal analysis, use
`paper-reading`; if they want it emailed, use `paper-to-email`.

## Stage 1 — Scaffold the note (metadata skeleton)

As soon as the user picks a paper (arXiv link, id, or title), create the note
file first, before reading. Use the helper script; it pulls structured metadata
from the arXiv Atom API and writes the skeleton:

```bash
python3 "$HOME/.copilot/skills/paper-reading-notes/scaffold_note.py" \
  <arxiv-id-or-url> --dir "<repo>/paper_reading_notes"
```

- Default `--dir` is `paper_reading_notes` relative to the current working
  directory. Pass an absolute path (or `cd` to the repo root first) so the file
  lands in the right repo folder.
- The filename is the paper's exact title (sanitized for the filesystem) plus
  `.md`, so notes stay searchable by title.
- The script does NOT overwrite an existing note unless you pass `--force`; it
  prints `NOOP:<path>` in that case. Use `--print` to preview without writing.
- The generated header contains: title (H1), authors, `abs` and `pdf` links,
  venue (from the arXiv comment, e.g. "Accepted by KDD 2026"), categories,
  published/updated dates, an `---` rule, and the body placeholder
  `<!-- Reflections / reading notes go here -->`.

The header always looks like this — keep this exact shape:

```markdown
# <Exact paper title>

**Authors:** <author 1, author 2, ...>

**arXiv:** https://arxiv.org/abs/<id> (v<n>)

**PDF:** https://arxiv.org/pdf/<id>

**Venue:** <arXiv comment, e.g. Accepted by KDD 2026, or an em dash if none>

**Categories:** <primary> (primary), <others>

**Published:** <YYYY-MM-DD> · **Updated:** <YYYY-MM-DD>

---

<!-- Reflections / reading notes go here -->
```

If the paper is not on arXiv, create the file by hand with the same header
shape, filling every metadata field you can and using an em dash (—) for any
field you cannot determine.

Only an arXiv id is needed for the metadata. Do not fabricate fields; the script
already leaves an em dash for anything arXiv does not provide.

## Stage 2 — Write the reflection while / after reading

You can write the note incrementally as you read together (abstract first, then
method, then experiments), not only at the very end. Whenever you write from
partial reading, mark the reading progress at the top of the body and label
anything you have not yet verified.

Read *with* the user — the loop that worked:

1. Let the user state their own understanding first.
2. Confirm what is right, then sharpen it: pin down the precise lineage and the
   exact causal chain (e.g. "the backbone changed from X to Y, and that is what
   creates problem Z"), not a vague summary.
3. Surface the questions the body must settle, and record them in the note.

The user drives the reading order and pace. Do **not** end a turn by asking which
section to read next — wait for the user to share their own reading of the next
part, then verify it, sharpen it, and record it.

To go deeper, get the full text (never rely on the abstract for method or
results). Prefer the **PDF** as the source of truth: the arXiv HTML render can be
lossy and has, in practice, fabricated sentences that were never in the paper.
Download the PDF and extract text with pymupdf:

```bash
cd /tmp && curl -sL "https://arxiv.org/pdf/<id>" -o paper.pdf
python3 - <<'PY'
import fitz  # pip install pymupdf
d = fitz.open("/tmp/paper.pdf")
t = "".join(p.get_text() for p in d).replace("\x00", "")
open("/tmp/paper.txt", "w").write(t)
print("pages", d.page_count, "chars", len(t))
PY
```

If a claim is surprising, or the user challenges one, verify it against the PDF
text (grep the extracted file) before asserting it — do not over-correct the user
from a lossy source. For a non-arXiv or non-PDF source, fall back to extracting
the page's HTML text directly (for example with the `paper-to-email` skill's
`fetch_paper.py` helper, if that skill happens to be installed). The PDF path
above needs only `curl` and `pymupdf` and is self-contained.

Read the intro, method, and experiments (and appendix when it matters), then
write into the `<!-- Reflections / reading notes go here -->` placeholder.

Language and voice:

- Write the reflection entirely in English. The user explicitly wants these
  reading notes written in English, even though general chat with the user is in
  Chinese. Keep standard technical terms as-is (Semantic ID, SID, generative
  recommendation, reinforcement learning, attention, ablation).
- It is a personal reading note, not a paper summary. Say what actually clicked,
  what is genuinely new, and what you doubt; do not just restate the abstract.
- **Readability comes before brevity.** The user dislikes dense, telegraphic
  shorthand. Do not glue clauses together with arrows (`→`) or equals signs, do
  not lean on heavy abbreviations, and never cram many ideas onto one long line.
  Write **complete, natural sentences**, group them into **short paragraphs**,
  and use **headings, sub-headings, and nested bullets** to give the note
  hierarchy and breathing room. Stay substantive and insightful, but whenever
  brevity would hurt readability, choose readability. Reserve arrows and symbols
  for actual math, not prose.

Keep the source discipline from the paper-reading skill: distinguish what the
**paper states** from your own **inference** and **speculation**; do not present
a guess as a fact. Mark inferences inline with *(inference)* and open questions
with *(open)*.

Note structure the user endorsed (use it; adapt or drop parts per paper). Every
section is written as complete sentences in short paragraphs, not as terse
fragments:

- A **reading-progress** marker as an HTML comment at the very top, for example
  `<!-- Reading progress: abstract, plus §1 to §3. §4 still to read. Verified against the PDF. Statements are the paper's unless marked (inference). -->`.
- **TL;DR** — a short paragraph that says what the method is and the one thing the
  paper stands or falls on.
- **Where it sits** — the lineage and where the paper fits. Use a **comparison
  table** when several approaches need to be contrasted, for example the
  different item representations.
- **What the paper actually does** — the real mechanism, correcting the
  misreadings that are easy to make; the challenges mapped to the design that
  answers each; and the core bet, meaning what is rented from prior components
  versus built here.
- **Method** — grouped by stage, with a bold `§x.y` sub-heading for each
  component, a paragraph of explanation, and nested bullets only for genuinely
  parallel parts. Put every equation in LaTeX.
- **Reader's insights and open questions** — the few sharp questions that decide
  whether the claim holds (attribution, reward design, interpretability), and the
  reader's own follow-up ideas, each marked *(my idea)*.
- **Net read** — a verdict of two or three sentences: is it well-framed, and what
  one thing does it stand or fall on.
- End an unfinished note with a `<!-- To be continued: ... -->` marker so a later
  session knows where to resume.

A fully worked example of this structure and style lives in this repo at
`paper_reading_notes/Reasoning over Semantic IDs Enhances Generative Recommendation.md`.

## Notes

- Always scaffold (Stage 1) before reading so the file exists even if the read
  happens later or across sessions.
- Write math as **GitHub-flavored LaTeX** (`$...$` inline, `$$...$$` display), not
  plain Unicode — the user reads these notes on GitHub (MathJax renders it), and
  plain-text subscripts like `r_{l-1}` otherwise risk breaking into italics.
- After writing the reflection, give the user a short (<100 word) Chinese
  summary in chat and the path to the note file.
- If beautifulsoup4 is missing for the fetcher: `python3 -m pip install
  beautifulsoup4`. The scaffold script itself needs only the standard library.
