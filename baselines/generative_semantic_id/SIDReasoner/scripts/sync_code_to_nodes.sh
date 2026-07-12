#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_PARENT="$(dirname "$REPO_ROOT")"
REPO_NAME="$(basename "$REPO_ROOT")"

HOSTFILE="${HOSTFILE:-$HOME/hostfile}"
SSH_OPTIONS=(
    -o BatchMode=yes
    -o StrictHostKeyChecking=no
    -o ConnectTimeout=15
    -o ServerAliveInterval=30
    -o ServerAliveCountMax=4
)

if [[ ! -r "$HOSTFILE" ]]; then
    echo "[sync] Hostfile is not readable: $HOSTFILE" >&2
    exit 1
fi

HOSTS=()
while read -r host _; do
    if [[ -n "$host" && "$host" != \#* ]]; then
        HOSTS+=("$host")
    fi
done < "$HOSTFILE"

if [[ ${#HOSTS[@]} -eq 0 ]]; then
    echo "[sync] Hostfile contains no hosts: $HOSTFILE" >&2
    exit 1
fi

LOCAL_HOSTNAME="$(hostname)"
LOCAL_SHORT_HOSTNAME="$(hostname -s)"

is_local_host() {
    local host="$1"
    [[ "$host" == "$LOCAL_HOSTNAME" ||
       "$host" == "$LOCAL_SHORT_HOSTNAME" ||
       "${host%%.*}" == "$LOCAL_SHORT_HOSTNAME" ]]
}

sync_host() {
    local host="$1"
    local quoted_parent
    printf -v quoted_parent '%q' "$REPO_PARENT"

    echo "[sync] Sending $REPO_NAME to $host:$REPO_ROOT"
    tar -czf - \
        -C "$REPO_PARENT" \
        --exclude="$REPO_NAME/output_dir" \
        --exclude="$REPO_NAME/logs" \
        --exclude="$REPO_NAME/temp" \
        --exclude="$REPO_NAME/temp_results" \
        --exclude="$REPO_NAME/results" \
        --exclude="$REPO_NAME/result_temp" \
        --exclude="$REPO_NAME/data" \
        --exclude="$REPO_NAME/data_backup" \
        --exclude="$REPO_NAME/downloaded_ckpts" \
        --exclude="$REPO_NAME/wandb" \
        --exclude="$REPO_NAME/analysis_results" \
        --exclude="$REPO_NAME/analysis/analysis_results" \
        --exclude="$REPO_NAME/rq" \
        --exclude="$REPO_NAME/.git" \
        --exclude='__pycache__' \
        --exclude='*/__pycache__' \
        --exclude='*.pyc' \
        "$REPO_NAME" \
        | ssh "${SSH_OPTIONS[@]}" "$host" \
            "mkdir -p $quoted_parent && tar -xzf - -C $quoted_parent"
}

PIDS=()
WORKER_HOSTS=()
for host in "${HOSTS[@]}"; do
    if is_local_host "$host"; then
        echo "[sync] Skipping local host $host"
        continue
    fi
    sync_host "$host" &
    PIDS+=("$!")
    WORKER_HOSTS+=("$host")
done

if [[ ${#PIDS[@]} -eq 0 ]]; then
    echo "[sync] No worker hosts to update."
    exit 0
fi

failed=0
for index in "${!PIDS[@]}"; do
    if wait "${PIDS[$index]}"; then
        echo "[sync] Completed ${WORKER_HOSTS[$index]}"
    else
        echo "[sync] Failed ${WORKER_HOSTS[$index]}" >&2
        failed=1
    fi
done

if [[ $failed -ne 0 ]]; then
    exit 1
fi

echo "[sync] All worker nodes are up to date."
