# CLAUDE.md — Phase-3 Interest Retriever

Instructions for an AI agent operating the retrieval-grounded interest reward
experiment. Run every command from the `SIDReasoner/` repository root. Do not
connect this service to Phase-3 RL until the offline recall evaluation succeeds.

## 1. What this service does

For each rollout, the model generates one `<future_interests>` block containing
multiple exploit/explore interest lines. The trainer extracts text after the
first `=>`; the independent endpoint embeds that text and returns target ranks:

```text
interest_reward = 1 if any interest retrieves the target SID in Top-K else 0
```

The endpoint itself assigns no RL credit; it returns only target ranks. The
trainer aggregates all interests in one rollout into a block reward. Under
signed GRPO, a non-covering block receives negative relative advantage when its
16-rollout group also contains covering blocks.

## 2. Fixed experiment inputs

- Embedding model:
  `/yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B`
- Catalog dataset:
  `yufan/recsys-genrec-dataset-refresh-gpt5.4-candidateV2`
- Dataset revision:
  `a5eb07115444b128ab7add812e4cee87517a5c41`
- Config/split: `Video_Games_catalog/train`
- Checkpoint analysis file:
  `yufan/rec_rl_checkpoints/results_analysis/yufan_diverisity_process.jsonl`
- Full index directory: `phase3_interest_retriever/indexes/Video_Games`
- Default endpoint: `http://localhost:8092`

The pinned catalog contains 3,858 item rows and 3,827 unique SIDs. Keep all item
rows. SID collisions are expected; target rank is the best rank among catalog
rows sharing the target SID.

## 3. Golden rules

1. Use the same model for document and query embeddings. The builder records the
   model path and query instruction in `manifest.json`; the server must load that
   manifest rather than silently selecting another model.
2. Query only the text after the first `=>`. Use the exact Video Games
  instruction recorded in the manifest and no space after `Query:`.
3. Build documents in fixed `Title`, `Brand`, `Details` order from `title`,
  `brand`, and `detailed_description`. Omit empty fields. Never include raw
  `description`, SID, item ID, `sid_interleaved_narrative`, a `Document:` prefix,
  or any instruction.
4. Never write a limited smoke index into the full index directory. Always use
   `indexes/Video_Games_smoke` for `--limit` runs.
5. Treat malformed or truncated reasoning as a miss in the primary recall. Do
   not recover partial interest blocks. `conditional_recall` may be used only as
   a diagnostic for successfully parsed and retrieved records.
6. Do not commit generated `indexes/` contents or detailed evaluation results.
7. Do not start RL training merely because the endpoint is healthy. First inspect
   offline recall, request failures, and representative retrievals.

## 4. Execution order

### Step 1 — Check the machine and local model

The index builder requires PyTorch, Transformers, and exactly eight available
CUDA GPUs. Verify the local checkpoint and GPU count before installing or
launching anything:

```bash
test -d /yufan/open_source_models/Embedding_Model/Qwen3-Embedding-0.6B
python3 -c "import torch, transformers; print(torch.__version__, transformers.__version__, torch.cuda.device_count()); assert torch.cuda.device_count() >= 8"
```

Stop if the model directory is missing or fewer than eight GPUs are available.
Do not fall back to a different model without recording the changed model in the
experiment name.

### Step 2 — Install dependencies and run CPU-only tests

```bash
pip install -r phase3_interest_retriever/requirements.txt
python3 -m unittest discover -s phase3_interest_retriever -p 'test_*.py'
python3 -m py_compile phase3_interest_retriever/*.py
bash -n phase3_interest_retriever/start_server.sh
```

All tests must pass before a GPU index build.

### Step 3 — Build a separate smoke index

Use a small catalog slice to validate model loading, dataset access, embedding
shape, and manifest generation without touching the full index:

```bash
python3 -m phase3_interest_retriever.build_index \
  --gpus 0,1,2,3,4,5,6,7 \
  --limit 100 \
  --output-dir phase3_interest_retriever/indexes/Video_Games_smoke
```

The builder always requires exactly eight distinct GPU IDs, including for the
smoke run. It spawns one isolated process per card and merges shards in catalog
order. Each worker sorts documents by token length and caps padded tokens at
32,768 per actual batch. The validated defaults are FP16, document max length
1,024, and batch size 32 per GPU. Do not launch multiple builders on the same
cards.

