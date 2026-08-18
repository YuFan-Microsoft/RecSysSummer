# Phase-3 Interest Retriever

This directory contains the standalone retrieval endpoint for the constrained-
sampling interest-reward experiment. It embeds each generated interest with a
local `Qwen3-Embedding-0.6B` checkpoint, retrieves catalog products by exact cosine
similarity, and returns a binary multiple-instance reward:

```text
reward = 1 if any interest retrieves the target SID in its Top-K, else 0
```

The endpoint reports ranks only; it does not assign positive or negative RL
credit. The trainer gives the whole interest block a positive reward when any
interest covers the target and zero otherwise. Signed GRPO then increases
covering blocks and decreases non-covering blocks within mixed rollout groups.

## Data and index

The builder defaults to:

- Dataset: `yufan/recsys-genrec-dataset-final`
- Revision: `bf00c35c019262437b8694b51209c419567044c0`
- Config/split: `Video_Games_catalog/train`
- Catalog size at that revision: 3,858 items
- Index text: `title`, optional `brand`, and `retrieval_summary`, in that order
- Embedding model: `/yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B`
- Document max length / batch per GPU: 1,024 / 32
- Query max length / batch: 512 / 128
- Dtype: FP16
- Attention: Transformers default (no FlashAttention 2)
- Padding / pooling / normalization: left / last token / L2

Raw `description`, `detailed_description`, and `sid_interleaved_narrative` are
excluded from the embedding text. The pinned `retrieval_summary` is the
interest-aligned product representation generated for this index.
Pass `--model Qwen/Qwen3-Embedding-0.6B` to the builder when the local
checkpoint is unavailable and a Hub download is preferred.

Install dependencies and build the index from the `SIDReasoner` root:

```bash
pip install -r phase3_interest_retriever/requirements.txt
python3 -m phase3_interest_retriever.build_index
```

Index construction uses exactly eight GPUs concurrently by default:
`--gpus 0,1,2,3,4,5,6,7`. The catalog is split into eight contiguous shards;
each spawned worker sees one physical GPU through `CUDA_VISIBLE_DEVICES` and
loads its own Qwen3 embedding model. The parent process merges all eight output
matrices in catalog order only after every worker succeeds. To select another
set of cards, pass exactly eight distinct IDs, for example
`--gpus 2,3,4,5,6,7,8,9`.

Each GPU has `--batch-size 32`, document `--max-length 1024`, and a 32,768-token
padding budget. Workers sort their shard by token length, encode, then restore
catalog order before shard merge. Documents are exactly:

```text
Title: {title}
Brand: {brand}
Summary: {retrieval_summary}
```

The `Brand` line is omitted when `brand` is empty. `Title` and `Summary` are
required. Document text contains no raw `description`, `detailed_description`,
SID, item ID, `sid_interleaved_narrative`, `Document:` prefix, or instruction.

The output directory contains `embeddings.npy`, `metadata.json`, and a
`manifest.json` that pins the data/model provenance and query instruction.
The manifest also records `build_world_size=8`, `build_gpu_ids`,
`build_batch_size_per_gpu=32`, `document_max_length=1024`,
`query_max_length=512`, FP16, default attention, and the token budget.
Use `--limit 100` for a quick build smoke test.

The catalog has 3,858 item rows and 3,827 unique SIDs at the pinned revision.
The index keeps every item row. When several items share a SID, target recall is
the best (lowest) rank among those rows because the Phase-3 ground truth exposes
the SID rather than a unique catalog row.

## Start the endpoint

```bash
bash phase3_interest_retriever/start_server.sh
```

Defaults are `0.0.0.0:8092`, GPU `cuda:0`, and the index directory
`phase3_interest_retriever/indexes/Video_Games`. Override these with
`INTEREST_RETRIEVER_PORT`, `INTEREST_RETRIEVER_GPU`, or `INTEREST_INDEX_DIR`.
Unlike the eight-GPU index builder, the online endpoint uses exactly one GPU.
`start_server.sh` defaults to physical GPU 0 by setting `CUDA_VISIBLE_DEVICES=0`
and loads the model on its isolated `cuda:0`. To use physical GPU 7 instead:

```bash
INTEREST_RETRIEVER_GPU=7 bash phase3_interest_retriever/start_server.sh
```

