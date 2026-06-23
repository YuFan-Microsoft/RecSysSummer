# Amazon Reviews 2023 — Data Processing

Reproducible code that turns the official **Amazon Reviews 2023** release into
ready-to-use **sequential / generative recommendation** splits (5-core,
leave-one-out, with item content features). Output is **JSON Lines**.

The produced data is published on the Hugging Face Hub:

| Dataset | Content |
|---|---|
| 🤗 [`yufan/amazon2023-user-interactions`](https://huggingface.co/datasets/yufan/amazon2023-user-interactions) | user–item interactions + leave-one-out / sequential splits (20 configs) |
| 🤗 [`yufan/amazon2023-item-metadata`](https://huggingface.co/datasets/yufan/amazon2023-item-metadata) | item content features — title, images, price, … (5 configs) |

> You usually **don't need to run anything** — just `load_dataset(...)` from the
> Hub. This repo is here for full reproducibility and to regenerate / extend the
> data (e.g. add categories or change `maxlen`).

## What it does

```
download (official 0-core rating_only)  ->  iterative 5-core filtering
  ->  per-user chronological ordering    ->  leave-one-out split
  ->  sequential history at maxlen 20 & 50
  ->  join item metadata (title, images, …)
  ->  write JSONL + statistics + validate against the official benchmark
```

The 5-core and leave-one-out logic is borrowed **verbatim** from the official
[Amazon Reviews 2023 benchmark scripts](https://github.com/hyp1231/AmazonReviews2023/tree/main/benchmark_scripts)
(`kcore_filtering.py`, `last_out_split.py`), so the output **reproduces the
official `5core/last_out` splits exactly** — and matches, to the digit, the
statistics reported by ~15 peer-reviewed papers. See
[`Amazon-2023_Data_Processing_Protocol.md`](Amazon-2023_Data_Processing_Protocol.md)
for the full protocol and validation.

Categories: `Video_Games`, `Industrial_and_Scientific`,
`Beauty_and_Personal_Care`, `Musical_Instruments`, `Books`.

## Quick start

Requirements: **Python 3.8+**, the `huggingface_hub` package, and the system
`curl` (used for resumable, stall-resistant download of the large metadata
files; Books metadata alone is ~14 GB raw).

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# process all 5 categories, both max lengths (writes ./processed)
python process_amazon2023.py

# a single category, only maxlen 50, skip metadata
python process_amazon2023.py --categories Video_Games --maxlens 50 --no-meta
```

Useful flags: `--categories`, `--maxlens`, `--no-meta`, `--no-validate`,
`--from-5core-cats` (process the very large categories from the official
pre-filtered 5-core data to save memory — the default for `Books` and
`Beauty_and_Personal_Care`).

## Output (`./processed/`)

```
interactions/<Category>.jsonl              # 5-core interactions
last_out/<Category>.{train,valid,test}.jsonl   # leave-one-out, direct
seq_maxlen20/<Category>.{train,valid,test}.jsonl   # sequential, history <= 20
seq_maxlen50/<Category>.{train,valid,test}.jsonl   # sequential, history <= 50
item_meta/<Category>.jsonl                 # item content features
stats.json   stats.md                      # statistics + validation report
```

Record formats:

```jsonc
// interactions / last_out
{"user_id": "...", "parent_asin": "B09JY72CNG", "rating": 4.0, "timestamp": 1630594913298}

// seq_maxlen20 / seq_maxlen50  (history = prior items, chronological, capped)
{"user_id": "...", "parent_asin": "B09JY72CNG", "rating": 4.0,
 "timestamp": 1630594913298, "history": ["B08R5B7YS4", "B0863MT183", "..."]}

// item_meta  (join by parent_asin; `details` is a JSON-encoded string)
{"parent_asin": "B00Z9TLVK0", "title": "...", "price": 58.0, "store": "2K",
 "categories": ["..."], "images": [{"thumb": "...", "large": "...", "hi_res": "...", "variant": "MAIN"}],
 "features": ["..."], "description": ["..."], "details": "{...}"}
```

Sequential `train` uses the standard rolling next-item scheme: each user's
sequence `[i1..in]` yields training rows `predict i2 from [i1]`,
`predict i3 from [i1,i2]`, … ; the last two items are held out for
`validation` / `test`. (`#train rows = #interactions − 3 × #users`.)

## Notes

- **Data is not committed to this repo** (it lives on the Hub). Re-run the script
  to regenerate it locally into `./processed/`.
- Implicit feedback by default (all retained reviews are positives; use `rating`
  for explicit labels). No leakage by construction (test = each user's last
  item).

## License & citation

Derived from **Amazon Reviews 2023** (McAuley Lab); for research use. Please cite:

> Yupeng Hou, Jiacheng Li, Zhankui He, An Yan, Xiusi Chen, Julian McAuley.
> *Bridging Language and Items for Retrieval and Recommendation.* 2024.
> [arXiv:2403.03952](https://arxiv.org/abs/2403.03952) ·
> https://amazon-reviews-2023.github.io/

> Shashank Rajput et al. *Recommender Systems with Generative Retrieval (TIGER).*
> NeurIPS 2023. [arXiv:2305.05065](https://arxiv.org/abs/2305.05065)
