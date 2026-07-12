"""Central Hugging Face data loader for SIDReasoner.

The explicit APIs (``load_seqrec``, ``load_item_features``, and friends) map a
category and split directly to ``yufan/recsys-genrec-dataset``. Override the
repository with ``$SIDR_HF_REPO``.

Legacy path-based adapters remain for pipelines that have not migrated yet;
new training code should use the explicit APIs.

Config <-> legacy-file mapping
------------------------------
    <cat>_seqrec      train/valid/test CSV        -> load_df()
    <cat>_catalog     item.json + index.json      -> load_item_feat(), load_indices()
                      item_enhanced_v2.json       -> load_enhanced()  (`sid_interleaved_narrative`)
                      info/*.txt                  -> load_info_lines()
    <cat>_reasoning   integrated_narrative.csv    -> load_df()
    general_reasoning general/sampled_data.arrow  -> load_general()
"""

import os
import json
import functools

import numpy as np
import pandas as pd

HF_REPO = os.environ.get("SIDR_HF_REPO", "yufan/recsys-genrec-dataset")

CATEGORIES = ["Video_Games", "Office_Products", "Industrial_and_Scientific"]


# --------------------------------------------------------------------------- #
# low-level loading (cached)                                                   #
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=None)
def _load_split(config, split):
    """Load one (config, split) as a pandas DataFrame, cached per process."""
    from datasets import load_dataset

    ds = load_dataset(HF_REPO, config, split=split)
    return ds.to_pandas()


@functools.lru_cache(maxsize=None)
def _catalog(category):
    return _load_split(f"{category}_catalog", "train")


# --------------------------------------------------------------------------- #
# path -> (category, config, split) inference                                 #
# --------------------------------------------------------------------------- #
def infer_category(path):
    """Extract the category name from a legacy file path/locator."""
    base = os.path.basename(str(path))
    if "_5_" in base:                       # <cat>_5_2016-10-2018-11.csv/.txt
        return base.split("_5_")[0]
    return base.split(".")[0]               # <cat>.item.json / <cat>.index.json / ...


def _seqrec_split(path):
    parent = os.path.basename(os.path.dirname(str(path))).lower()
    name = os.path.basename(str(path)).lower()
    if parent == "valid" or "valid" in name:
        return "validation"
    if parent == "test" or "_for_test" in name:
        return "test"
    return "train"


def _stringify_list_columns(df):
    """Reproduce ``pd.read_csv`` semantics: list/array cells -> ``str([...])``.

    The parquet stores real Python lists for ``history_item_*`` columns, but the
    original code reads CSV strings and calls ``eval(...)`` on them, so we
    convert list-typed columns back to their string representation.
    """
    df = df.copy()
    for col in df.columns:
        sample = next((v for v in df[col].head(50) if v is not None), None)
        if isinstance(sample, (list, np.ndarray)):
            df[col] = df[col].map(
                lambda x: str(list(x)) if isinstance(x, (list, np.ndarray)) else x
            )
    return df


# --------------------------------------------------------------------------- #
# explicit Hugging Face APIs                                                   #
# --------------------------------------------------------------------------- #
def load_seqrec(category, split="train"):
    """Load a category's sequential-recommendation split."""
    if split not in {"train", "validation", "test"}:
        raise ValueError(f"Unsupported seqrec split: {split}")
    return _stringify_list_columns(_load_split(f"{category}_seqrec", split))


def load_sequence_narratives(category):
    """Load the category-level reasoning narratives used by sequence tasks."""
    return _stringify_list_columns(_load_split(f"{category}_reasoning", "train"))


def load_item_features(category):
    """Return catalog item metadata keyed by item ID."""
    df = _catalog(category)
    features = {}
    for row in df.itertuples(index=False):
        features[str(row.item_id)] = {
            "title": row.title,
            "description": row.description,
            "brand": getattr(row, "brand", None),
            "categories": "",
        }
    return features


def load_sid_indices(category):
    """Return each catalog item's ordered SID-token sequence."""
    df = _catalog(category)
    return {
        str(row.item_id): list(row.sid_tokens)
        for row in df.itertuples(index=False)
    }


def load_sid_tokens(category):
    """Return the sorted, unique SID tokens that extend the model vocabulary."""
    return sorted({
        token
        for sid_tokens in load_sid_indices(category).values()
        for token in sid_tokens
    })


def load_item_narratives(category):
    """Return item-level SID/text narratives keyed by item ID."""
    df = _catalog(category)
    narratives = {}
    for row in df.itertuples(index=False):
        narrative = row.sid_interleaved_narrative
        if narrative is not None and not (
            isinstance(narrative, float) and np.isnan(narrative)
        ):
            narratives[str(row.item_id)] = {
                "sid_interleaved_narrative": narrative
            }
    return narratives


def load_general_reasoning():
    """Return decoded role/content messages for general-reasoning SFT."""
    df = _load_split("general_reasoning", "train")
    output = []
    for messages in df["messages"].tolist():
        # The column may contain nested JSON strings; decode to the actual list.
        for _ in range(3):
            if isinstance(messages, str):
                messages = json.loads(messages)
            else:
                break
        output.append(messages)
    return output


# --------------------------------------------------------------------------- #
# legacy path-based adapters                                                   #
# --------------------------------------------------------------------------- #
def load_df(path):
    """Replacement for ``pd.read_csv(path)`` on seqrec / reasoning CSVs.

    If ``path`` is a real local file (e.g. the per-GPU chunk CSVs that
    ``evaluation/split.py`` materializes, or a user-provided local copy), it is
    read directly; otherwise the path is treated as a locator and resolved
    against the Hugging Face dataset.
    """
    if os.path.isfile(str(path)):
        return pd.read_csv(path)
    category = infer_category(path)
    name = os.path.basename(str(path)).lower()
    if "integrated_narrative" in name:
        return load_sequence_narratives(category)
    return load_seqrec(category, _seqrec_split(path))


def load_item_feat(item_file):
    """Replacement for ``json.load(open(<cat>.item.json))`` -> {id: {..}} dict."""
    return load_item_features(infer_category(item_file))


def load_indices(index_file):
    """Replacement for ``json.load(open(<cat>.index.json))`` -> {id: [sids]} dict."""
    return load_sid_indices(infer_category(index_file))


def load_enhanced(json_file):
    """Replacement for ``json.load(open(<cat>.item_enhanced_v2.json))``.

    Returns ``{id: {"sid_interleaved_narrative": <narrative>}}`` — the only field
    ``SidTextInterleaveItemDataset`` consumes. (The legacy field name was
    ``llm_stage2``; "stage2" was the data-generation step, not training Phase-2.)
    """
    return load_item_narratives(infer_category(json_file))


def load_general(path=None):
    """Replacement for the general reasoning JSONL reader.

    Returns a list where each element is the parsed ``messages`` object
    (list of role/content dicts), matching ``eval(sample["messages"])``.
    """
    return load_general_reasoning()


def load_info_lines(info_file):
    """Replacement for ``open(<cat>_5_...txt).readlines()``.

    Rebuilds the ``semantic_id \\t title \\t item_id`` map from the catalog,
    ordered by ``item_id`` (== the 0-based index the evaluator relies on).
    """
    df = _catalog(infer_category(info_file)).sort_values("item_id")
    lines = []
    for r in df.itertuples(index=False):
        lines.append(f"{r.sid}\t{r.title}\t{r.item_id}\n")
    return lines
