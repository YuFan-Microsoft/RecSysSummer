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

[`SASRec`](https://arxiv.org/abs/1808.09781) (55) · [`GRU4Rec`](https://arxiv.org/abs/1511.06939) (29) · [`BERT4Rec`](https://arxiv.org/abs/1904.06690) (27) · [`Caser`](https://arxiv.org/abs/1809.07426) (15) · [`FMLP-Rec`](https://arxiv.org/abs/2202.13556) (11) · [`S3-Rec`](https://arxiv.org/abs/2008.07873) (10) · [`DuoRec`](https://arxiv.org/abs/2110.05730) (8) · `FDSA` (8) · [`HGN`](https://arxiv.org/abs/1906.09217) (4) · [`CL4SRec`](https://arxiv.org/abs/2010.14395) (3) · [`NextItNet`](https://arxiv.org/abs/1808.05163) (3) · [`MAERec`](https://arxiv.org/abs/2305.04619) (3) · [`SASRec Base`](https://arxiv.org/abs/1808.09781) (2) · [`BERT4Rec Base`](https://arxiv.org/abs/1904.06690) (2) · [`FEARec`](https://arxiv.org/abs/2304.09184) (2) · [`DiffuRec`](https://arxiv.org/abs/2304.00686) (2) · [`CoST`](https://arxiv.org/abs/2404.14774) (2) · [`LRURec`](https://arxiv.org/abs/2310.02367) (2) · [`CORE`](https://arxiv.org/abs/2204.11067) (2) · [`BSARec`](https://arxiv.org/abs/2312.10325) (2) · [`ReaRec`](https://arxiv.org/abs/2503.22675) (2)

</details>

<details open>
<summary><b>Generative retrieval / semantic-ID</b> — 43 papers</summary>

[`TIGER`](https://arxiv.org/abs/2305.05065) (23) · [`HSTU`](https://arxiv.org/abs/2402.17152) (13) · [`LETTER`](https://arxiv.org/abs/2405.07314) (11) · [`LCRec`](https://arxiv.org/abs/2311.09049) (8) · [`VQ-Rec`](https://arxiv.org/abs/2210.12316) (7) · [`P5`](https://arxiv.org/abs/2203.13366) (4) · [`MiniOneRec`](https://arxiv.org/abs/2510.24431) (3) · [`ETEGRec`](https://arxiv.org/abs/2409.05546) (3) · [`ActionPiece`](https://arxiv.org/abs/2502.13581) (3) · [`P5-CID`](https://arxiv.org/abs/2305.06569) (2) · `RK-Means` (2) · [`GenRec`](https://arxiv.org/abs/2307.00457) (2)

</details>

<details open>
<summary><b>LLM-based recommenders</b> — 41 papers</summary>

[`S-DPO`](https://arxiv.org/abs/2406.09215) (7) · [`TALLRec`](https://arxiv.org/abs/2305.00447) (7) · [`BIGRec`](https://arxiv.org/abs/2308.08434) (6) · [`LLaRA`](https://arxiv.org/abs/2312.02445) (6) · [`D3`](https://arxiv.org/abs/2406.14900) (5) · [`RLMRec`](https://arxiv.org/abs/2310.15950) (4) · [`AlphaRec`](https://arxiv.org/abs/2407.05441) (4) · [`LLMRank`](https://arxiv.org/abs/2305.08845) (3) · [`AgentCF`](https://arxiv.org/abs/2310.09233) (3) · [`KAR`](https://arxiv.org/abs/2306.10933) (3) · [`RLMRec-Con`](https://arxiv.org/abs/2310.15950) (3) · [`RLMRec-Gen`](https://arxiv.org/abs/2310.15950) (3) · [`InteRecAgent`](https://arxiv.org/abs/2308.16505) (3) · [`R2ec`](https://arxiv.org/abs/2505.16994) (3) · [`LLMInit`](https://arxiv.org/abs/2503.01814) (2) · [`LLM-ESR`](https://arxiv.org/abs/2405.20646) (2) · [`Chat-Rec`](https://arxiv.org/abs/2303.14524) (2) · [`Rec-R1`](https://arxiv.org/abs/2503.24289) (2) · [`LLM-Rec`](https://arxiv.org/abs/2307.15780) (2) · [`LlamaRec`](https://arxiv.org/abs/2311.02089) (2)

</details>

<details open>
<summary><b>Classical CF · MF, neighborhood, neural CF</b> — 34 papers</summary>

`Popularity` (9) · `MF` (7) · [`NCF`](https://arxiv.org/abs/1708.05031) (5) · [`BPR-MF`](https://arxiv.org/abs/1205.2618) (5) · [`BPR`](https://arxiv.org/abs/1205.2618) (4) · `DMF` (2) · `SVD` (2) · `ALS` (2) · `ItemKNN` (2) · [`NeuMF`](https://arxiv.org/abs/1708.05031) (2)

</details>

<details open>
<summary><b>Text- & multimodal-enhanced</b> — 34 papers</summary>

[`UniSRec`](https://arxiv.org/abs/2206.05941) (11) · [`RecFormer`](https://arxiv.org/abs/2305.13731) (6) · [`MoRec`](https://arxiv.org/abs/2303.13835) (4) · `BM25` (4) · [`VBPR`](https://arxiv.org/abs/1510.01784) (3) · [`BLAIR-BASE`](https://arxiv.org/abs/2403.03952) (3) · [`TedRec`](https://arxiv.org/abs/2402.18166) (3) · [`QARM`](https://arxiv.org/abs/2411.11739) (2) · [`BLAIR-LARGE`](https://arxiv.org/abs/2403.03952) (2)

</details>

<details open>
<summary><b>Graph-based CF</b> — 19 papers</summary>

[`LightGCN`](https://arxiv.org/abs/2002.02126) (15) · [`NGCF`](https://arxiv.org/abs/1905.08108) (3) · [`SimGCL`](https://arxiv.org/abs/2112.08679) (2)

</details>

<details open>
<summary><b>General-purpose LLMs · zero-shot / prompted</b> — 18 papers</summary>

`GPT-4o` (4) · `GPT-4o-mini` (3) · `GPT4` (2) · `Claude 3.5 Haiku` (2) · `Gemini 2.5 Flash` (2) · `GPT-3.5-Turbo` (2)

</details>

<details open>
<summary><b>CTR / feature-interaction</b> — 6 papers</summary>

[`DIN`](https://arxiv.org/abs/1706.06978) (3) · [`CTRL`](https://arxiv.org/abs/2306.02841) (2)

</details>

<details>
<summary><b>Other / specialized</b> — 65 papers</summary>

`Centric` (3) · `Temp-Fusion` (3) · `Random` (3) · `Retrain` (3) · [`FairRec`](https://arxiv.org/abs/2002.10764) (2) · `UniCDR` (2) · `Zero-shot` (2) · [`ERL`](https://arxiv.org/abs/2503.22675) (2) · [`PRL`](https://arxiv.org/abs/2503.22675) (2) · [`ReRe`](https://arxiv.org/abs/2510.12211) (2) · [`LatentR3`](https://arxiv.org/abs/2505.19092) (2)

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