Inspect the smoke manifest:

```bash
python3 -c "import json; print(json.load(open('phase3_interest_retriever/indexes/Video_Games_smoke/manifest.json')))"
```

Expected properties include `item_count=100`, the local embedding model path,
`normalized=true`, `search=exact_cosine`, and
`build_batch_size_per_gpu=32`, `document_max_length=1024`,
`query_max_length=512`, `dtype=float16`, and
`max_batch_tokens_per_gpu=32768`.

### Step 4 — Start and probe the smoke endpoint

Run the service in a dedicated terminal:

```bash
INTEREST_INDEX_DIR=phase3_interest_retriever/indexes/Video_Games_smoke \
  bash phase3_interest_retriever/start_server.sh
```

From another terminal:

```bash
curl --fail http://localhost:8092/healthz
```

The health response must report 100 items and the expected model. Stop the smoke
service before building or serving the full index.

### Step 5 — Build the complete Video Games index

```bash
python3 -m phase3_interest_retriever.build_index \
  --gpus 0,1,2,3,4,5,6,7
```

Validate the resulting manifest before starting the endpoint:

```bash
python3 -c "import json; m=json.load(open('phase3_interest_retriever/indexes/Video_Games/manifest.json')); assert m['item_count']==3858; assert m['unique_sid_count']==3827; assert m['build_world_size']==8; assert len(m['build_gpu_ids'])==8; assert m['build_batch_size_per_gpu']==32; assert m['document_max_length']==1024; assert m['query_max_length']==512; assert m['dtype']=='float16'; assert m['attention_backend']=='transformers_default'; print(m)"
```

Do not reuse a smoke manifest or embeddings file for the full evaluation.

### Step 6 — Start the full endpoint

The endpoint is deliberately single-GPU even though index construction uses
eight GPUs. `start_server.sh` isolates one physical card with
`CUDA_VISIBLE_DEVICES=${INTEREST_RETRIEVER_GPU:-0}` and loads the query encoder
on the worker-visible `cuda:0`. Do not start eight endpoint replicas unless a
separate serving-scale experiment explicitly requires them.

For an interactive run:

```bash
bash phase3_interest_retriever/start_server.sh
```

To select a different physical card:

```bash
INTEREST_RETRIEVER_GPU=7 bash phase3_interest_retriever/start_server.sh
```

For a long-lived remote run, keep the process alive across SSH disconnects:

```bash
mkdir -p logs
nohup bash phase3_interest_retriever/start_server.sh \
  > logs/phase3_interest_retriever.log 2>&1 &
```

Then verify:

```bash
curl --fail http://localhost:8092/healthz
```

The health response must report 3,858 items. If the endpoint reports a different
model, item count, or embedding dimension, stop and rebuild rather than evaluating
an inconsistent index.

### Step 7 — Run a 100-record recall smoke test

```bash
python3 -m phase3_interest_retriever.evaluate_checkpoint_interests \
  --limit 100 \
  --output phase3_interest_retriever/results/yufan_diversity_process_smoke.jsonl
```

Before proceeding, require:

- `request_failures == 0`;
- the endpoint remains healthy;
- retrieved titles are semantically related to several sampled interests;
- target ranks and `any_hit` agree in the detailed JSONL.

Low recall alone is not a service failure. HTTP errors, missing targets, model
mismatch, or incoherent nearest neighbors are failures that must be investigated.

### Step 8 — Run the full 6,142-record evaluation

```bash
python3 -m phase3_interest_retriever.evaluate_checkpoint_interests \
  --output phase3_interest_retriever/results/yufan_diversity_process_retrieval.jsonl \
  | tee phase3_interest_retriever/results/yufan_diversity_process_summary.json
```

The source currently contains 6,142 records. A prior parser-only check found
6,044 strict interest blocks and 98 truncated outputs. Recheck these counts in
the final summary; unexpected changes indicate a different source revision or a
parser regression.

## 5. Reading the evaluation

Use `all_recall.recall_at_K` as the primary interest-block metric. Its denominator
is all 6,142 records, so malformed reasoning and request failures count as misses.

