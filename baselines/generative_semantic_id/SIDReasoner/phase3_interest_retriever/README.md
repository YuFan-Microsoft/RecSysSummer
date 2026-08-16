# Phase-3 Interest Retriever

This directory contains the standalone retrieval endpoint for the constrained-
sampling interest-reward experiment. It embeds each generated interest with a
local `Qwen3-Embedding-0.6B` checkpoint, retrieves catalog products by exact cosine
similarity, and returns a binary multiple-instance reward:

```text
reward = 1 if any interest retrieves the target SID in its Top-K, else 0
```

A missed interest is not penalized individually. This leaves room for valid
exploration interests when the interaction log exposes only one target item.
The service embeds interest strings exactly as supplied by the caller.

## Data and index

The builder defaults to:

- Dataset: `yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV2`
- Revision: `a5eb07115444b128ab7add812e4cee87517a5c41`
- Config/split: `Video_Games_catalog/train`
- Catalog size at that revision: 3,858 items
- Index text: `title`, `brand`, `description`, and `detailed_description`
- Embedding model: `/yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B`

`sid_interleaved_narrative` is intentionally excluded from the first index so
the reward measures retrieval from product metadata rather than generated
training narratives.
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

The output directory contains `embeddings.npy`, `metadata.json`, and a
`manifest.json` that pins the data/model provenance and query instruction.
The manifest also records `build_world_size=8` and `build_gpu_ids`.
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
`INTEREST_RETRIEVER_PORT`, `INTEREST_RETRIEVER_DEVICE`, or
`INTEREST_INDEX_DIR`.

The same process mounts a Gradio UI at `http://<host>:8092/gradio`. Its named
Gradio API endpoint is `retrieve_interests`. Disable the UI with
`--disable-gradio` when only the stable REST API is needed.

### Gradio input and output

Inputs:

| Name | Type | Contract |
| --- | --- | --- |
| `target_sid` | string | One catalog SID matching `<a_N><b_N><c_N>` |
| `interests_text` | string | 1–8 non-empty lines; each complete line is embedded unchanged |
| `top_k` | integer | Retrieval cutoff from 1 to 100 in the UI |

Outputs:

| Name | Type | Contents |
| --- | --- | --- |
| `response_json` | object | `any_hit`, binary `reward`, latency, and complete per-interest results |
| `result_table` | table | One row per retrieved item with interest index, hit/rank, item ID, SID, title, and cosine score |

The Gradio endpoint is for manual inspection. Trainer integration should call
the stable `POST /v1/retrieve` or `POST /v1/retrieve/batch` JSON endpoints.

Programmatic Gradio clients call `api_name="/retrieve_interests"` and receive a
two-element output: the complete response object followed by the flattened
result table. The three positional inputs are `target_sid`, `interests_text`,
and `top_k`, in that order.

Health check:

```bash
curl http://localhost:8092/healthz
```

Retrieve and compute the block reward:

```bash
curl -X POST http://localhost:8092/v1/retrieve \
  -H 'Content-Type: application/json' \
  -d '{
    "request_id": "rollout-7",
    "target_sid": "<a_1><b_2><c_3>",
    "interests": [
      "- [exploit] <a_7><b_8><c_9> => survival crafting games",
      "- [explore] <a_4><b_5><c_6> => console accessories"
    ],
    "top_k": 20
  }'
```

The response includes the Top-K items and target rank for every interest, plus
the block-level fields `any_hit` and `reward`. `POST /v1/retrieve/batch` accepts
`{"requests": [...]}` for trainer-side batching.

## Python client

```python
from phase3_interest_retriever.client import InterestRetrieverClient

client = InterestRetrieverClient("http://retriever-host:8092")
response = client.retrieve(payload)
interest_reward = response["reward"]
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