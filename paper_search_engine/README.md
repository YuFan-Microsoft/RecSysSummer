# Paper Finder — semantic search over your Markdown papers

Two-stage semantic search over the `.md` papers collected by the arXiv tool:

1. **Recall** — embed the query with **Qwen3-Embedding-8B** and take the top candidates by cosine similarity. The recall pool size is derived automatically as `min(2 × top-K, recall_cap)` (default cap **100**).
2. **Rerank** — score those candidates with **Qwen3-Reranker-8B** and keep the top **K** (slider in the UI, default **15**).

A clean, Apple-styled **Gradio** UI lets you type an idea, pick how many papers to return, and flip through them one fully-rendered card at a time with the ‹ › arrows, ordered **most-relevant first**. Launched with `share=True` for a public URL.

## Files

| File | Purpose |
| --- | --- |
| `config.yaml` | All paths and parameters (models, data, devices, `recall_k`, `rerank_k`, ...) |
| `common.py` | Config loading + Markdown paper parsing |
| `embedder.py` | `Qwen3Embedder` (last-token pooling, instruct prompt) |
| `reranker.py` | `Qwen3Reranker` (yes/no relevance cross-encoder) |
| `build_index.py` | Embed every paper → `index/embeddings.npy` + `index/metadata.json` |
| `search.py` | `SearchEngine`: recall + rerank |
| `app.py` | Gradio UI |

## Expected data layout

```
data_dir/
  Apple/   Apple_arxiv_..._Title.md
  Google/  ...md
  ...
```
Each `.md` starts with `# Title` and an `**arXiv:** [url](url)` line (the format produced by the arXiv download tool). `README.md` files are skipped.

## Setup (remote 8×A100)

```bash
cd paper_search_engine
pip install -r requirements.txt
```

Edit `config.yaml` so `data_dir`, `embedding_model_path`, and `reranker_model_path` point at the right places. The two 8B models default to **separate GPUs** (`cuda:0` / `cuda:1`) so the web app can hold both at once.

## 1) Build the index (run once)

```bash
python build_index.py
# or override paths:
python build_index.py --data-dir /yufan/RecSysPaper --index-dir ./index
```

This embeds all ~2k papers and writes `index/embeddings.npy` and `index/metadata.json`.

## 2) Launch the search UI

```bash
python app.py
```

Gradio prints a local URL **and** a public `https://*.gradio.live` share link (because `share: true` in `config.yaml`). Open it, type an idea, and browse the 15 reranked papers.

### Quick CLI test (no UI)

```bash
python search.py "generative retrieval for sequential recommendation with LLMs"
```

## Tuning

All in `config.yaml`:
- `rerank_k` — default top-K returned (the UI slider starts here).
- `recall_cap` — hard upper bound on the recall pool (recall = `min(2 × top-K, recall_cap)`).
- `embedding_batch_size` — raise it for faster indexing on A100.
- `use_flash_attention` — set `true` after `pip install flash-attn` for speed/memory.
- `dtype` — `bfloat16` recommended on A100.