- `all_recall`: any exploit or explore interest retrieves the target.
- `exploit_recall`: only exploit interests are eligible to hit.
- `explore_recall`: only explore interests are eligible to hit.
- `*_conditional_recall`: diagnostic recall among successfully parsed/retrieved
  records; never present this as the main result.
- `prediction_beam_recall_at_10`: original SID prediction-beam recall from the
  checkpoint file; this is a reference metric, not the interest reward.

Inspect more than the aggregate number. Review successful and failed examples,
generic-query hits, duplicate-SID cases, and whether complete-line SID citations
dominate retrieval over the natural-language interest.

## 6. Final step — establish the Gradio endpoint

After the full offline recall evaluation is complete and inspected, launch the
full service as the final deliverable:

```bash
mkdir -p logs
nohup bash phase3_interest_retriever/start_server.sh \
  > logs/phase3_interest_retriever.log 2>&1 &
```

Verify both surfaces:

```bash
curl --fail http://localhost:8092/healthz
curl --fail http://localhost:8092/gradio/
```

Sharing is enabled by default. Wait for startup logs containing all three URLs:

```text
Public Gradio UI: https://<share>.gradio.live/gradio
Public rank API: https://<share>.gradio.live/v1/rank
Public batch rank API: https://<share>.gradio.live/v1/rank/batch
```

Use `--no-share` only when public exposure is intentionally disabled. Use the
private host URL for high-volume RL calls even while the public UI remains
available.

Open `http://<server-host>:8092/gradio` for manual inspection. The named Gradio
API endpoint is `rank_interest`.

### Gradio input contract

1. `target_sid` — one catalog SID in `<a_N><b_N><c_N>` form.
2. `interest_text` — exactly one pure-text interest after the first `=>`.

### Gradio output contract

One integer `rank`: 1–100 when the target SID appears in Top-100, otherwise `-1`.
The Gradio endpoint returns no item details, similarity scores, or reward.

Programmatic Gradio call:

```python
from gradio_client import Client

client = Client("http://localhost:8092/gradio")
rank = client.predict(
    target_sid="<a_1><b_2><c_3>",
    interest_text="survival crafting games",
    api_name="/rank_interest",
)
```

The Gradio UI/API is for manual testing and demonstration. RL workers call the
compact `/v1/rank/batch` REST contract rather than depending on Gradio routes or
returning complete Top-100 items.

The public tunnel has no authentication. Share its URL only with trusted users
or place the service behind an authenticated reverse proxy.

## 7. RL integration

The constrained-sampling trainer extracts pure text after `=>`, sends one
`interest + target_sid` pair per interest to `/v1/rank/batch`, takes the best
positive rank in each rollout, and thresholds it with configurable `reward_top_k`.
Interest reward is normalized separately with signed GRPO and applied only to
the generated `<future_interests>` token mask. SID and process advantages remain
separate.

The integration tests must prove that:

- one hitting interest gives block reward 1;
- a mixed group gives positive advantage to covering blocks and negative
  advantage to non-covering blocks;
- all misses give block reward 0;
- malformed format gates retrieval reward to 0;
- endpoint failures do not silently become positive rewards.

On the first GPU pilot step, require
`interest_token_mask_nonempty_rate == interest_format_valid_rate` (up to any
known tokenizer edge cases). A lower mask rate means tag tokenization did not
match the generated IDs and training must stop for investigation.

## 8. Common failures

- **Model path missing:** mount or copy the local checkpoint; use the Hub ID only
  as an explicit, recorded override.
- **CUDA out of memory:** reduce `--batch-size` for index building or
  `INTEREST_RETRIEVER_BATCH_SIZE` for serving.
- **A build worker fails:** inspect the worker traceback, verify all eight GPU
  IDs are available, and rerun the complete build. The builder does not publish
  a merged index unless every shard succeeds.
- **Target SID absent:** verify the checkpoint and index use the same Video Games
  catalog revision. The checked checkpoint currently has zero missing targets.
- **98 parse failures:** these are expected truncated generations in the current
  source and should remain misses. A substantially different count needs review.
- **Wrong item count:** delete/rebuild the selected index directory; do not mix
  smoke and full artifacts.
- **Port 8092 occupied:** set `INTEREST_RETRIEVER_PORT` consistently for the
  server and pass the matching `--endpoint` URL to the evaluator.