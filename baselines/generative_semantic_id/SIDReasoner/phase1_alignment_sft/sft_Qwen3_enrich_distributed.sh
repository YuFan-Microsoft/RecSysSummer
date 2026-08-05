#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

BASE_MODEL="${BASE_MODEL:-Qwen/Qwen3-1.7B}"
# TEMP: point Phase-1 at the refreshed GPT-5.4 dataset (revert to yufan/recsys-genrec-dataset).
SIDR_HF_REPO="${SIDR_HF_REPO:-yufan/recsys-genrec-dataset-refresh-gpt5.4}"
HOSTFILE="${HOSTFILE:-$HOME/hostfile}"
DIST_MASTER_PORT="${DIST_MASTER_PORT:-29500}"
GPUS_PER_NODE="${GPUS_PER_NODE:-8}"
MICRO_BATCH_SIZE="${MICRO_BATCH_SIZE:-8}"
NUM_EPOCHS="${NUM_EPOCHS:-10}"
LR="${LR:-9e-5}"
NCCL_DEBUG="${NCCL_DEBUG:-WARN}"
DRY_RUN="${DRY_RUN:-0}"
EVAL_NUM_SAMPLES="${EVAL_NUM_SAMPLES:--1}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-96}"

DEFAULT_CATEGORIES=(Video_Games Office_Products Industrial_and_Scientific)
if [[ $# -gt 0 ]]; then
    CATEGORIES=("$@")
else
    CATEGORIES=("${DEFAULT_CATEGORIES[@]}")
fi

is_positive_integer() {
    [[ "$1" =~ ^[1-9][0-9]*$ ]]
}

is_valid_category() {
    case "$1" in
        Video_Games|Office_Products|Industrial_and_Scientific) return 0 ;;
        *) return 1 ;;
    esac
}

if [[ ! -r "$HOSTFILE" ]]; then
    echo "[launcher] Hostfile is not readable: $HOSTFILE" >&2
    exit 1
fi
if ! is_positive_integer "$GPUS_PER_NODE"; then
    echo "[launcher] GPUS_PER_NODE must be a positive integer: $GPUS_PER_NODE" >&2
    exit 1
fi
if ! is_positive_integer "$MICRO_BATCH_SIZE"; then
    echo "[launcher] MICRO_BATCH_SIZE must be a positive integer: $MICRO_BATCH_SIZE" >&2
    exit 1
fi
if ! is_positive_integer "$NUM_EPOCHS"; then
    echo "[launcher] NUM_EPOCHS must be a positive integer: $NUM_EPOCHS" >&2
    exit 1
fi
if ! is_positive_integer "$DIST_MASTER_PORT"; then
    echo "[launcher] DIST_MASTER_PORT must be a positive integer: $DIST_MASTER_PORT" >&2
    exit 1
fi
if ! is_positive_integer "$EVAL_BATCH_SIZE"; then
    echo "[launcher] EVAL_BATCH_SIZE must be a positive integer: $EVAL_BATCH_SIZE" >&2
    exit 1
fi
if [[ ! "$EVAL_NUM_SAMPLES" =~ ^-1$|^[1-9][0-9]*$ ]]; then
    echo "[launcher] EVAL_NUM_SAMPLES must be -1 or a positive integer: $EVAL_NUM_SAMPLES" >&2
    exit 1
fi
for category in "${CATEGORIES[@]}"; do
    if ! is_valid_category "$category"; then
        echo "[launcher] Unsupported category: $category" >&2
        exit 1
    fi
done

