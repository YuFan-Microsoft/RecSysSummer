"""Central Hugging Face data loader for SIDReasoner.

All dataset classes / scripts used to read local files
(``*_5_2016-10-2018-11.csv``, ``<cat>.item.json``, ``<cat>.index.json``,
``<cat>.item_enhanced_v2.json``, ``<cat>.integrated_narrative.csv``,
``general/sampled_data.arrow`` and the ``info/*.txt`` maps).

Those files no longer need to exist on disk: this module fetches the
equivalent data straight from the Hugging Face dataset
``yufan/recsys-genrec-dataset`` (override with ``$SIDR_HF_REPO``) via
``datasets.load_dataset`` and returns the *exact* in-memory structures the
existing code expects, so the call sites only change by one line.

Legacy file-path arguments are kept as *locators*: we parse the category
(and, for the sequence data, the split) out of the path string, so the
training / evaluation shell scripts do not need to change.

Config <-> legacy-file mapping
------------------------------
    <cat>_seqrec      train/valid/test CSV        -> load_df()
    <cat>_catalog     item.json + index.json      -> load_item_feat(), load_indices()
                      item_enhanced_v2.json       -> load_enhanced()  (`llm_stage2`)
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
# public API — drop-in replacements for the old reads                         #
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
        df = _load_split(f"{category}_reasoning", "train")
    else:
        df = _load_split(f"{category}_seqrec", _seqrec_split(path))
    return _stringify_list_columns(df)


def load_item_feat(item_file):
    """Replacement for ``json.load(open(<cat>.item.json))`` -> {id: {..}} dict."""
    df = _catalog(infer_category(item_file))
    feat = {}
    for r in df.itertuples(index=False):
        feat[str(r.item_id)] = {
            "title": r.title,
            "description": r.description,
            "brand": getattr(r, "brand", None),
            "categories": "",
        }
    return feat


def load_indices(index_file):
    """Replacement for ``json.load(open(<cat>.index.json))`` -> {id: [sids]} dict."""
    df = _catalog(infer_category(index_file))
    idx = {}
    for r in df.itertuples(index=False):
        idx[str(r.item_id)] = list(r.sid_tokens)
    return idx


def load_enhanced(json_file):
    """Replacement for ``json.load(open(<cat>.item_enhanced_v2.json))``.

    Returns ``{id: {"llm_stage2": <sid-interleaved narrative>}}`` — the only
    field ``SidTextInterleaveDataset_v2`` consumes.
    """
    df = _catalog(infer_category(json_file))
    out = {}
    for r in df.itertuples(index=False):
        narrative = r.sid_interleaved_narrative
        if narrative is not None and not (isinstance(narrative, float) and np.isnan(narrative)):
            out[str(r.item_id)] = {"llm_stage2": narrative}
    return out


def load_general(path=None):
    """Replacement for the general reasoning JSONL reader.

    Returns a list where each element is the parsed ``messages`` object
    (list of role/content dicts), matching ``eval(sample["messages"])``.
    """
    df = _load_split("general_reasoning", "train")
    out = []
    for messages in df["messages"].tolist():
        # ``messages`` is stored double-encoded (a JSON string wrapping the
        # inner messages-JSON string that the original code ``eval``-decoded);
        # decode until we get the actual list of role/content dicts.
        for _ in range(3):
            if isinstance(messages, str):
                messages = json.loads(messages)
            else:
                break
        out.append(messages)
    return out


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
