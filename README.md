<div align="center">

# 📚 RecSys Summer

### A survey of **2025–2026** recommender-systems papers, mapped to the **top-30** most-used evaluation datasets

![Papers](https://img.shields.io/badge/papers-2041-1f6feb?style=flat-square) ![Years](https://img.shields.io/badge/2025--2026-corpus-8957e5?style=flat-square) ![Top datasets](https://img.shields.io/badge/top__eval__datasets-30-fb8500?style=flat-square) ![Amazon-2023](https://img.shields.io/badge/Amazon_2023-132_papers-ff9f1c?style=flat-square) ![With code](https://img.shields.io/badge/with__code-72%2F132-2ea043?style=flat-square) ![Data](https://img.shields.io/badge/full_set-Hugging_Face-ffce00?style=flat-square)

</div>

---

A curated map of where recent recommender-systems research is evaluated. Starting from the full **2025–2026 corpus of 2,041 papers**, we keep the **top-30 most-used evaluation datasets** and group papers by the datasets they use in **experiments** — **1,141** of the 2,041 papers use at least one top-30 dataset (the rest evaluate only on rarer sets). A deep dive then covers the **Amazon Reviews 2023** subset — its baselines, product categories, and data-processing recipes.

> **📦 Want every paper?** All 2025–2026 papers — PDFs + metadata — live on Hugging Face: **[`yufan/recsys-papers-2025-2026`](https://huggingface.co/datasets/yufan/recsys-papers-2025-2026)**.

---

## Contents

1. [At a glance](#at-a-glance)
2. [Top 30 evaluation datasets](#1--top-30-evaluation-datasets)
3. [Amazon-2023 · baselines by family](#2--amazon-2023--baselines-by-method-family)
4. [Amazon-2023 · product categories](#3--amazon-2023--product-categories)
5. [Amazon-2023 · data processing](#4--amazon-2023--data-processing)
6. [Amazon-2023 · GPU setups](#5--amazon-2023--gpu-setups)
7. [Amazon-2023 · code availability](#6--amazon-2023--code-availability)
8. [Methodology](#methodology)

---

## At a glance

| | |
|---|---|
| 📚 **Papers · 2025–2026 corpus** | 2,041 |
| 🗂️ **Papers using a top-30 dataset** | 1,141 |
| 📊 **Top-30 evaluation datasets** | 30 |
| 🛒 **Amazon-2023 papers** | 132 |
| 🧩 **Distinct baselines (Amazon-2023)** | 517 |
| 🏷️ **Amazon categories used** | 29 |
| 💻 **Amazon-2023 papers with public code** | 72 / 132 |

---

## 1 · Top 30 evaluation datasets

The **30 most-used** evaluation datasets across the 2,041-paper 2025–2026 corpus, ranked by the number of papers that use each in experiments (a paper may appear under several).

| # | Dataset | Papers | |
|---:|---|---:|:--|
| 1 | **MovieLens** | 397 | `████████████████` |
| 2 | **Amazon-2014** | 302 | `████████████····` |
| 3 | **Yelp** | 208 | `████████········` |
| 4 | **Amazon-2018** | 150 | `██████··········` |
| 5 | **Amazon-2023** | 132 | `█████···········` |
| 6 | **LastFM** | 82 | `███·············` |
| 7 | **Gowalla** | 60 | `██··············` |
| 8 | **Steam** | 51 | `██··············` |
| 9 | **KuaiRand** | 43 | `██··············` |
| 10 | **MIND** | 36 | `█···············` |
| 11 | **ReDial** | 33 | `█···············` |
| 12 | **Taobao** | 33 | `█···············` |
| 13 | **Foursquare** | 32 | `█···············` |
| 14 | **Goodreads** | 32 | `█···············` |
| 15 | **Tmall** | 29 | `█···············` |
| 16 | **Douban** | 24 | `█···············` |
| 17 | **RetailRocket** | 23 | `█···············` |
| 18 | **Book-Crossing** | 21 | `█···············` |
| 19 | **INSPIRED** | 21 | `█···············` |
| 20 | **Netflix** | 21 | `█···············` |
| 21 | **KuaiRec** | 20 | `█···············` |
| 22 | **MicroLens** | 20 | `█···············` |
| 23 | **Criteo** | 19 | `█···············` |
| 24 | **Epinions** | 15 | `█···············` |
| 25 | **Avazu** | 14 | `█···············` |
| 26 | **Tenrec** | 14 | `█···············` |
| 27 | **Ciao** | 12 | `················` |
| 28 | **MillionSongDataset** | 11 | `················` |
| 29 | **Alibaba-iFashion** | 10 | `················` |
| 30 | **KuaiSAR** | 10 | `················` |

---

## 2 · Amazon-2023 · baselines by method family

The 132 Amazon-2023 papers compare against **517 distinct baselines**. Here they are merged into method families. *Family of every baseline was assigned by method type; grouping is best-effort and some methods straddle families.*

### 2.1 · Frequency by family

“Papers” = distinct papers using **≥ 1** baseline from that family (so columns sum to more than 132).

| Method family | Papers | Share | |
|---|---:|---:|:--|
| **Sequential / session-based** | 64 | 50% | `████████████████` |
| **Generative retrieval / semantic-ID** | 43 | 33% | `███████████·····` |
| **LLM-based recommenders** | 41 | 32% | `██████████······` |
| **Classical CF · MF, neighborhood, neural CF** | 34 | 26% | `████████········` |
| **Text- & multimodal-enhanced** | 34 | 26% | `████████········` |
| **Graph-based CF** | 19 | 15% | `█████···········` |
| **General-purpose LLMs · zero-shot / prompted** | 18 | 14% | `████············` |
| **CTR / feature-interaction** | 6 | 5% | `█···············` |
| **Other / specialized** | 65 | 50% | `████████████████` |

_Based on 129/132 papers that report baselines._

### 2.2 · Baselines in each family

Baselines used by **≥ 2 papers** (paper count in parentheses); a long tail of **423** further baselines appears once each.

<details open>
<summary><b>Sequential / session-based</b> — 64 papers</summary>

`SASRec` (55) · `GRU4Rec` (29) · `BERT4Rec` (27) · `Caser` (15) · `FMLP-Rec` (11) · `S3-Rec` (10) · `DuoRec` (8) · `FDSA` (8) · `HGN` (4) · `CL4SRec` (3) · `NextItNet` (3) · `MAERec` (3) · `SASRec Base` (2) · `BERT4Rec Base` (2) · `FEARec` (2) · `DiffuRec` (2) · `CoST` (2) · `LRURec` (2) · `CORE` (2) · `BSARec` (2) · `ReaRec` (2)

</details>

<details open>
<summary><b>Generative retrieval / semantic-ID</b> — 43 papers</summary>

`TIGER` (23) · `HSTU` (13) · `LETTER` (11) · `LCRec` (8) · `VQ-Rec` (7) · `P5` (4) · `MiniOneRec` (3) · `ETEGRec` (3) · `ActionPiece` (3) · `P5-CID` (2) · `RK-Means` (2) · `GenRec` (2)

</details>

<details open>
<summary><b>LLM-based recommenders</b> — 41 papers</summary>

`S-DPO` (7) · `TALLRec` (7) · `BIGRec` (6) · `LLaRA` (6) · `D3` (5) · `RLMRec` (4) · `AlphaRec` (4) · `LLMRank` (3) · `AgentCF` (3) · `KAR` (3) · `RLMRec-Con` (3) · `RLMRec-Gen` (3) · `InteRecAgent` (3) · `R2ec` (3) · `LLMInit` (2) · `LLM-ESR` (2) · `Chat-Rec` (2) · `Rec-R1` (2) · `LLM-Rec` (2) · `LlamaRec` (2)

</details>

<details open>
<summary><b>Classical CF · MF, neighborhood, neural CF</b> — 34 papers</summary>

`Popularity` (9) · `MF` (7) · `NCF` (5) · `BPR-MF` (5) · `BPR` (4) · `DMF` (2) · `SVD` (2) · `ALS` (2) · `ItemKNN` (2) · `NeuMF` (2)

</details>

<details open>
<summary><b>Text- & multimodal-enhanced</b> — 34 papers</summary>

`UniSRec` (11) · `RecFormer` (6) · `MoRec` (4) · `BM25` (4) · `VBPR` (3) · `BLAIR-BASE` (3) · `TedRec` (3) · `QARM` (2) · `BLAIR-LARGE` (2)

</details>

<details open>
<summary><b>Graph-based CF</b> — 19 papers</summary>

`LightGCN` (15) · `NGCF` (3) · `SimGCL` (2)

</details>

<details open>
<summary><b>General-purpose LLMs · zero-shot / prompted</b> — 18 papers</summary>

`GPT-4o` (4) · `GPT-4o-mini` (3) · `GPT4` (2) · `Claude 3.5 Haiku` (2) · `Gemini 2.5 Flash` (2) · `GPT-3.5-Turbo` (2)

</details>

<details open>
<summary><b>CTR / feature-interaction</b> — 6 papers</summary>

`DIN` (3) · `CTRL` (2)

</details>

<details>
<summary><b>Other / specialized</b> — 65 papers</summary>

`Centric` (3) · `Temp-Fusion` (3) · `Random` (3) · `Retrain` (3) · `FairRec` (2) · `UniCDR` (2) · `Zero-shot` (2) · `ERL` (2) · `PRL` (2) · `ReRe` (2) · `LatentR3` (2)

</details>

---

## 3 · Amazon-2023 · product categories

Amazon product categories used as evaluation domains across the 132 papers.

| Category | Papers | |
|---|---:|:--|
| Video Games | 51 | `████████████████` |
| Industrial & Scientific | 29 | `█████████·······` |
| Beauty | 28 | `█████████·······` |
| Musical Instruments | 27 | `████████········` |
| Books | 27 | `████████········` |
| Sports & Outdoors | 22 | `███████·········` |
| Movies & TV | 22 | `███████·········` |
| CDs & Vinyl | 21 | `███████·········` |
| Electronics | 20 | `██████··········` |
| Office Products | 19 | `██████··········` |
| Clothing, Shoes & Jewelry | 18 | `██████··········` |
| Toys & Games | 18 | `██████··········` |
| Baby Products | 16 | `█████···········` |
| Home & Kitchen | 12 | `████············` |
| Grocery & Gourmet Food | 12 | `████············` |
| Amazon Fashion | 10 | `███·············` |
| Health & Household | 9 | `███·············` |
| Software | 8 | `███·············` |
| Arts, Crafts & Sewing | 7 | `██··············` |
| Cell Phones & Accessories | 7 | `██··············` |
| Digital Music | 5 | `██··············` |
| Pet Supplies | 5 | `██··············` |
| Automotive | 4 | `█···············` |
| Magazine Subscriptions | 4 | `█···············` |
| Tools & Home Improvement | 4 | `█···············` |
| Kindle Store | 2 | `█···············` |
| Subscription Boxes | 1 | `················` |
| Appliances | 1 | `················` |
| Patio, Lawn & Garden | 1 | `················` |

---

## 4 · Amazon-2023 · data processing

### Overall — how the field processes Amazon-2023

Of the **131/132** papers that describe their pipeline, the recurring recipe is: take a handful of product categories, apply **k-core filtering** (most often **5-core**) to drop sparse users/items, order each user’s interactions **chronologically**, and hold out the **last interaction for testing** (leave-one-out) — capping sequences at a fixed length and pairing IDs with **item text** (title, description, brand) for modern text/LLM models. Common ingredients:

| Processing step | Papers (of described) | |
|---|---:|:--|
| Chronological / temporal split | 60 (45%) | `████████████████` |
| Leave-one-out split | 44 (33%) | `████████████····` |
| Text / title / metadata features | 40 (30%) | `███████████·····` |
| 5-core filtering | 33 (25%) | `█████████·······` |
| Max sequence-length cap | 27 (20%) | `███████·········` |
| Negative sampling | 17 (12%) | `█████···········` |
| Ratio split (e.g. 8:1:1) | 15 (11%) | `████············` |
| Rating binarization / implicit | 13 (9%) | `███·············` |
| Image / visual features | 13 (9%) | `███·············` |
| Min interactions / threshold | 10 (7%) | `███·············` |

> Per-paper recipes (all 132, with arXiv links) are in **[`Amazon-2023_Data_Processing.md`](Amazon-2023_Data_Processing.md)**.

---

## 5 · Amazon-2023 · GPU setups

Hardware is reported by **73/132** papers. Top-5 setups (cards × model):

| GPU setup | Papers | |
|---|---:|:--|
| **1× A100** | 7 | `████████████████` |
| **1× RTX A6000** | 6 | `██████████████··` |
| **4× A100** | 5 | `███████████·····` |
| **8× A100** | 4 | `█████████·······` |
| **4× A800** | 3 | `███████·········` |

_**A100** is the workhorse — one card for fine-tuning, 4–8× for pre-training; **RTX A6000 / 3090** cover smaller setups._

---

## 6 · Amazon-2023 · code availability

**72 / 132** Amazon-2023 papers release a *working* public code repository — a GitHub/GitLab repo or an anonymized review repo (`anonymous.4open.science`). The remaining 60 ship no code, only release data/model/demo artifacts, promise code upon acceptance, or list a link that is currently broken/empty/expired.

| | Papers | |
|---|---:|:--|
| **Public code** | 72 | `████████████████` |
| **No public code** | 60 | `█████████████···` |

> Per-paper links — **paper · arXiv · code** for all 77 — are in **[`Amazon-2023_Code.md`](Amazon-2023_Code.md)**.

---

## Methodology

- **Dataset frequencies** — PDF counts under each `Freq_<count>_<dataset>` folder; a paper appears under every dataset it uses.
- **Baselines & categories** — aggregated from per-paper analyses of the 132 Amazon-2023 papers; each paper counted once per distinct baseline/category. Spelling/abbreviation variants were consolidated.
- **Method-family grouping** — each baseline labelled by method type; best-effort, and a few methods span families.
- **Data processing** — condensed from each paper’s reported preprocessing; “described” excludes papers that omit a pipeline.
- **Code availability** — detected from PDF hyperlinks and “code/implementation available” statements; a paper counts only when it links its **own** public repo (GitHub/GitLab or an anonymized review repo). Baseline/library/model links and data-, model- or demo-only artifacts are excluded.


<div align="center"><sub>Full corpus · <a href="https://huggingface.co/datasets/yufan/recsys-papers-2025-2026">Hugging Face: yufan/recsys-papers-2025-2026</a></sub></div>
