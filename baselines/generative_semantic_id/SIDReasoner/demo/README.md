# SIDReasoner Video Games Demo

This demo calls an OpenAI-compatible SIDReasoner endpoint and presents the full
Video Games recommendation flow:

- user history entered as SIDs or catalog titles;
- every history SID resolved to its catalog title and brand;
- raw reasoning parsed into `history_summary` and `future_interests`;
- catalog-constrained beam Top-10 displayed in exactly two columns: SID and title.

The current catalog has 3,858 rows and 3,827 unique SIDs. When multiple catalog
rows share one SID, the UI preserves and displays every matching item instead of
silently choosing one.

The defaults are pinned in `app.py`:

- checkpoint repo: `yufan/recsys-genrec-checkpoints-final` (dataset repo);
- checkpoint subdirectory: `Video_Games/stage3_interest_grounding_candidate1`;
- checkpoint revision: `e50227d879aebe80a6054750536a3d505a8bea0d`;
- catalog: `yufan/recsys-genrec-dataset-final`, config `Video_Games_catalog`.

The checkpoint is stored under a dataset-repo subdirectory, so it cannot be
passed directly to vLLM as a model ID. The included downloader returns the local
directory that contains `config.json`, `model.safetensors`, and the SID tokenizer.

## Run on the A100 machine

Use a CUDA environment that already has the SIDReasoner vLLM stack, then install
the small demo dependencies from the `SIDReasoner` directory:

```bash
pip install -r demo/requirements.txt
```

Download the hardcoded checkpoint once:

```bash
CHECKPOINT=$(python demo/download_checkpoint.py)
echo "$CHECKPOINT"
```

Start the model endpoint in terminal 1. vLLM 0.10.2 is the currently verified
SIDReasoner serving version:

```bash
CHECKPOINT=$(python demo/download_checkpoint.py)
OMP_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
OPENBLAS_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 \
vllm serve "$CHECKPOINT" \
  --served-model-name sidreasoner \
  --host 127.0.0.1 \
  --port 8000 \
  --dtype bfloat16 \
  --seed 42 \
  --max-model-len 2048 \
  --logprobs-mode processed_logprobs \
  --gpu-memory-utilization 0.90
```

Start Gradio in terminal 2:

```bash
python demo/app.py \
  --endpoint http://127.0.0.1:8000/v1 \
  --model sidreasoner \
  --host 0.0.0.0 \
  --port 7860 \
  --share
```

Gradio prints a temporary public `https://....gradio.live` URL. Public sharing is
enabled by default; pass `--no-share` for local-only serving. The model endpoint
stays bound to localhost and is not exposed directly.

For an authenticated endpoint, keep the key out of the shared UI:

```bash
export SIDR_DEMO_API_KEY='...'
python demo/app.py --endpoint https://MODEL_HOST/v1 --model sidreasoner --share
```

## Input

Build history in chronological order, oldest to newest, with searchable catalog
selectors. On every page load, the interface samples one real row from
`Video_Games_seqrec/test`:

- the first two positions are required;
- use **🎲 Random history** to sample another test user at any time;
- histories of length 2–5 are preserved exactly;
- longer histories use their most recent five clicks in original order;
- the row's held-out target `item_sid` is never added to the input history;
- search each selector by either title text or SID.

To keep the browser lightweight, choices are grouped by the first SID token
`<a_n>`. Each first-level group contributes the 5 most popular full SIDs, ranked
by interaction count in `Video_Games_seqrec/train`. Validation and test rows are
not used for popularity, so the manual selector does not leak held-out behavior.
Sampled test-history SIDs outside this Top-5 pool are added only to the position
where they occur, keeping the real sequence intact without expanding every dropdown.

Every dropdown value is still a real SID from `Video_Games_catalog`; arbitrary
input is not accepted. SID collisions are labeled with their catalog match count.

## Inference behavior

The system and user messages match `ReasoningEvalDataset`. The parser supports
both raw Qwen `<think>...</think>` responses and servers that return
`reasoning_content` separately. It recognizes the current Phase-3 format:

```text
<history_summary>
- HISTORY_SID[, ...] => factual summary
</history_summary>
<future_interests>
- [exploit|explore] HISTORY_SID[, ...] => predicted interest
</future_interests>
</think>

<a_N><b_N><c_N>
```

After generating one reasoning trace, the demo continues through the endpoint's
OpenAI completions API for a three-level catalog-constrained beam search. It uses
the checkpoint tokenizer locally, but does not load model weights into the Gradio
process. Start vLLM with `--logprobs-mode processed_logprobs` so Top-10 candidates
are ranked after the valid-SID token constraint. Final prediction contains only
the ten SID/title rows.

## Test

```bash
cd demo
python -m unittest -v test_app.py
```