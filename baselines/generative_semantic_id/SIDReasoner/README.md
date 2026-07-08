# SIDReasoner — Reasoning over Semantic IDs for Generative Recommendation

Official implementation of **"Reasoning over Semantic IDs Enhances Generative
Recommendation"** ([arXiv:2603.23183](https://arxiv.org/abs/2603.23183)).

SIDReasoner teaches a generative recommender to **think in natural language over
Semantic IDs (SIDs)** before it recommends. A single Qwen3-1.7B backbone is
aligned so that a compact `<a_i><b_j><c_k>` SID and its underlying item
semantics become interchangeable — the model can read an interaction history in
SID space, reason about the user's intent in plain language, and then decode the
next item as a valid SID. Data streams straight from the Hub; there is no local
dataset to prepare.

> **TL;DR recipe.** Qwen3-1.7B backbone · 3-token RK-Means SIDs · **three
> stages**: (1) SID↔language *alignment SFT* over 8 complementary tasks →
> (2) *reasoning activation* SFT on interleaved SID-text narratives →
> (3) *GRPO RL* with a rule-based recommendation reward. Evaluate in
> **thinking mode**: vLLM drafts the reasoning trace, then constrained beam
> search (beam 10) decodes a catalog-valid SID.

---

## Contents

- [Highlights](#highlights)
- [Repository layout](#repository-layout)
- [How it works](#how-it-works)
- [Quickstart](#quickstart)
- [Data](#data-from-the-hub)
- [Training](#training)
- [Evaluation](#evaluation)
- [Results](#results)
- [Checkpoints](#checkpoints)
- [Citation](#citation)

---

## Highlights

- **Reasoning that ends in a valid item.** The model produces a free-form
  `<think>…</think>` trace, then decodes an SID under a prefix trie so every
  recommendation is guaranteed to exist in the catalog.
- **Alignment-first.** Stage 1 mixes 8 tasks that tie SIDs to titles and text in
  both directions, so reasoning has real semantics to work with.
- **Academic-scale.** Everything runs on a single 4–8 GPU node with a 1.7B model
  and public Amazon-2023 categories.
- **Zero data prep.** All splits, item catalogs and RL prompts load from
  [`yufan/recsys-genrec-dataset`](https://huggingface.co/datasets/yufan/recsys-genrec-dataset)
  through one helper, [`hf_data.py`](hf_data.py).

---

## Repository layout

```text
SIDReasoner/
├── hf_data.py                     # single entry point for all HF dataset access
├── data_Qwen3.py                  # every Dataset class (alignment, reasoning, eval)
├── phase1_alignment_sft/          # Stage 1 — SID ↔ language alignment SFT
│   ├── sft_Qwen3.py
│   └── sft_Qwen3_enrich.sh
├── phase2_reasoning_activation/   # Stage 2 — reasoning activation SFT
│   ├── sft_reasoning_activation.py
│   └── sft_reasoning_activation.sh
├── phase3_rl/                     # Stage 3 — GRPO RL (built on VERL)
│   ├── RL_training_script.sh
│   ├── create_reasoning_rl_data.py
│   └── merge_fsdp_checkpoint.py   # FSDP shards → HF `actor_merged`
├── evaluation/                    # split → generate → merge → score
│   ├── evaluate_Qwen3.py / .sh          # non-thinking mode
│   ├── evaluate_Qwen3_think.py / .sh    # thinking mode (vLLM + constrained beam)
│   ├── split.py / merge.py / calc.py
├── verl/                          # vendored VERL RL trainer
├── scripts/install_vllm_sglang_mcore.sh
└── requirements.txt
```

---

## How it works

Three training stages produce one model; evaluation is two-pass.

**Stage 1 — SID ↔ language alignment (SFT).** Eight complementary tasks are
concatenated so the model learns to translate freely between SIDs, titles and
descriptions, and to do sequence recommendation in every representation:

| # | Task (input → output) | What it teaches |
|--:|---|---|
| 1 | SID history → next SID | recommendation in SID space |
| 2 | Title ↔ SID (both directions) | bidirectional item translation |
| 3 | SID history → next Title | fusion sequence recommendation |
| 4 | Title history → next Title | text-only sequence recommendation |
| 5 | Title history → next SID | cross-representation recommendation |
| 6 | Item narrative with SIDs | item-level SID-text interleaving |
| 7 | User-sequence narrative with SIDs | sequence-level SID-text interleaving |
| 8 | General reasoning | preserve base reasoning ability |

**Stage 2 — reasoning activation (SFT).** Fine-tune on interleaved
SID-and-text narratives so the model starts *explaining* a recommendation before
emitting it, producing coherent `<think>` traces grounded in SID semantics.

**Stage 3 — reinforcement learning (GRPO).** Optimize the reasoning policy with
[VERL](https://github.com/volcengine/verl) using a **rule-based recommendation
reward** that scores whether the reasoned-out SID matches the ground-truth next
item. Output is an FSDP checkpoint; merge it into an HF model (`actor_merged`).

**Evaluation (thinking mode).** Two generators, each doing what it is best at:

1. **vLLM** greedily drafts the reasoning trace (`temperature=0`), truncated at
   `</think>`.
2. **Hugging Face `generate`** runs **beam search (beam 10)** with a
   `prefix_allowed_tokens_fn` over a trie of all catalog SIDs, so the top-K
   decoded SIDs are always valid items — scored with NDCG@K / HR@K.

---

## Quickstart

### Install

```bash
pip install -r requirements.txt
# RL (Stage 3) + thinking-mode eval need a CUDA-matched vLLM/VERL stack:
bash scripts/install_vllm_sglang_mcore.sh
```

> **Note.** vLLM 0.8.5 is built for `torch 2.6.0+cu124` (pre-CXX11 ABI). If
> `import vllm` fails with an `undefined symbol … parseSchemaOrName …` error,
> your Torch is ABI-mismatched — reinstall the matched wheel:
> `pip install "torch==2.6.0" "torchvision==0.21.0" "torchaudio==2.6.0" --index-url https://download.pytorch.org/whl/cu124`.

### Categories

Three Amazon-2023 categories are supported out of the box — set `CATEGORY` at the
top of any stage/eval script:

`Video_Games` · `Office_Products` · `Industrial_and_Scientific`

---

## Data (from the Hub)

All training and evaluation data loads **at runtime** from
[`yufan/recsys-genrec-dataset`](https://huggingface.co/datasets/yufan/recsys-genrec-dataset)
via [`hf_data.py`](hf_data.py) — no manual download, no `./data/Amazon` folder.

The file paths that remain in the scripts are only **locators**: `hf_data.py`
parses the category (and split) out of them and maps to the right HF config, so
you never have to change a shell argument.

| Legacy file (locator) | Hugging Face config |
| --- | --- |
| `train/valid/test/<cat>_5_*.csv` | `<cat>_seqrec` |
| `index/<cat>.item.json`, `index/<cat>.index.json`, `index/<cat>.item_enhanced_v2.json`, `info/<cat>_5_*.txt` | `<cat>_catalog` |
| `index/<cat>.integrated_narrative.csv` | `<cat>_reasoning` |
| `rec_reasoning_verl/<cat>/*.parquet` | `<cat>_rl` |
| `general/sampled_data.arrow` | `general_reasoning` |

- Point at a fork with `export SIDR_HF_REPO=<your-org>/<your-dataset>`.
- Prefer local files? The original archive is
  [available here](https://drive.google.com/file/d/1etg1e8oStGOjsg1Vr15vFnjlTMUx4Htz/view?usp=sharing).

---

## Training

Run the three stages in order. Each writes logs to `./logs` and checkpoints to
`./output_dir` (Stages 1–2) or `./checkpoints` (Stage 3).

```bash
# Stage 1 — SID ↔ language alignment SFT      (4 GPUs, Qwen3-1.7B)
bash phase1_alignment_sft/sft_Qwen3_enrich.sh

# Stage 2 — reasoning activation SFT          (resumes from Stage 1)
bash phase2_reasoning_activation/sft_reasoning_activation.sh

# Stage 3 — GRPO RL via VERL                  (resumes from Stage 2)
bash phase3_rl/RL_training_script.sh
```

| Stage | Objective | Backbone / resume | Default hardware |
|---|---|---|---|
| 1 | Alignment SFT (8 tasks) | `Qwen/Qwen3-1.7B` | 4× GPU, `torchrun` |
| 2 | Reasoning activation SFT | Stage-1 `final_checkpoint` | 4× GPU, `torchrun` |
| 3 | GRPO RL (rule-based reward) | Stage-2 `final_checkpoint` | 4× GPU, VERL |

### Stage-1 throughput / memory

Measured on Stage-1 alignment SFT (Qwen3-1.7B, bf16, ZeRO-2). `GC` = gradient
checkpointing; `bs` = per-GPU micro-batch. Peak memory is per-GPU; throughput is
global (tokens/s across the run).

| Config | Peak memory | Per step | Global tok/s |
|---|---|---|---|
| GC off, bs4 | 70.6 GiB | 5377 ms | 10,922 |
| GC on, bs4  | 32.5 GiB | 5583 ms | 10,519 |
| GC on, bs8  | 58.4 GiB | 7457 ms | 19,720 |

- **Gradient checkpointing is nearly free.** At `bs4` it cuts peak memory by more
  than half (70.6 → 32.5 GiB) for only ~4% slower steps (~4% lower tok/s).
- **Spend the freed memory on batch size.** With GC on, `bs8` fits in 58.4 GiB
  (< 80 GB) and nearly doubles throughput (10.5k → 19.7k tok/s) despite longer
  steps — so **GC on + bs8** is the throughput-optimal setting on an 80 GB GPU.

### Merge a Stage-3 checkpoint

Thinking-mode evaluation expects a merged HF checkpoint named `actor_merged`.
If RL produced raw FSDP `actor/` shards, merge them first:

```bash
python3 ./phase3_rl/merge_fsdp_checkpoint.py \
  --checkpoint ./checkpoints/RecRL_Reasoning/<run>/global_step_<N>/actor \
  --output-dir ./checkpoints/RecRL_Reasoning/<run>/global_step_<N>/actor_merged
```

---

## Evaluation

```bash
# Thinking mode — vLLM reasoning trace + constrained beam-search SID decoding
bash evaluation/evaluate_Qwen3_think.sh

# Non-thinking mode — direct constrained SID decoding
bash evaluation/evaluate_Qwen3.sh
```

Each script splits the test set across the listed GPUs, generates in parallel,
merges the shards, and reports **NDCG@{1,3,5,10}** and **HR@{1,3,5,10}**.
Results land in `./results/<run>/`.

---

## Results

### Reported in the paper (Table 2)

Numbers as published in **"Reasoning over Semantic IDs Enhances Generative
Recommendation"** (KDD 2026, [arXiv:2603.23183](https://arxiv.org/abs/2603.23183)).
All methods use the same protocol: **full-item ranking**, temporal 8:1:1 split,
maximum history length 10. `R` is Recall, `N` is NDCG; **best per column in bold**.
SIDReasoner is the strongest method across every metric on all three datasets.

**Video Games**
| Method | R@5 | N@5 | R@10 | N@10 |
|---|---:|---:|---:|---:|
| Caser | 0.0376 | 0.0241 | 0.0659 | 0.0332 |
| GRU4Rec | 0.0329 | 0.0219 | 0.0599 | 0.0305 |
| SASRec | 0.0501 | 0.0345 | 0.0723 | 0.0416 |
| TIGER | 0.0489 | 0.0300 | 0.0763 | 0.0402 |
| HSTU | 0.0539 | 0.0396 | 0.0746 | 0.0462 |
| LETTER | 0.0445 | 0.0294 | 0.0709 | 0.0378 |
| LC-Rec | 0.0441 | 0.0274 | 0.0876 | 0.0412 |
| ReaRec | 0.0568 | 0.0381 | 0.0843 | 0.0470 |
| R²ec | 0.0655 | 0.0399 | 0.0931 | 0.0525 |
| **SIDReasoner** | **0.0710** | **0.0460** | **0.1031** | **0.0563** |

**Office Products**
| Method | R@5 | N@5 | R@10 | N@10 |
|---|---:|---:|---:|---:|
| Caser | 0.0880 | 0.0663 | 0.1114 | 0.0738 |
| GRU4Rec | 0.0682 | 0.0480 | 0.0974 | 0.0574 |
| SASRec | 0.1019 | 0.0824 | 0.1167 | 0.0871 |
| TIGER | 0.1270 | 0.1037 | 0.1429 | 0.1121 |
| HSTU | 0.1204 | 0.1069 | 0.1323 | 0.1107 |
| LETTER | 0.1315 | 0.1074 | 0.1520 | 0.1139 |
| LC-Rec | 0.0964 | 0.0699 | 0.1487 | 0.0867 |
| ReaRec | 0.1173 | 0.0988 | 0.1385 | 0.1057 |
| R²ec | 0.1147 | 0.0894 | 0.1486 | 0.1004 |
| **SIDReasoner** | **0.1373** | **0.1119** | **0.1648** | **0.1208** |

**Industrial and Scientific**
| Method | R@5 | N@5 | R@10 | N@10 |
|---|---:|---:|---:|---:|
| Caser | 0.0664 | 0.0528 | 0.0852 | 0.0588 |
| GRU4Rec | 0.0788 | 0.0578 | 0.1030 | 0.0649 |
| SASRec | 0.0807 | 0.0647 | 0.0964 | 0.0697 |
| TIGER | 0.1003 | 0.0823 | 0.1325 | 0.0924 |
| HSTU | 0.1008 | 0.0898 | 0.1138 | 0.0940 |
| LETTER | 0.1080 | 0.0850 | 0.1389 | 0.0950 |
| LC-Rec | 0.0805 | 0.0520 | 0.1330 | 0.0687 |
| ReaRec | 0.0973 | 0.0796 | 0.1205 | 0.0870 |
| R²ec | 0.0880 | 0.0774 | 0.1253 | 0.0774 |
| **SIDReasoner** | **0.1109** | **0.0905** | **0.1438** | **0.1010** |

### Our reproduction

Reproduced with the released per-domain Stage-3 checkpoints (`actor_merged`),
**thinking mode**, full test set, `num_beams=10`, `max_new_tokens=1024`,
`temperature=0` (greedy, deterministic). Every decoded SID was catalog-valid
(0 invalid generations). Because a single item is held out per user, **HR@K equals
Recall@K**, so these numbers are directly comparable to the paper's Table 2 above —
and the reproduction closely matches the reported SIDReasoner results.

**Video_Games** — 6,142 test users
| Metric | @1 | @3 | @5 | @10 |
|---|---:|---:|---:|---:|
| NDCG | 0.0217 | 0.0346 | 0.0456 | 0.0554 |
| HR | 0.0217 | 0.0444 | 0.0715 | 0.1018 |

**Office_Products** — 4,866 test users
| Metric | @1 | @3 | @5 | @10 |
|---|---:|---:|---:|---:|
| NDCG | 0.0824 | 0.1026 | 0.1110 | 0.1193 |
| HR | 0.0824 | 0.1169 | 0.1377 | 0.1636 |

**Industrial_and_Scientific** — 4,533 test users
| Metric | @1 | @3 | @5 | @10 |
|---|---:|---:|---:|---:|
| NDCG | 0.0708 | 0.0834 | 0.0905 | 0.1010 |
| HR | 0.0708 | 0.0927 | 0.1101 | 0.1427 |

---

## Checkpoints

Pretrained per-domain checkpoints are released on the
[SIDReasoner-Models Hub](https://huggingface.co/Sober-Clever/SIDReasoner-Models/tree/main).
Point `evaluate_Qwen3_think.sh` at a domain's `actor_merged` folder to reproduce
the numbers above.

---

## Citation

```bibtex
@article{SIDReasoner,
  title={Reasoning over Semantic IDs Enhances Generative Recommendation},
  author={Yingzhi He and Yan Sun and Junfei Tan and Yuxin Chen and Xiaoyu Kong and Chunxu Shen and Xiang Wang and An Zhang and Tat-Seng Chua},
  journal={arXiv preprint arXiv:2603.23183},
  year={2026}
}
```

## Acknowledgement

Built upon [MiniOneRec](https://github.com/AkaliKong/MiniOneRec); the RL stage
uses [VERL](https://github.com/volcengine/verl).
