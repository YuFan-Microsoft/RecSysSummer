# 🧪 Amazon-2023 — Baseline Reproduction-Code Paths

One most-reliable code path for every baseline (used by **≥ 2** of the 132 Amazon-2023 papers), chosen by priority **official repo → runs on Amazon-2023 → runs on other data**. Companion to [`Amazon-2023_Code.md`](Amazon-2023_Code.md) (which tracks *corpus-paper* code). All GitHub URLs HTTP-200 verified Jun 2026.

## TL;DR

- **Classical / sequential / graph (~23 baselines) → one framework: [RecBole](https://github.com/RUCAIBox/RecBole)** (+ RecBole-DA, RecBole-GNN). The official **McAuley-Lab benchmark** [`hyp1231/AmazonReviews2023`](https://github.com/hyp1231/AmazonReviews2023) already converts Amazon-2023 into RecBole format (+ BLAIR text embeddings) — **start there**, then swap `--model=X`.
- **Generative / semantic-ID / LLM → each method's own repo.** Five ship **native Amazon-2023** code: **BLAIR · MiniOneRec · ReaRec · R²ec · Rec-R1**.
- **No public code** (reimplement from paper): `CoST` · `Chat-Rec` · `LLM-Rec` · `QARM` · `CTRL`. General-purpose LLMs (GPT-4o, Claude, Gemini…) are **API-only**.
- ⚠️ **A paper's repo rarely contains the baselines** — most corpus-paper repos ship only their *own* method. Borrow baseline code from **RecBole** or the baseline's **own** repo, not from a paper repo.

## Per-baseline code path

Priority per baseline: **official → runs-on-Amazon-2023 → runs-on-other-data**. Type: `Official` · `Official·2023` (native) · `RecBole(-DA/GNN)` · `Reproduction` · `Library` · `API` · `❌` (none). "Run on Amazon-2023" = the practical route.

### Sequential / session-based
| Baseline (uses) | Most-reliable code path | Type | Run on Amazon-2023 |
|---|---|---|---|
| **SASRec** (55) | [kang205/SASRec](https://github.com/kang205/SASRec) | Official (TF) | RecBole `SASRec` (direct) |
| **GRU4Rec** (29) | [hidasib/GRU4Rec](https://github.com/hidasib/GRU4Rec) | Official | RecBole `GRU4Rec` |
| **BERT4Rec** (27) | [FeiSun/BERT4Rec](https://github.com/FeiSun/BERT4Rec) | Official (TF) | RecBole `BERT4Rec` |
| **Caser** (15) | [graytowne/caser_pytorch](https://github.com/graytowne/caser_pytorch) | Official | RecBole `Caser` |
| **FMLP-Rec** (11) | [Woeee/FMLP-Rec](https://github.com/Woeee/FMLP-Rec) | Official | adapt (custom format + 99 negatives) |
| **S3-Rec** (10) | [RUCAIBox/CIKM2020-S3Rec](https://github.com/RUCAIBox/CIKM2020-S3Rec) | Official | RecBole `S3Rec` (needs item attrs) |
| **DuoRec** (8) | [RuihongQiu/DuoRec](https://github.com/RuihongQiu/DuoRec) | Official | RecBole-DA `DuoRec` |
| **FDSA** (8) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `FDSA` | RecBole (no official) | direct (needs item features) |
| **HGN** (4) | [allenjack/HGN](https://github.com/allenjack/HGN) | Official | RecBole `HGN` |
| **CL4SRec** (3) | [RUCAIBox/RecBole-DA](https://github.com/RUCAIBox/RecBole-DA) `CL4SRec` | RecBole-DA (no official) | direct |
| **NextItNet** (3) | [fajieyuan/WSDM2019-nextitnet](https://github.com/fajieyuan/WSDM2019-nextitnet) | Official (TF) | RecBole `NextItNet` |
| **MAERec** (3) | [HKUDS/MAERec](https://github.com/HKUDS/MAERec) | Official | adapt (custom pkl + graph) |
| **SASRec Base** (2) | [kang205/SASRec](https://github.com/kang205/SASRec) | Official (=SASRec) | RecBole `SASRec` |
| **BERT4Rec Base** (2) | [FeiSun/BERT4Rec](https://github.com/FeiSun/BERT4Rec) | Official (=BERT4Rec) | RecBole `BERT4Rec` |
| **FEARec** (2) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `FEARec` | RecBole | direct |
| **DiffuRec** (2) | [WHUIR/DiffuRec](https://github.com/WHUIR/DiffuRec) | Official | adapt |
| **CoST** (2) | — | ❌ no public code | implement from paper |
| **LRURec** (2) | [yueqirex/LRURec](https://github.com/yueqirex/LRURec) | Official | adapt |
| **CORE** (2) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `CORE` | RecBole | direct |
| **BSARec** (2) | [yehjin-shin/BSARec](https://github.com/yehjin-shin/BSARec) | Official | adapt (FMLP format) |
| **ReaRec** (2) | [TangJiakai/ReaRec](https://github.com/TangJiakai/ReaRec) | Official·2023 | native (needs LLaMA-3.1-8B emb) |

### Generative retrieval / semantic-ID
| Baseline (uses) | Most-reliable code path | Type | Run on Amazon-2023 |
|---|---|---|---|
| **TIGER** (23) | [snap-research/GRID](https://github.com/snap-research/GRID) | in a 2023 repo (no official) | run via GRID (supply your 2023 atomic files) |
| **HSTU** (13) | [meta-recsys/generative-recommenders](https://github.com/meta-recsys/generative-recommenders) | Official | write a 2023 preprocessor |
| **LETTER** (11) | [HonghuiBao2000/LETTER](https://github.com/HonghuiBao2000/LETTER) | Official | needs item-text emb, multi-GPU |
| **LCRec** (8) | [RUCAIBox/LC-Rec](https://github.com/RUCAIBox/LC-Rec) | Official | LLaMA-7B, 8×GPU |
| **VQ-Rec** (7) | [RUCAIBox/VQ-Rec](https://github.com/RUCAIBox/VQ-Rec) | Official (RecBole) | needs PLM emb + faiss PQ |
| **P5** (4) | [jeykigung/P5](https://github.com/jeykigung/P5) | Official | multi-GPU retrain + prompts |
| **MiniOneRec** (3) | [AkaliKong/MiniOneRec](https://github.com/AkaliKong/MiniOneRec) | Official·2023 | native (4–8×A100) |
| **ETEGRec** (3) | [RUCAIBox/ETEGRec](https://github.com/RUCAIBox/ETEGRec) | Official | needs SASRec/PLM emb |
| **ActionPiece** (3) | [google-deepmind/action_piece](https://github.com/google-deepmind/action_piece) | Official | add a 2023 data config |
| **P5-CID** (2) | [Wenyueh/LLM-RecSys-ID](https://github.com/Wenyueh/LLM-RecSys-ID) | Official (Hua et al.) | adapt |
| **RK-Means** (2) | [snap-research/GRID](https://github.com/snap-research/GRID) `rkmeans_*` | in a 2023 repo | run via GRID |
| **GenRec** (2) | [rutgerswiselab/GenRec](https://github.com/rutgerswiselab/GenRec) | Official | adapt |

### LLM-based recommenders
| Baseline (uses) | Most-reliable code path | Type | Run on Amazon-2023 |
|---|---|---|---|
| **S-DPO** (7) | [chenyuxin1999/S-DPO](https://github.com/chenyuxin1999/S-DPO) | Official | LoRA+DPO, 4-GPU |
| **TALLRec** (7) | [SAI990323/TALLRec](https://github.com/SAI990323/TALLRec) | Official | LLaMA-7B LoRA, 1-GPU |
| **BIGRec** (6) | [SAI990323/BIGRec](https://github.com/SAI990323/BIGRec) | Official | LoRA (data 2018→2023) |
| **LLaRA** (6) | [ljy0ustc/LLaRA](https://github.com/ljy0ustc/LLaRA) | Official | LoRA (train CF backbone first) |
| **D3** (5) | [SAI990323/DecodingMatters](https://github.com/SAI990323/DecodingMatters) | Official | Qwen2-0.5B LoRA, 1-GPU |
| **RLMRec** (4) | [HKUDS/RLMRec](https://github.com/HKUDS/RLMRec) | Official | LLM inference + CF training |
| **AlphaRec** (4) | [LehengTHU/AlphaRec](https://github.com/LehengTHU/AlphaRec) | Official | frozen LLM emb + MLP/GCN |
| **LLMRank** (3) | [RUCAIBox/LLMRank](https://github.com/RUCAIBox/LLMRank) | Official | OpenAI API zero-shot |
| **AgentCF** (3) | [RUCAIBox/AgentCF](https://github.com/RUCAIBox/AgentCF) | Official | GPT-4 API (expensive at scale) |
| **KAR** (3) | [YunjiaXi/Open-World-Knowledge-Augmented-Recommendation](https://github.com/YunjiaXi/Open-World-Knowledge-Augmented-Recommendation) | Official | LLM knowledge + small CF |
| **RLMRec-Con** (3) | [HKUDS/RLMRec](https://github.com/HKUDS/RLMRec) | Official (variant) | same as RLMRec |
| **RLMRec-Gen** (3) | [HKUDS/RLMRec](https://github.com/HKUDS/RLMRec) | Official (variant) | same as RLMRec |
| **InteRecAgent** (3) | [microsoft/RecAI](https://github.com/microsoft/RecAI) (`InteRecAgent/`) | Official | GPT-4 API + tools |
| **R2ec** (3) | [YRYangang/RRec](https://github.com/YRYangang/RRec) | Official·2023 | native (4-GPU RL) |
| **LLMInit** (2) | [DavidZWZ/LLMInit](https://github.com/DavidZWZ/LLMInit) | Official | frozen-LLM init for RecBole CF |
| **LLM-ESR** (2) | [liuqidong07/LLM-ESR](https://github.com/liuqidong07/LLM-ESR) | Official | adapt |
| **Chat-Rec** (2) | — | ❌ no official repo | implement from paper (prompt) |
| **Rec-R1** (2) | [linjc16/Rec-R1](https://github.com/linjc16/Rec-R1) | Official·2023 | native (PPO via veRL) |
| **LLM-Rec** (2) | — | ❌ no official repo | implement from paper (prompt) |
| **LlamaRec** (2) | [Yueeeeeeee/LlamaRec](https://github.com/Yueeeeeeee/LlamaRec) | Official | LoRA (Llama-2) |

### Classical CF
| Baseline (uses) | Most-reliable code path | Type | Run on Amazon-2023 |
|---|---|---|---|
| **Popularity** (9) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `Pop` | RecBole | direct |
| **MF** (7) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `BPR` | RecBole | direct |
| **NCF** (5) | [hexiangnan/neural_collaborative_filtering](https://github.com/hexiangnan/neural_collaborative_filtering) | Official (Keras) | RecBole `NeuMF` |
| **BPR-MF** (5) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `BPR` | RecBole | direct |
| **BPR** (4) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `BPR` | RecBole | direct |
| **DMF** (2) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `DMF` | RecBole | direct |
| **SVD** (2) | [PreferredAI/cornac](https://github.com/PreferredAI/cornac) `SVD` | Library | direct |
| **ALS** (2) | [benfred/implicit](https://github.com/benfred/implicit) | Library | direct |
| **ItemKNN** (2) | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `ItemKNN` | RecBole | direct |
| **NeuMF** (2) | [hexiangnan/neural_collaborative_filtering](https://github.com/hexiangnan/neural_collaborative_filtering) | Official | RecBole `NeuMF` |

### Text- & multimodal-enhanced
| Baseline (uses) | Most-reliable code path | Type | Run on Amazon-2023 |
|---|---|---|---|
| **UniSRec** (11) | [RUCAIBox/UniSRec](https://github.com/RUCAIBox/UniSRec) | Official (RecBole) | needs text emb (BLAIR); shipped in McAuley benchmark |
| **RecFormer** (6) | [AaronHeee/RecFormer](https://github.com/AaronHeee/RecFormer) | Reproduction ([Official](https://github.com/JiachengLi1995/Recformer) withholds code) | adapt (from 2018) |
| **MoRec** (4) | [westlake-repl/IDvs.MoRec](https://github.com/westlake-repl/IDvs.MoRec) | Official | full data swap (non-Amazon) |
| **BM25** (4) | [dorianbrown/rank_bm25](https://github.com/dorianbrown/rank_bm25) | Library | direct (also in Rec-R1) |
| **VBPR** (3) | [PreferredAI/cornac](https://github.com/PreferredAI/cornac) `VBPR` | Library (⚠️ not in RecBole) | needs product-image emb |
| **BLAIR-BASE** (3) | [hyp1231/AmazonReviews2023](https://github.com/hyp1231/AmazonReviews2023) (`blair/`) | Official·2023 | HF `hyp1231/blair-roberta-base` |
| **TedRec** (3) | [RUCAIBox/TedRec](https://github.com/RUCAIBox/TedRec) | Official (RecBole) | needs BERT item emb |
| **QARM** (2) | — | ❌ no official repo | implement from paper |
| **BLAIR-LARGE** (2) | [hyp1231/AmazonReviews2023](https://github.com/hyp1231/AmazonReviews2023) | Official·2023 | HF `hyp1231/blair-roberta-large` |

### Graph-based CF
| Baseline (uses) | Most-reliable code path | Type | Run on Amazon-2023 |
|---|---|---|---|
| **LightGCN** (15) | [gusye1234/LightGCN-PyTorch](https://github.com/gusye1234/LightGCN-PyTorch) | Official | RecBole / RecBole-GNN |
| **NGCF** (3) | [xiangwang1223/neural_graph_collaborative_filtering](https://github.com/xiangwang1223/neural_graph_collaborative_filtering) | Official | RecBole / RecBole-GNN |
| **SimGCL** (2) | [Coder-Yu/SELFRec](https://github.com/Coder-Yu/SELFRec) | Official | RecBole-GNN `SimGCL` |

### CTR / feature-interaction
| Baseline (uses) | Most-reliable code path | Type | Run on Amazon-2023 |
|---|---|---|---|
| **DIN** (3) | [zhougr1993/DeepInterestNetwork](https://github.com/zhougr1993/DeepInterestNetwork) | Official (TF) | RecBole `DIN` (needs CTR labels) |
| **CTRL** (2) | — | ❌ no official repo | implement from paper |

### General-purpose LLMs (zero-shot / prompted)
| Baseline (uses) | Code path | Type |
|---|---|---|
| **GPT-4o** (4) · **GPT-4o-mini** (3) · **GPT4** (2) · **GPT-3.5-Turbo** (2) | OpenAI API | API (no repo) |
| **Claude 3.5 Haiku** (2) | Anthropic API | API |
| **Gemini 2.5 Flash** (2) | Google API | API |

## Notes

- Baselines + paper counts from [`README.md §2.2`](../README.md#22--baselines-in-each-family); arXiv links there.
- RecBole membership verified against `recbole/model/*` (+ RecBole-DA / RecBole-GNN); every repo URL HTTP-200 checked and matched to its paper; native-2023 data versions confirmed from each repo's download script.

<div align="center"><sub>Companion to <a href="Amazon-2023_Code.md">Amazon-2023_Code.md</a> · corpus on <a href="https://huggingface.co/datasets/yufan/recsys-papers-2025-2026">Hugging Face</a></sub></div>
