#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

python3 -m phase3_interest_retriever.server \
    --index-dir "${INTEREST_INDEX_DIR:-phase3_interest_retriever/indexes/Video_Games}" \
    --host "${INTEREST_RETRIEVER_HOST:-0.0.0.0}" \
    --port "${INTEREST_RETRIEVER_PORT:-8092}" \
    --device "${INTEREST_RETRIEVER_DEVICE:-cuda:0}" \
    --dtype "${INTEREST_RETRIEVER_DTYPE:-bfloat16}" \
    --query-batch-size "${INTEREST_RETRIEVER_BATCH_SIZE:-32}" \
    --gradio-path "${INTEREST_RETRIEVER_GRADIO_PATH:-/gradio}" \
    "$@"