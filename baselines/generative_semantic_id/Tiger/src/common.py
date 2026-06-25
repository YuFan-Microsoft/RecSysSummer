"""Shared utilities and data I/O for the simplified TIGER pipeline.

Data is read straight from the HuggingFace Hub:

    yufan/amazon2023-item-metadata    config=<Category>            (items + text)
    yufan/amazon2023-user-interactions config=seq_maxlen20_<Category>
                                       (train/validation/test rows, each with a
                                        `history` list and a `parent_asin` target)

Items are keyed by `parent_asin` (a string); we map them to a contiguous
0..N-1 index by sorting the metadata asins, so the same order is reproduced by
every step (embeddings, quantization, TIGER) without passing a mapping file.

Generated artifacts:

    embeddings.pt      float tensor (num_items, embed_dim)         <- step 1
    semantic_ids.pt    dict {"codes": LongTensor(num_items, H),    <- step 2
                             "codebook_width": int, "num_hierarchies": H}

Categories: Video_Games, Industrial_and_Scientific, Beauty_and_Personal_Care,
Musical_Instruments, Books.
"""

import argparse
import hashlib
import os
import random

import torch

ITEM_METADATA_REPO = "yufan/amazon2023-item-metadata"
INTERACTIONS_REPO = "yufan/amazon2023-user-interactions"


def hierarchize(flat_args):
    """Turn a flat argparse Namespace with dotted dest names into nested
    namespaces, so callers can write ``args.model.name`` instead of
    ``getattr(args, "model.name")``. Keys without dots stay at the top level.
    """
    root = {}
    for key, value in vars(flat_args).items():
        node = root
        parts = key.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def build(node):
        if isinstance(node, dict):
            return argparse.Namespace(**{k: build(v) for k, v in node.items()})
        return node

    return build(root)


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device(device: str = "auto") -> torch.device:
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return torch.device(device)


# --------------------------------------------------------------------------- #
# Data loading (HuggingFace)
# --------------------------------------------------------------------------- #
DEFAULT_TEXT_FIELDS = ("title", "features", "description", "categories")


def _field_to_text(value):
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(_field_to_text(v) for v in value)
    return str(value)


def build_item_text(record, fields=DEFAULT_TEXT_FIELDS):
    """Concatenate the chosen metadata fields into a single item description."""
    parts = [_field_to_text(record.get(f)) for f in fields]
    return " ".join(p for p in parts if p).strip()


def load_item_vocab(category, fields=DEFAULT_TEXT_FIELDS):
    """Load item metadata for a category.

    Returns (asins, asin2idx, texts) where `asins` is the sorted list of
    parent_asin (index order), `asin2idx` maps asin -> index, and `texts[i]` is
    the description of item i. The deterministic sort guarantees every step
    agrees on the item index.
    """
    from datasets import load_dataset

    ds = load_dataset(ITEM_METADATA_REPO, category, split="train")
    text_by_asin = {}
    for record in ds:
        text_by_asin[record["parent_asin"]] = build_item_text(record, fields)
    asins = sorted(text_by_asin)
    asin2idx = {a: i for i, a in enumerate(asins)}
    texts = [text_by_asin[a] for a in asins]
    return asins, asin2idx, texts


def load_interaction_splits(category, maxlen=20):
    """Load the leave-one-out sequential splits for a category.

    Returns {split: rows} where each row is (history, target, user_id):
    `history` is a list of parent_asin (oldest first, most-recent-last) and
    `target` is the next parent_asin to predict.
    """
    from datasets import load_dataset

    config = f"seq_maxlen{maxlen}_{category}"
    ds = load_dataset(INTERACTIONS_REPO, config)
    out = {}
    for hf_split, name in [("train", "train"), ("validation", "valid"), ("test", "test")]:
        rows = []
        for record in ds[hf_split]:
            rows.append((list(record["history"]), record["parent_asin"], record["user_id"]))
        out[name] = rows
    return out


def user_hash(user_id, num_bins=1_000_000):
    """Stable hash of a string user id into [0, num_bins) for user embeddings."""
    digest = hashlib.md5(str(user_id).encode()).hexdigest()
    return int(digest, 16) % num_bins


# --------------------------------------------------------------------------- #
# Tensor helpers
# --------------------------------------------------------------------------- #
def mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Mean-pool token embeddings over the sequence using the attention mask."""
    mask = attention_mask.unsqueeze(-1).to(last_hidden_state.dtype)
    summed = (last_hidden_state * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts


def save_pt(obj, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    torch.save(obj, path)


def load_semantic_ids(path: str):
    """Load semantic ids saved by quantize.py. Returns (codes, codebook_width, H)."""
    blob = torch.load(path, map_location="cpu")
    return blob["codes"], int(blob["codebook_width"]), int(blob["num_hierarchies"])


# --------------------------------------------------------------------------- #
# Weights & Biases logging
# --------------------------------------------------------------------------- #
def add_wandb_args(parser):
    """Register the wandb CLI flags on an argparse parser."""
    import datetime as _dt

    parser.add_argument("--logger.wandb.enable", type=int, default=1,
                        help="1=use wandb if a key is available, 0=disable")
    parser.add_argument("--logger.wandb.key", type=str, default=None,
                        help="wandb API key (falls back to $WANDB_API_KEY)")
    parser.add_argument("--logger.wandb.org", type=str, default=None)
    parser.add_argument("--logger.wandb.group", type=str, default=None)
    parser.add_argument("--logger.wandb.project", type=str, default="tiger")
    parser.add_argument("--logger.wandb.run_name", type=str,
                        default="tiger_%s" % _dt.datetime.now().strftime("%m%dT%H:%M"))


def _flatten_namespace(ns, prefix=""):
    out = {}
    for key, value in vars(ns).items():
        name = f"{prefix}{key}"
        if isinstance(value, argparse.Namespace):
            out.update(_flatten_namespace(value, prefix=f"{name}."))
        else:
            out[name] = value
    return out


class WandbLogger:
    """Thin wandb wrapper. No-op when disabled or no key is available.

    Mirrors the reference setup: define separate step axes for train/eval so
    metrics logged at different frequencies line up correctly.
    """

    def __init__(self, args, enabled=True):
        self.run = None
        self.wandb = None
        cfg = args.logger.wandb
        if not enabled or not int(getattr(cfg, "enable", 1)):
            return
        key = cfg.key or os.environ.get("WANDB_API_KEY")
        if not key:
            print("[wandb] no API key found (set --logger.wandb.key or $WANDB_API_KEY); "
                  "logging to console only.")
            return
        import wandb

        self.wandb = wandb
        if not wandb.api.api_key:
            wandb.login(key=key)
        self.run = wandb.init(
            entity=cfg.org, project=cfg.project, group=cfg.group, name=cfg.run_name,
            config=_flatten_namespace(args), reinit=True,
        )
        wandb.define_metric("train/global_step")
        wandb.define_metric("train/*", step_metric="train/global_step")
        wandb.define_metric("eval/global_step")
        wandb.define_metric("eval/*", step_metric="eval/global_step")
        wandb.define_metric("test/*")

    def log(self, data):
        if self.run is not None:
            self.wandb.log(data)

    def finish(self):
        if self.run is not None:
            self.wandb.finish()
