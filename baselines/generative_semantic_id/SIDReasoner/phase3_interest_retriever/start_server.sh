#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export CUDA_VISIBLE_DEVICES="${INTEREST_RETRIEVER_GPU:-0}"

DOMAIN="${INTEREST_RETRIEVER_DOMAIN:-Video_Games}"
SERVER_ARGS=()
while (($#)); do
    case "$1" in
        --domain)
            if (($# < 2)); then
                echo "--domain requires a value" >&2
                exit 2
            fi
            DOMAIN="$2"
            shift 2
            ;;
        --domain=*)
            DOMAIN="${1#*=}"
            shift
            ;;
        *)
            SERVER_ARGS+=("$1")
            shift
            ;;
    esac
done

case "${DOMAIN}" in
    Video_Games|Office_Products|Industrial_and_Scientific) ;;
    *)
        echo "Unsupported domain: ${DOMAIN}" >&2
        exit 2
        ;;
esac

python3 -m phase3_interest_retriever.server \
    --domain "${DOMAIN}" \
    --index-dir "${INTEREST_INDEX_DIR:-phase3_interest_retriever/indexes/${DOMAIN}}" \
    --host "${INTEREST_RETRIEVER_HOST:-0.0.0.0}" \
    --port "${INTEREST_RETRIEVER_PORT:-8092}" \
    --device cuda:0 \
    --dtype "${INTEREST_RETRIEVER_DTYPE:-float16}" \
    --query-batch-size "${INTEREST_RETRIEVER_BATCH_SIZE:-128}" \
    --gradio-path "${INTEREST_RETRIEVER_GRADIO_PATH:-/gradio}" \
    --share \
    "${SERVER_ARGS[@]}"