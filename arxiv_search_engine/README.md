# arXiv Search Engine

Two-stage semantic search over **5 years of arXiv** (2020–2026) using each
paper's **title + abstract** as the index text — `Qwen3-Embedding-4B` recall →
`Qwen3-Reranker-8B` rerank — with three query-time controls:

| Control | Behaviour |
|---|---|
| **Domain** | **Single-select.** The index covers **all** domains, but every search targets exactly **one** (the web app lists the domains you've actually built). |
| **Year(s)** | **Multi-select.** Keep only papers published in the chosen years (e.g. just 2024 + 2025). Empty selection = all years. |
| **Sort** | Order the results by **relevance** (reranker score) or by **citation count**. |

## Data

The corpus is the Hugging Face dataset
[`yufan/arxiv-metadata-2020-2026`](https://huggingface.co/datasets/yufan/arxiv-metadata-2020-2026)
(~1.45M papers, 2.3 GB), stored as `<Domain>/<year>/metadata.jsonl` — one JSON
paper per line. Download it with [`download_data.py`](download_data.py) (see
below). Every `fieldsOfStudy` is a searchable domain; `build_index.py` builds a
shard for **all** of them:

| Domain (folder) | Papers | | Domain (folder) | Papers |
|---|---:|---|---|---:|
| `Computer_Science` | 656,684 | | `Chemistry` | 404 |
| `Physics` | 438,722 | | `Geology` | 401 |
| `Mathematics` | 243,044 | | `Business` | 369 |
| `Medicine` | 39,162 | | `Environmental_Science` | 358 |
| `Engineering` | 32,925 | | `Psychology` | 326 |
| `Economics` | 14,358 | | `Geography` | 229 |
| `Biology` | 10,443 | | `Political_Science` | 159 |
| `Materials_Science` | 5,398 | | `Sociology` | 131 |
| `Unknown` | 4,985 | | `Philosophy` | 69 |
| | | | `History` / `Art` | 63 / 10 |

The domain list lives in [`config.yaml`](config.yaml) under `domains:`.

## How it works

```
data_dir/<Domain>/<year>/metadata.jsonl        # one JSON paper per line (HF layout)
        │
        ▼  build_index.py  (embed title + abstract, ALL domains)
index_dir/<Domain>/embeddings.npy              # (N, dim) float32, L2-normalised
index_dir/<Domain>/metadata.json               # parallel paper records
        │
        ▼  search.py / app.py  (serve per your selection)
   1. pick the ONE chosen domain's shard
   2. keep only rows whose year is selected
   3. embedding recall  → top recall_k
   4. reranker          → top rerank_k (the result set)
   5. sort by relevance OR citation count
```

The index is **sharded by domain** (one folder per domain) because the domain
filter is single-select: a query only ever loads the one shard it needs, so even
`Computer_Science` (~650k papers) stays quick to search.

## Files

| File | Purpose |
|---|---|
| [`config.yaml`](config.yaml) | paths, model locations, domains, years, retrieval sizes |
| [`common.py`](common.py) | config loader + `ArxivPaper` parsing from `metadata.jsonl` |
| [`download_data.py`](download_data.py) | download the corpus from Hugging Face into `data_dir` |
| [`embedder.py`](embedder.py) | `Qwen3-Embedding-4B` wrapper (recall) |
| [`reranker.py`](reranker.py) | `Qwen3-Reranker-8B` wrapper (rerank) |
| [`build_index.py`](build_index.py) | build per-domain embedding shards (multi-GPU) |
| [`search.py`](search.py) | `SearchEngine` with domain/year filters + sort |
| [`app.py`](app.py) | Apple-styled Gradio web UI |
| [`search_arxiv.py`](search_arxiv.py) | command-line client for the running app |

## Setup

```bash
pip install -r requirements.txt
```

Edit [`config.yaml`](config.yaml):

- `data_dir` — where the downloaded `<Domain>/<year>/metadata.jsonl` files live
  (defaults to `./arxiv_metadata_hf`).
- `index_dir` — where the built shards are written.
- `embedding_model_path` / `reranker_model_path` — local paths to the
  `Qwen3-Embedding-4B` and `Qwen3-Reranker-8B` models.
- **GPUs** (0 and 1 are reserved — only 2–7 may be used):
  - `index_gpus: [2, 3, 4, 5, 6, 7]` — index building fans out over all of
    these (one worker process per GPU).
  - `embedding_device: cuda:2` / `reranker_device: cuda:3` — inference (search +
    web app) uses just these two so both models can be held at once.

## Download the data (Hugging Face)

```bash
# everything: all domains, all years (~2.3 GB) -> data_dir
python download_data.py

# or just some domains / years
python download_data.py --domain Physics
python download_data.py --domain Medicine --years 2024 2025
```

## Build the index

Building embeds the title + abstract of every paper, so it is the heavy step
(run it on the GPU box). It fans out across every GPU in `index_gpus` (2–7 by
default) — one worker process per GPU — so a domain is split into equal slices
and embedded in parallel. It builds **all** domains by default; build one at a
time or all at once:

```bash
# quick smoke test — index the first 500 papers of one domain
python build_index.py --domain Medicine --limit 500

# build a single domain (fans out over index_gpus)
python build_index.py --domain Physics

# build every domain in config.yaml
python build_index.py

# override which GPUs to use for this run
python build_index.py --domain Physics --gpus 2 3 4 5 6 7
```

Each domain writes `index_dir/<Domain>/embeddings.npy` +
`index_dir/<Domain>/metadata.json`.

## Search

**Web UI** (domain dropdown, year checkboxes, sort toggle, top-K slider):

```bash
python app.py          # serves on port 7861, prints a gradio.live share link
```

**From Python:**

```python
from search import SearchEngine
engine = SearchEngine()
hits = engine.search(
    "diffusion models for video generation",
    domain="Computer_Science",
    years=[2024, 2025],     # None / [] = all years
    sort_by="citation",     # or "relevance"
    rerank_k=15,
)
for h in hits:
    print(h.rank, h.year, h.citation_count, h.title)
```

**From the command line** (against the running `app.py` — paste its share link
into [`arxiv_search_endpoint.txt`](arxiv_search_endpoint.txt) or pass `--url`):

```bash
python search_arxiv.py "black hole thermodynamics" \
    --domain Physics --years 2024 2025 --sort citation -k 10
```
