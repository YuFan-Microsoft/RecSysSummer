#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

python3 -m phase3_llm_judger.server \
    --model "${JUDGE_MODEL:-/yufan/open_source_models/Qwen3_LLM/instruct_model/Qwen3-32B/}" \
    --served-model-name "${JUDGE_SERVED_MODEL_NAME:-qwen3-32b-phase3-judge}" \
    --host "${JUDGE_HOST:-0.0.0.0}" \
    --port "${JUDGE_PORT:-8090}" \
    --backend-host "${JUDGE_BACKEND_HOST:-127.0.0.1}" \
    --backend-port "${JUDGE_BACKEND_PORT:-8091}" \
    --tensor-parallel-size "${JUDGE_TP_SIZE:-8}" \
    --cuda-visible-devices "${CUDA_VISIBLE_DEVICES:-0,1,2,3,4,5,6,7}" \
    --gpu-memory-utilization "${JUDGE_GPU_MEMORY_UTILIZATION:-0.90}" \
    --max-model-len "${JUDGE_MAX_MODEL_LEN:-32768}" \
    --max-num-seqs "${JUDGE_MAX_NUM_SEQS:-32}" \
    --share \
    "$@"