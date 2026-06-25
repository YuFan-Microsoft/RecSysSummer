<div align="center">

# 🧪 Baselines

### Reproduction-code homes for every Amazon-2023 baseline, grouped by method family

</div>

---

A working area for **running and re-implementing the baselines** that the 132 Amazon-2023 papers compare against. The taxonomy here mirrors the method families in [`../docs/Amazon-2023_Baselines_Code.md`](../docs/Amazon-2023_Baselines_Code.md) — one subfolder per family. Each family `README.md` lists its baselines with the **single most-reliable code path** (priority **official repo → runs on Amazon-2023 → runs on other data**) and the practical route to run it on Amazon-2023.

> **Drop code here.** Put each baseline's implementation / adapter / config in a subfolder under its family, e.g. `sequential_session_based/SASRec/`. Keep heavy artifacts (checkpoints, embeddings, datasets) out of git — pull data via [`../amazon_2023/`](../amazon_2023/).

## Families

Ordered by the number of Amazon-2023 papers that use **≥ 1** baseline from the family (see [`../README.md` §2.1](../README.md#21--frequency-by-family)).

| Family | Papers | Baselines | Code strategy |
|---|---:|---:|---|
| [`sequential_session_based/`](sequential_session_based/) | 64 | 19 | Mostly **RecBole** `--model=X`; a few need adapters |
| [`generative_semantic_id/`](generative_semantic_id/) | 43 | 12 | Each method's **own repo**; TIGER/RK-Means via **GRID** |
| [`llm_based/`](llm_based/) | 41 | 20 | Each method's **own repo** (LoRA / RL / API) |
| [`classical_cf/`](classical_cf/) | 34 | 10 | **RecBole** + libraries (`cornac`, `implicit`) |
| [`text_multimodal/`](text_multimodal/) | 34 | 9 | **RecBole**-family + libraries; text emb via **BLAIR** |
| [`graph_cf/`](graph_cf/) | 19 | 3 | **RecBole-GNN** / official repos |
| [`general_purpose_llms/`](general_purpose_llms/) | 18 | 6 | **API-only** (no training) — prompt code only |
| [`ctr_feature_interaction/`](ctr_feature_interaction/) | 6 | 2 | **RecBole** `DIN`; CTRL reimplemented |

## How to use

1. **Start from the McAuley-Lab benchmark** — [`hyp1231/AmazonReviews2023`](https://github.com/hyp1231/AmazonReviews2023) already converts Amazon-2023 into RecBole atomic files (+ BLAIR text embeddings). ~23 classical / sequential / graph baselines run by swapping `--model=X`.
2. **For generative / LLM methods**, clone the baseline's own repo (linked in each family README) and point it at the Amazon-2023 splits produced by [`../amazon_2023/process_amazon2023.py`](../amazon_2023/process_amazon2023.py).
3. **Keep the protocol fixed** — official 5-core / `last_out` split, full-ranking eval, Recall@K & NDCG@K (K ∈ {5, 10}); see [`../amazon_2023/Amazon-2023_Data_Processing_Protocol.md`](../amazon_2023/Amazon-2023_Data_Processing_Protocol.md).

## Suggested per-baseline layout

```
baselines/<family>/<Baseline>/
├── README.md      # source repo, commit, what was changed for 2023
├── run.sh         # exact command(s) to reproduce
├── config/        # dataset + model configs
└── (code / submodule / adapter)
```

---

<div align="center"><sub>Taxonomy & code paths from <a href="../docs/Amazon-2023_Baselines_Code.md">Amazon-2023_Baselines_Code.md</a> · corpus on <a href="https://huggingface.co/datasets/yufan/recsys-papers-2025-2026">Hugging Face</a></sub></div>
