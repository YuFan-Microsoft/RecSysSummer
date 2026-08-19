from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

from app import (
    DEFAULT_CHECKPOINT_REPO,
    DEFAULT_CHECKPOINT_REVISION,
    DEFAULT_CHECKPOINT_SUBDIR,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the pinned default SIDReasoner Video Games checkpoint."
    )
    parser.add_argument(
        "--local-dir",
        default=None,
        help="Optional download root. The Hugging Face cache is used by default.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_path = snapshot_download(
        repo_id=DEFAULT_CHECKPOINT_REPO,
        repo_type="dataset",
        revision=DEFAULT_CHECKPOINT_REVISION,
        allow_patterns=[f"{DEFAULT_CHECKPOINT_SUBDIR}/*"],
        local_dir=args.local_dir,
    )
    checkpoint_path = Path(snapshot_path) / DEFAULT_CHECKPOINT_SUBDIR
    required_files = ("config.json", "model.safetensors", "tokenizer.json")
    missing = [name for name in required_files if not (checkpoint_path / name).is_file()]
    if missing:
        raise RuntimeError(f"Downloaded checkpoint is incomplete: {', '.join(missing)}")
    print(checkpoint_path.resolve())


if __name__ == "__main__":
    main()