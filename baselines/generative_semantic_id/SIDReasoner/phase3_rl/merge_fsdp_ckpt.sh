#!/bin/bash

# === Usage ===
# bash merge_fsdp_ckpt.sh   (edit CKPT_DIR below, or adapt to take $1)
#
# Uses verl v0.6.0: `verl` is a top-level package dir at the repo root, so
# merge_fsdp_checkpoint.py's `from verl.model_merger ...` (with
# PYTHONPATH=$REPO_ROOT) resolves to it.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

CKPT_DIR="./output_dir/Video_Games_stage3_rl_Qwen3-1.7B/global_step_100/actor"

if [ -z "$CKPT_DIR" ]; then
    echo "❌ ERROR: Please provide a verl checkpoint directory."
    echo "Usage: bash merge_fsdp_ckpt.sh /path/to/actor"
    exit 1
fi

# Remove trailing slash if exists
CKPT_DIR="${CKPT_DIR%/}"

# Output directory
MERGED_DIR="${CKPT_DIR}_merged"

echo "🔍 Verl checkpoint directory: $CKPT_DIR"
echo "📦 Will save merged HF model to: $MERGED_DIR"
echo ""


MERGE_PY="$SCRIPT_DIR/merge_fsdp_checkpoint.py"

if [ ! -f "$MERGE_PY" ]; then
    echo "❌ ERROR: Cannot find merge_fsdp_checkpoint.py."
    echo "Expected at: $MERGE_PY"
    exit 1
fi

echo "🔧 Using merge script: $MERGE_PY"
echo ""

# Run merge
python3 "$MERGE_PY" \
    --checkpoint "$CKPT_DIR" 
    # --save_path "$MERGED_DIR"

echo ""
echo "✅ Merge completed!"
echo "📁 Merged HuggingFace model is saved to:"
echo "   $MERGED_DIR"
echo ""
echo "You can load it with:"
echo "   from transformers import AutoModelForCausalLM"
echo "   model = AutoModelForCausalLM.from_pretrained('$MERGED_DIR')"
