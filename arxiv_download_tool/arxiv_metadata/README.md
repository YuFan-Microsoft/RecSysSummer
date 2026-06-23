# arXiv title index

`arxiv_title_index.tsv` is a compact local lookup table built from arXiv's
official **OAI-PMH** bulk metadata feed (`export.arxiv.org/oai2`,
`metadataPrefix=arXiv`). It exists so we can map a paper title to its arXiv id
**offline and instantly**, instead of issuing one rate-limited API call per
paper.

## Format

One paper per line, tab-separated, three fields, in their **original arXiv
casing**:

```
<arxiv_id>\t<title>\t<first_author>
```

Example:

```
2304.11406	LaMP: When Large Language Models Meet Personalization	Alireza Salemi
```

- `title` and `first_author` are stored exactly as arXiv provides them (real
  capitalisation and accents preserved, e.g. `LaMP`, `NeRF`, `Loïc Foissy`);
  only surrounding whitespace is collapsed.
- The matcher normalises on the fly (lower-cases the title, strips to
  `[a-z0-9 ]`, transliterates unicode/LaTeX, and takes the first author's
  surname), so display casing never affects lookups.
- Only these three fields are stored — **no abstracts, no PDFs, no full text.**

## Provenance

- Source: arXiv OAI-PMH, metadata only, single connection, polite (honors
  `Retry-After` / 503 flow control).
- Date window: papers with an OAI datestamp (last-modified) in the harvested
  range (see the run log). Because the datestamp is the modification date, this
  also captures older papers revised within the window.

## Regenerate / extend

From `../papers/accepted/`:

```bash
# harvest metadata + fill arxiv links into the accepted/*.json files
python3 _arxiv_bulk.py all --from 2022-01-01

# only (re)build the index
python3 _arxiv_bulk.py harvest --from 2022-01-01

# only match an existing index into the JSONs
python3 _arxiv_bulk.py match
```
