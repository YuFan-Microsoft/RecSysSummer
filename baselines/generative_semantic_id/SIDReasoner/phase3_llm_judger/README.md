# Phase-3 Qwen3-32B LLM Judge

This directory contains a standalone target-aware judge service for Phase-3 RL.
It starts an internal vLLM OpenAI-compatible server with the local Qwen3-32B
checkpoint across eight GPUs, exposes a Gradio UI for manual evaluation, and
keeps a stable domain API for later RL integration.

The RL trainer does not call the vLLM API directly. It sends one prompt group to
`POST /v1/judge`: chronological history titles, the held-out target title, and
up to 16 rollout candidates containing reasoning plus a predicted-item title.
Qwen returns a compact relative partition (`high`, `medium`, `low`); the gateway
maps it to normalized rewards `1.0`, `0.5`, and `0.0`.

## Start the service

From the `SIDReasoner` root:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
  bash phase3_llm_judger/start_server.sh
```

Install the small gateway/UI dependency set if the image does not include it:

```bash
pip install -r phase3_llm_judger/requirements.txt
```

Defaults:

| Setting | Value |
| --- | --- |
| Model | `/yufan/open_source_models/Qwen3_LLM/instruct_model/Qwen3-32B/` |
| External endpoint | `0.0.0.0:8090` |
| Internal vLLM endpoint | `127.0.0.1:8091` |
| Tensor parallel size | 8 |
| Dtype | BF16 |
| Max model length | 32,768 |
| Max candidates per group | 16 |

The process waits for `/health` from vLLM before accepting judge traffic. Model
weights may require `HF_TOKEN`. The eight judge GPUs should be separate from the
policy-training GPUs; the 32B service otherwise competes with rollout and FSDP.

Open `http://judge-host:8090/gradio` to edit a complete request and inspect the
per-candidate scores. The Gradio function is also published with API name
`judge_group`; Gradio's generated API documentation is available from the UI.
The stable `POST /v1/judge` endpoint below remains the recommended RL interface.
The temporary service has no authentication. Bind or expose port `8090` only on
a trusted network.

Sharing is enabled by default. After startup the log prints URLs like:

```text
Gradio public UI: https://<random>.gradio.live/gradio
Public judge API: https://<random>.gradio.live/v1/judge
```

The public tunnel exposes both Gradio and the unauthenticated REST API. Disable
it with `--no-share` when only local or private-network access is needed:

```bash
bash phase3_llm_judger/start_server.sh --no-share
```

To use an already-running OpenAI-compatible vLLM backend instead of spawning one:

```bash
python3 -m phase3_llm_judger.server \
  --external-backend-url http://judge-host:8091 \
  --served-model-name qwen3-32b-phase3-judge
```

## API

Health:

```bash
curl http://localhost:8090/healthz
```

Single group:

```text
POST /v1/judge
Content-Type: application/json
```

Request shape:

```json
{
  "request_id": "step-100-prompt-7",
  "history": [
    {
      "sid": "<a_1><b_2><c_3>",
      "title": "History item"
    }
  ],
  "target": {
    "sid": "<a_4><b_5><c_6>",
    "title": "Held-out target"
  },
  "candidates": [
    {
      "candidate_id": "0",
      "reasoning": "<history_summary>...</future_interests>",
      "predicted_item": {
        "sid": "<a_7><b_8><c_9>",
        "title": "Predicted item"
      },
      "hard_valid": true
    }
  ]
}
```

The model emits only this compact structured output:

```json
{
  "high": ["0", "3"],
  "medium": ["1"],
  "low": ["2", "4"]
}
```

All tiers may be empty. If no candidate is useful, all IDs belong in `low`, so
the group has no artificial best-of-garbage advantage. The gateway restores
request order and returns each candidate as:

```json
{
  "candidate_id": "0",
  "tier": "high",
  "normalized_reward": 1.0
}
```

`POST /v1/judge/batch` accepts `{"requests": [...]}` with up to 64 groups and
lets vLLM batch requests concurrently. Candidate order is deterministically
shuffled from `request_id` before prompting to reduce position bias, then restored
to request order in the response. Ties are explicitly allowed.

## Python client

```python
from phase3_llm_judger.client import JudgeClient

client = JudgeClient("http://judge-host:8090")
response = client.judge(payload)
rewards = {
    row["candidate_id"]: row["normalized_reward"]
    for row in response["judgments"]
}
```

`AsyncJudgeClient` exposes the same `judge` and `judge_batch` methods for trainer
integration and reuses HTTP connections. Use it as an async context manager:

```python
async with AsyncJudgeClient(url) as client:
  response = await client.judge(payload)
```

## Intended RL integration

The first integration should call this endpoint only after bounded retry still
leaves an all-wrong 16-trajectory group. Exact-hit groups keep the existing SID
advantage. Final all-wrong groups use the judge as a weak dense fallback:

```text
A = 0.2 * A_judge + 0.1 * A_process
```

The current deterministic hard-validity gate remains authoritative. Candidates
with `hard_valid=false` are forced to reward `0` by the gateway even if the model
assigns a larger utility. The endpoint is target-aware by design; the policy
rollout itself must remain target-blind.

## Checkpoint-derived test data

Generate representative title-only requests from the checkpoint result JSONL:

```bash
python3 phase3_llm_judger/prepare_test_data.py \
  --input /Users/yufan/Desktop/Checkpoint_Result/constrained_sampling_with_format_reward
```

The default records contain five all-wrong examples and one target-hit control.
Each beam item becomes a simulated rollout candidate and shares the record's
single reasoning trace. This is useful for testing title-level target relation
and reasoning-prediction coherence, but it does not simulate independently
sampled reasoning traces.

## Validate without GPUs

```bash
python3 -m unittest phase3_llm_judger.test_contract
python3 -m py_compile phase3_llm_judger/*.py
bash -n phase3_llm_judger/start_server.sh
```