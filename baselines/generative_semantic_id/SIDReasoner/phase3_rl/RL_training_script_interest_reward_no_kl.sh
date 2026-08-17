#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTEREST_REWARD_ENDPOINT="${INTEREST_REWARD_ENDPOINT:-https://bf5e9cbea14925c5fa.gradio.live/v1/rank/batch}"
INTEREST_REWARD_TOP_K="${INTEREST_REWARD_TOP_K:-50}"
INTEREST_REWARD_WEIGHT="${INTEREST_REWARD_WEIGHT:-0.1}"
INTEREST_REWARD_REQUEST_BATCH_SIZE="${INTEREST_REWARD_REQUEST_BATCH_SIZE:-2048}"
INTEREST_REWARD_MAX_ATTEMPTS="${INTEREST_REWARD_MAX_ATTEMPTS:-10}"

if ! [[ "${INTEREST_REWARD_TOP_K}" =~ ^[0-9]+$ ]] \
    || (( INTEREST_REWARD_TOP_K < 1 || INTEREST_REWARD_TOP_K > 100 )); then
    echo "INTEREST_REWARD_TOP_K must be an integer between 1 and 100" >&2
    exit 2
fi
if ! [[ "${INTEREST_REWARD_MAX_ATTEMPTS}" =~ ^[1-9][0-9]*$ ]]; then
    echo "INTEREST_REWARD_MAX_ATTEMPTS must be a positive integer" >&2
    exit 2
fi

INTEREST_REWARD_BASE_URL="${INTEREST_REWARD_ENDPOINT%/}"
INTEREST_REWARD_BASE_URL="${INTEREST_REWARD_BASE_URL%/v1/rank/batch}"
INTEREST_REWARD_BASE_URL="${INTEREST_REWARD_BASE_URL%/v1/rank}"
curl --fail --silent --show-error "${INTEREST_REWARD_BASE_URL}/healthz" >/dev/null

export EXPERIMENT_NAME="${EXPERIMENT_NAME:-Video_Games_stage3_rl_interest_retrieval_k${INTEREST_REWARD_TOP_K}_no_kl_Qwen3-1.7B}"

exec bash "${SCRIPT_DIR}/RL_training_script_no_kl.sh" \
    algorithm.interest_reward.enable=true \
    algorithm.interest_reward.endpoint="${INTEREST_REWARD_ENDPOINT}" \
    algorithm.interest_reward.reward_top_k="${INTEREST_REWARD_TOP_K}" \
    algorithm.interest_reward.weight="${INTEREST_REWARD_WEIGHT}" \
    algorithm.interest_reward.request_batch_size="${INTEREST_REWARD_REQUEST_BATCH_SIZE}" \
    algorithm.interest_reward.timeout=600 \
    algorithm.interest_reward.max_attempts="${INTEREST_REWARD_MAX_ATTEMPTS}" \
    algorithm.interest_reward.fail_open=true \
    "$@"