HOSTS=()
SLOTS=()
while read -r host slots_field _; do
    if [[ -z "$host" || "$host" == \#* ]]; then
        continue
    fi
    if [[ "$slots_field" != slots=* ]]; then
        echo "[launcher] Invalid hostfile row for $host: expected 'slots=N'" >&2
        exit 1
    fi
    slots="${slots_field#slots=}"
    if ! is_positive_integer "$slots"; then
        echo "[launcher] Invalid slot count for $host: $slots" >&2
        exit 1
    fi
    if [[ $slots -lt $GPUS_PER_NODE ]]; then
        echo "[launcher] $host has $slots slots, fewer than GPUS_PER_NODE=$GPUS_PER_NODE" >&2
        exit 1
    fi
    HOSTS+=("$host")
    SLOTS+=("$slots")
done < "$HOSTFILE"

if [[ ${#HOSTS[@]} -eq 0 ]]; then
    echo "[launcher] Hostfile contains no hosts: $HOSTFILE" >&2
    exit 1
fi

LOCAL_HOSTNAME="$(hostname)"
LOCAL_SHORT_HOSTNAME="$(hostname -s)"
FIRST_HOST="${HOSTS[0]}"
if [[ "$FIRST_HOST" != "$LOCAL_HOSTNAME" &&
      "$FIRST_HOST" != "$LOCAL_SHORT_HOSTNAME" &&
      "${FIRST_HOST%%.*}" != "$LOCAL_SHORT_HOSTNAME" ]]; then
    echo "[launcher] Hostfile rank 0 must be this node." >&2
    echo "[launcher] first_host=$FIRST_HOST local_host=$LOCAL_HOSTNAME" >&2
    exit 1
fi

NUM_NODES="${#HOSTS[@]}"
MASTER_ADDR="${MASTER_ADDR:-$FIRST_HOST}"
GLOBAL_BATCH_SIZE=$((MICRO_BATCH_SIZE * GPUS_PER_NODE * NUM_NODES))
EVAL_CUDA_LIST=""
for ((gpu = 0; gpu < GPUS_PER_NODE; gpu++)); do
    EVAL_CUDA_LIST+="${EVAL_CUDA_LIST:+,}${gpu}"
done

mkdir -p logs output_dir

export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export HF_HUB_ENABLE_HF_TRANSFER="${HF_HUB_ENABLE_HF_TRANSFER:-1}"

# Never inherit the single-node launcher's fabric-disabling settings.
unset NCCL_IB_DISABLE
unset NCCL_P2P_DISABLE
unset NCCL_NET_GDR_LEVEL

if [[ "$DRY_RUN" != "1" ]]; then
    for command_name in deepspeed ssh tar; do
        if ! command -v "$command_name" >/dev/null 2>&1; then
            echo "[launcher] Required command not found: $command_name" >&2
            exit 1
        fi
    done
fi
if [[ ! -f "$SCRIPT_DIR/sft_Qwen3.py" ]]; then
    echo "[launcher] Training script not found: $SCRIPT_DIR/sft_Qwen3.py" >&2
    exit 1
fi
if [[ ! -f "$SCRIPT_DIR/evaluate_checkpoints.py" ]]; then
    echo "[launcher] Evaluation script not found: $SCRIPT_DIR/evaluate_checkpoints.py" >&2
    exit 1
fi
if [[ ! -f "$SCRIPT_DIR/prepare_epoch_zero.py" ]]; then
    echo "[launcher] Epoch-0 preparation script not found: $SCRIPT_DIR/prepare_epoch_zero.py" >&2
    exit 1
fi

echo "[launcher] nodes=$NUM_NODES gpus_per_node=$GPUS_PER_NODE world_size=$((NUM_NODES * GPUS_PER_NODE))"
echo "[launcher] master=$MASTER_ADDR:$DIST_MASTER_PORT global_batch=$GLOBAL_BATCH_SIZE"
echo "[launcher] categories=${CATEGORIES[*]} hostfile=$HOSTFILE"

COMMON_ENV=(
    "PATH=$PATH"
    "PYTHONPATH=$PYTHONPATH"
    "PYTORCH_CUDA_ALLOC_CONF=$PYTORCH_CUDA_ALLOC_CONF"
    "HF_HUB_ENABLE_HF_TRANSFER=$HF_HUB_ENABLE_HF_TRANSFER"
    "NCCL_DEBUG=$NCCL_DEBUG"
    "SIDR_HF_REPO=$SIDR_HF_REPO"
)
ENV_COMMAND=(
    env
    -u NCCL_IB_DISABLE
    -u NCCL_P2P_DISABLE
    -u NCCL_NET_GDR_LEVEL
)

for variable_name in \
    HF_HOME HF_DATASETS_CACHE HUGGINGFACE_HUB_CACHE TRANSFORMERS_CACHE \
    CUDA_HOME LD_LIBRARY_PATH NCCL_IB_HCA NCCL_IB_GID_INDEX NCCL_IB_TC NCCL_IB_SL \
    NCCL_IB_TIMEOUT NCCL_IB_RETRY_CNT NCCL_IB_PCI_RELAXED_ORDERING NCCL_TOPO_FILE \
    NCCL_SHARP_DISABLE NCCL_SOCKET_IFNAME UCX_NET_DEVICES; do
    if [[ -n "${!variable_name:-}" ]]; then
        COMMON_ENV+=("$variable_name=${!variable_name}")
    fi
done

SSH_OPTIONS=(
    -o BatchMode=yes
    -o StrictHostKeyChecking=no
    -o ConnectTimeout=15
    -o ServerAliveInterval=30
    -o ServerAliveCountMax=4
)
if command -v uv >/dev/null 2>&1; then
    PYTHON_COMMAND=(uv run python)
elif command -v python >/dev/null 2>&1; then
    PYTHON_COMMAND=(python)
else
    echo "[launcher] Neither uv nor python is available for HF prefetch." >&2
    exit 1
fi
ACTIVE_PIDS=()
ACTIVE_HOSTS=()
CURRENT_ENV=()

cleanup() {
    local pid
    if [[ ${#ACTIVE_PIDS[@]} -eq 0 ]]; then
        return
    fi
    for pid in "${ACTIVE_PIDS[@]}"; do
        kill "$pid" >/dev/null 2>&1 || true
    done
}
trap cleanup EXIT
trap 'exit 130' INT TERM

shell_join() {
    local joined
    printf -v joined '%q ' "$@"
    printf '%s' "$joined"
}

launch_process() {
    local node_rank="$1"
    local host="$2"
    local log_file="$3"
    shift 3

    if [[ "$DRY_RUN" == "1" ]]; then
        echo "[dry-run] node_rank=$node_rank host=$host log=$log_file"
        echo "  cd $(printf '%q' "$REPO_ROOT") && $(shell_join "${ENV_COMMAND[@]}" "${CURRENT_ENV[@]}" "$@")"
        return 0
    fi

    if [[ $node_rank -eq 0 ]]; then
        (
            cd "$REPO_ROOT"
            "${ENV_COMMAND[@]}" "${CURRENT_ENV[@]}" "$@"
        ) > "$log_file" 2>&1 &
    else
        local quoted_repo remote_command
        printf -v quoted_repo '%q' "$REPO_ROOT"
        remote_command="cd $quoted_repo && $(shell_join "${ENV_COMMAND[@]}" "${CURRENT_ENV[@]}" "$@")"
        ssh "${SSH_OPTIONS[@]}" "$host" "$remote_command" > "$log_file" 2>&1 &
    fi

    ACTIVE_PIDS+=("$!")
    ACTIVE_HOSTS+=("$host")
}

wait_for_processes() {
    local phase="$1"
    local remaining="${#ACTIVE_PIDS[@]}"
    local index
    local other_index
    local -a finished

    while [[ $remaining -gt 0 ]]; do
        for index in "${!ACTIVE_PIDS[@]}"; do
            if [[ "${finished[$index]:-0}" == "1" ]]; then
                continue
            fi
            if kill -0 "${ACTIVE_PIDS[$index]}" >/dev/null 2>&1; then
                continue
            fi

            if wait "${ACTIVE_PIDS[$index]}"; then
                echo "[$phase] completed host=${ACTIVE_HOSTS[$index]}"
                finished[$index]=1
                remaining=$((remaining - 1))
                continue
            fi

            echo "[$phase] failed host=${ACTIVE_HOSTS[$index]}" >&2
            finished[$index]=1
            for other_index in "${!ACTIVE_PIDS[@]}"; do
                if [[ "${finished[$other_index]:-0}" != "1" ]]; then
                    kill "${ACTIVE_PIDS[$other_index]}" >/dev/null 2>&1 || true
                fi
            done
            for other_index in "${!ACTIVE_PIDS[@]}"; do
                if [[ "${finished[$other_index]:-0}" != "1" ]]; then
                    wait "${ACTIVE_PIDS[$other_index]}" >/dev/null 2>&1 || true
                fi
            done
            ACTIVE_PIDS=()
            ACTIVE_HOSTS=()
            return 1
        done
        if [[ $remaining -gt 0 ]]; then
            sleep 1
        fi
    done

    ACTIVE_PIDS=()
    ACTIVE_HOSTS=()
}

prepare_workers() {
    local node_rank
    local host
    local quoted_hostfile
    local quoted_hostfile_dir
    local quoted_python_command
    local quoted_repo
    local remote_command

    printf -v quoted_hostfile '%q' "$HOSTFILE"
    printf -v quoted_hostfile_dir '%q' "$(dirname "$HOSTFILE")"
    printf -v quoted_python_command '%q' "${PYTHON_COMMAND[0]}"
    printf -v quoted_repo '%q' "$REPO_ROOT"

    for node_rank in "${!HOSTS[@]}"; do
        if [[ $node_rank -eq 0 ]]; then
            continue
        fi
        host="${HOSTS[$node_rank]}"
        if [[ "$DRY_RUN" == "1" ]]; then
            echo "[dry-run] sync hostfile and preflight host=$host"
            continue
        fi

        ssh "${SSH_OPTIONS[@]}" "$host" \
            "mkdir -p $quoted_hostfile_dir && cat > $quoted_hostfile" < "$HOSTFILE"

        remote_command="cd $quoted_repo && test -r $quoted_hostfile && test -f phase1_alignment_sft/sft_Qwen3.py && command -v deepspeed >/dev/null && command -v $quoted_python_command >/dev/null"
        if ! ssh "${SSH_OPTIONS[@]}" "$host" "$remote_command"; then
            echo "[launcher] Worker preflight failed: $host" >&2
            return 1
        fi
        echo "[launcher] Worker preflight passed: $host"
    done
}

if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] HOSTFILE=$(printf '%q' "$HOSTFILE") bash scripts/sync_code_to_nodes.sh"
else
    HOSTFILE="$HOSTFILE" bash scripts/sync_code_to_nodes.sh
fi
prepare_workers

for CATEGORY in "${CATEGORIES[@]}"; do
    RUN_NAME="${CATEGORY}_Stage1_SFT_Qwen3-1.7B"
    OUTPUT_DIR="./output_dir/${CATEGORY}_stage1_sft_Qwen3-1.7B_distributed"
    TRAIN_LOG="./logs/${CATEGORY}_stage1_sft_Qwen3-1.7B_distributed.txt"
    PRE_EVAL_LOG="./logs/${CATEGORY}_stage1_sft_Qwen3-1.7B_distributed.eval_epoch0.txt"
    POST_EVAL_LOG="./logs/${CATEGORY}_stage1_sft_Qwen3-1.7B_distributed.eval_epochs.txt"
    WANDB_PROJECT="SIDReasoner_Phase1_Distributed_Training"
    WANDB_RUN_ID="${RUN_NAME}-$(date -u +%Y%m%dT%H%M%SZ)-$$"

    echo "==== [Stage-1 distributed] PREFETCH domain=$CATEGORY ===="
    CURRENT_ENV=(
        "${COMMON_ENV[@]}"
        "HF_HUB_OFFLINE=0"
        "HF_DATASETS_OFFLINE=0"
        "TRANSFORMERS_OFFLINE=0"
    )
    for node_rank in "${!HOSTS[@]}"; do
        PREFETCH_LOG="./logs/${CATEGORY}_prefetch.node${node_rank}.txt"
        launch_process \
            "$node_rank" "${HOSTS[$node_rank]}" "$PREFETCH_LOG" \
            "${PYTHON_COMMAND[@]}" scripts/prefetch_hf.py \
            --category "$CATEGORY" \
            --base_model "$BASE_MODEL" \
            --strict
    done
    wait_for_processes "prefetch:$CATEGORY"

    # Build the identical SID-extended baseline on every node's local
    # filesystem, then evaluate node-0's copy before training starts.
    echo "==== [Stage-1 distributed] PREPARE epoch_0 domain=$CATEGORY ===="
    CURRENT_ENV=(
        "${COMMON_ENV[@]}"
        "HF_HUB_OFFLINE=1"
        "HF_DATASETS_OFFLINE=1"
        "TRANSFORMERS_OFFLINE=1"
    )
    for node_rank in "${!HOSTS[@]}"; do
        if [[ $node_rank -eq 0 ]]; then
            PREPARE_LOG="./logs/${CATEGORY}_stage1_sft_Qwen3-1.7B_distributed.prepare.txt"
        else
            PREPARE_LOG="./logs/${CATEGORY}_stage1_sft_Qwen3-1.7B_distributed.prepare.node${node_rank}.txt"
        fi
        launch_process \
            "$node_rank" "${HOSTS[$node_rank]}" "$PREPARE_LOG" \
            "${PYTHON_COMMAND[@]}" "$SCRIPT_DIR/prepare_epoch_zero.py" \
            --base-model "$BASE_MODEL" \
            --output-dir "$OUTPUT_DIR" \
            --category "$CATEGORY" \
            --wandb-run-id "$WANDB_RUN_ID" \
            --seed 42 \
            --dtype bf16
    done
    wait_for_processes "prepare-epoch0:$CATEGORY"

    echo "==== [Stage-1 distributed] PRE-EVAL epoch_0 domain=$CATEGORY ===="
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "[dry-run] $(shell_join "${PYTHON_COMMAND[@]}" "$SCRIPT_DIR/evaluate_checkpoints.py" \
            --output-dir "$OUTPUT_DIR" \
            --category "$CATEGORY" \
            --cuda-list "$EVAL_CUDA_LIST" \
            --num-samples "$EVAL_NUM_SAMPLES" \
            --batch-size "$EVAL_BATCH_SIZE" \
            --num-beams 10 \
            --min-epoch 0 \
            --max-epoch 0 \
            --report-to wandb \
            --wandb-project "$WANDB_PROJECT" \
            --wandb-run-name "$RUN_NAME" \
            --wandb-run-id "$WANDB_RUN_ID")"
    else
        "${ENV_COMMAND[@]}" "${COMMON_ENV[@]}" \
            HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
            "${PYTHON_COMMAND[@]}" "$SCRIPT_DIR/evaluate_checkpoints.py" \
            --output-dir "$OUTPUT_DIR" \
            --category "$CATEGORY" \
            --cuda-list "$EVAL_CUDA_LIST" \
            --num-samples "$EVAL_NUM_SAMPLES" \
            --batch-size "$EVAL_BATCH_SIZE" \
            --num-beams 10 \
            --min-epoch 0 \
            --max-epoch 0 \
            --report-to wandb \
            --wandb-project "$WANDB_PROJECT" \
            --wandb-run-name "$RUN_NAME" \
            --wandb-run-id "$WANDB_RUN_ID" \
            > "$PRE_EVAL_LOG" 2>&1
    fi

    echo "==== [Stage-1 distributed] TRAIN domain=$CATEGORY -> $OUTPUT_DIR ===="
    CURRENT_ENV=(
        "${COMMON_ENV[@]}"
        "HF_HUB_OFFLINE=1"
        "HF_DATASETS_OFFLINE=1"
        "TRANSFORMERS_OFFLINE=1"
    )
    for node_rank in "${!HOSTS[@]}"; do
        if [[ $node_rank -eq 0 ]]; then
            NODE_LOG="$TRAIN_LOG"
        else
            NODE_LOG="./logs/${CATEGORY}_stage1_sft_Qwen3-1.7B_distributed.node${node_rank}.txt"
        fi

        launch_process \
            "$node_rank" "${HOSTS[$node_rank]}" "$NODE_LOG" \
            deepspeed \
            --hostfile "$HOSTFILE" \
            --no_ssh \
            --node_rank "$node_rank" \
            --master_addr "$MASTER_ADDR" \
            --master_port "$DIST_MASTER_PORT" \
            --num_nodes "$NUM_NODES" \
            --num_gpus "$GPUS_PER_NODE" \
            "$SCRIPT_DIR/sft_Qwen3.py" \
            --base_model "$OUTPUT_DIR/epoch_0" \
            --micro_batch_size "$MICRO_BATCH_SIZE" \
            --num_epochs "$NUM_EPOCHS" \
            --early_stopping_patience 2 \
            --learning_rate "$LR" \
            --cutoff_len 1024 \
            --output_dir "$OUTPUT_DIR" \
            --report_to wandb \
            --wandb_project "$WANDB_PROJECT" \
            --wandb_run_name "$RUN_NAME" \
            --wandb_run_id "$WANDB_RUN_ID" \
            --epoch_zero_prepared \
            --category "$CATEGORY" \
            --seed 42 \
            --mask_assistant True \
            --zero_stage 2 \
            --dtype bf16 \
            --gradient_checkpointing \
            --deepspeed
    done
    wait_for_processes "train:$CATEGORY"

    # Every DeepSpeed process has exited. Replay only trained checkpoints;
    # epoch_0 already succeeded before training and is retained in metrics.json.
    echo "==== [Stage-1 distributed] POST-EVAL domain=$CATEGORY checkpoints=$OUTPUT_DIR/epoch_[1-N] ===="
    if [[ "$DRY_RUN" == "1" ]]; then
        echo "[dry-run] $(shell_join "${PYTHON_COMMAND[@]}" "$SCRIPT_DIR/evaluate_checkpoints.py" \
            --output-dir "$OUTPUT_DIR" \
            --category "$CATEGORY" \
            --cuda-list "$EVAL_CUDA_LIST" \
            --num-samples "$EVAL_NUM_SAMPLES" \
            --batch-size "$EVAL_BATCH_SIZE" \
            --num-beams 10 \
            --min-epoch 1 \
            --report-to wandb \
            --wandb-project "$WANDB_PROJECT" \
            --wandb-run-name "$RUN_NAME" \
            --wandb-run-id "$WANDB_RUN_ID")"
    else
        "${ENV_COMMAND[@]}" "${COMMON_ENV[@]}" \
            HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
            "${PYTHON_COMMAND[@]}" "$SCRIPT_DIR/evaluate_checkpoints.py" \
            --output-dir "$OUTPUT_DIR" \
            --category "$CATEGORY" \
            --cuda-list "$EVAL_CUDA_LIST" \
            --num-samples "$EVAL_NUM_SAMPLES" \
            --batch-size "$EVAL_BATCH_SIZE" \
            --num-beams 10 \
            --min-epoch 1 \
            --report-to wandb \
            --wandb-project "$WANDB_PROJECT" \
            --wandb-run-name "$RUN_NAME" \
            --wandb-run-id "$WANDB_RUN_ID" \
            > "$POST_EVAL_LOG" 2>&1
    fi
    echo "==== [Stage-1 distributed] DONE domain=$CATEGORY ===="
done

echo "==== [Stage-1 distributed] all domains finished: ${CATEGORIES[*]} ===="