Public sharing is enabled by default. After the local UI is ready, the launcher
creates a `gradio.live` tunnel for the entire FastAPI port and prints:

```text
Public Gradio UI: https://<share>.gradio.live/gradio
Public rank API: https://<share>.gradio.live/v1/rank
Public batch rank API: https://<share>.gradio.live/v1/rank/batch
```

Disable public exposure with:

```bash
bash phase3_interest_retriever/start_server.sh --no-share
```

The public tunnel has no authentication. The current Phase-3 default is hardcoded
to `https://bf5e9cbea14925c5fa.gradio.live/v1/rank/batch`; override it with
`INTEREST_REWARD_ENDPOINT` only when intentionally switching deployments.

The same process mounts a Gradio UI at `http://<host>:8092/gradio`. Its named
Gradio API endpoint is `rank_interest`. Disable the UI with
`--disable-gradio --no-share` when only the private REST API is needed.

### Gradio input and output

Inputs:

| Name | Type | Contract |
| --- | --- | --- |
| `target_sid` | string | One catalog SID matching `<a_N><b_N><c_N>` |
| `interest_text` | string | Exactly one pure-text interest, normally the text after `=>` |

Outputs:

| Name | Type | Contents |
| --- | --- | --- |
| `rank` | integer | 1-based Top-100 target rank, or `-1` when not retrieved |

No item titles, scores, Top-K details, JSON result object, or reward are returned.
Trainer integration calls compact `POST /v1/rank/batch` for real batching.

Programmatic Gradio call:

```python
from gradio_client import Client

client = Client("https://<share>.gradio.live/")
rank = client.predict(
  target_sid="<a_1><b_2><c_3>",
  interest_text="cooperative survival crafting games",
  api_name="/rank_interest",
)
```

Health check:

```bash
curl http://localhost:8092/healthz
```

### Training rank API

The rank service always searches Top-100. A 1-based rank means the target SID
was retrieved; `-1` means it was absent from Top-100. A target SID absent from
the catalog is an HTTP error, not a miss.

```text
POST /v1/rank
{"interest": "survival crafting games", "target_sid": "<a_1><b_2><c_3>"}
-> {"rank": 37}
```

The true batch endpoint deduplicates equal interest strings, embeds all unique
queries in one service call, searches Top-100 once, and preserves request order:

```text
POST /v1/rank/batch
{"requests": [{"interest": "...", "target_sid": "<a_1><b_2><c_3>"}]}
-> {"ranks": [37]}
```

The trainer extracts only the text after the first `=>`. Query strings are:

```text
Instruct: Retrieve relevant Video Games products.
Query: cooperative survival crafting games
```

## Python client

```python
from phase3_interest_retriever.client import InterestRetrieverClient

client = InterestRetrieverClient("https://bf5e9cbea14925c5fa.gradio.live/v1/rank/batch")
ranks = client.rank_batch([
  {"interest": "survival crafting games", "target_sid": "<a_1><b_2><c_3>"}
])
```

An `AsyncInterestRetrieverClient` with the same methods is available for the RL
integration and reuses its HTTP session.

## Evaluate generated interests

With the endpoint running, evaluate the generated `<future_interests>` blocks
from `yufan/rec_rl_checkpoints`:

```bash
python3 -m phase3_interest_retriever.evaluate_checkpoint_interests \
  --output phase3_interest_retriever/results/yufan_diversity_process_retrieval.jsonl
```

The evaluator downloads and caches
`results_analysis/yufan_diverisity_process.jsonl`, extracts the complete original
interest lines, and reports any-interest Recall@1/5/10/20/50/100. It also reports
exploit-only and explore-only recall and the checkpoint file's original
`prediction_beam_10` recall for reference. The detailed output records target
ranks and retrieved items for each interest. Use `--limit 100` for a smoke test.
The primary recall uses every source record as its denominator, so malformed or
truncated reasoning is a miss. A separate `conditional_recall` reports retrieval
quality only among records that parsed and reached the endpoint successfully.

## Validate without a GPU

```bash
python3 -m unittest discover -s phase3_interest_retriever -p 'test_*.py'
python3 -m py_compile phase3_interest_retriever/*.py
bash -n phase3_interest_retriever/start_server.sh
```