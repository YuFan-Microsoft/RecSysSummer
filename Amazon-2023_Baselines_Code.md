# 🧪 Amazon-2023 — Baseline **Reproduction-Code** Availability & Ease of Running

Which **baseline methods** (not corpus papers) used across the 132 Amazon-2023 papers ship runnable code, and how hard each is to actually run **on Amazon Reviews 2023**. Scope = high-frequency baselines (used by **≥ 3** papers in [`README.md §2.2`](README.md#22--baselines-in-each-family)) **plus** the newest 2025–26 baselines. Companion to [`Amazon-2023_Code.md`](Amazon-2023_Code.md) (which instead tracks *corpus-paper* code). Verified Jun 2026.

> ⚠️ **Two code sources — don't confuse them.** **(A)** A baseline's *own canonical repo* (`kang205/SASRec`, `RUCAIBox/UniSRec`…) — mostly Amazon **2014/2018** (per-family tables below). **(B)** A *corpus-paper repo* (from [`Amazon-2023_Code.md`](Amazon-2023_Code.md)) that **reports the baseline on Amazon-2023** — gives you the 2023 data splits + reference numbers, **but I checked each one and most ship only their *own* method, not the baselines** (see [§ where the code lives](#-where-each-baselines-amazon-2023-code-actually-lives)). **Net:** to *run* a baseline on Amazon-2023, borrow **RecBole + the McAuley benchmark** (classical/sequential) or the baseline's **own** repo (generative/LLM) — and copy the data setup from a corpus paper.

---

## 🚀 TL;DR — the easy path

1. **One framework covers ~22 baselines: [RecBole](https://github.com/RUCAIBox/RecBole).** SASRec, GRU4Rec, BERT4Rec, Caser, S³-Rec, FDSA, HGN, NextItNet, CORE, FEARec, DIN, BPR/MF, NCF/NeuMF, LightGCN, NGCF, Pop, ItemKNN, DMF are **built in**. Convert Amazon-2023 → RecBole atomic files **once**, then swap models with `--model=X`. (+ RecBole-DA adds CL4SRec, DuoRec; + RecBole-GNN adds SimGCL.)
2. **The official McAuley-Lab benchmark already does that conversion for you.** [`hyp1231/AmazonReviews2023`](https://github.com/hyp1231/AmazonReviews2023) → `seq_rec_results/` is RecBole-based: `process_amazon_2023.py` builds the atomic files (+ BLAIR text embeddings) and `run.py -m {UniSRec,SASRecText}` trains. Any RecBole model plugs into the same data. **Start here** — you already use this repo's `benchmark_scripts/` for data processing (`amazon_2023/process_amazon2023.py`).
3. **5 baselines ship native Amazon-2023 code** (no version porting, but heavier compute): **BLAIR**, **ReaRec**, **R²ec**, **Rec-R1**, **MiniOneRec**.
4. **Only 2 of ~45 have no usable code at all:** **CoST** and **ReRe**. **TIGER** has no official Google repo but a solid community reproduction.

**Suggested order:** RecBole core (Phase 1) → text/RecBole-compatible UniSRec/VQ-Rec/TedRec (Phase 2) → native-2023 newest ReaRec/R²ec/Rec-R1/MiniOneRec (Phase 3) → standalone + LLM repos that need data porting (Phase 4).

---

## ⭐ Where each baseline's Amazon-2023 code actually lives

Joining the **132** per-paper "Baselines Used" lists with the **72** code-released papers shows **every** high-frequency baseline has been *reported* on Amazon-2023 by several papers (SASRec in 32, TIGER in 14, HSTU in 6, LETTER in 8…) — so the data setups, splits and reference numbers all exist. **But ⚠️ I inspected each repo's code one by one: most ship only their *own* method, not the baselines.** In RUCAIBox/HKUDS-style papers the baselines were run via **RecBole** or each baseline's own repo, and only the numbers are reported. What each repo's code actually contains:

| Repo | A2023 data | Repo's *code* contains | Borrowable **baseline** code? |
|---|---|---|---|
| ⭐ [`AkaliKong/MiniOneRec`](https://github.com/AkaliKong/MiniOneRec) | ✅ `amazon23` | SASRec + RQ-VAE semantic-ID tokenizer + OneRec | ✅ **SASRec** + the SID tokenizer pipeline |
| ⭐ [`linjc16/Rec-R1`](https://github.com/linjc16/Rec-R1) | ✅ HF | bundles McAuley's RecBole `SASRecText`+`UniSRec` + BM25 + its RL | ✅ **SASRec/UniSRec** (RecBole) + BM25 |
| [`snap-research/GRID`](https://github.com/snap-research/GRID) | ❓ default cfg = P5/old | clean **TIGER** + RQ-VAE/k-means modules | ✅ **TIGER** (point it at your 2023 atomic data) |
| ⭐ [`FuCongResearchSquad/ReSID`](https://github.com/FuCongResearchSquad/ReSID) | ✅ 10 cats | own method only (T5: famae/gaoq) | ❌ — but borrow its **A2023 data pipeline** |
| ⭐ [`RUCAIBox/UTGRec`](https://github.com/RUCAIBox/UTGRec) | ✅ `./AmazonReviews2023/` | own tokenizer (`model.py`) | ❌ |
| ⭐ [`hyp1231/Latte`](https://github.com/hyp1231/Latte) | ✅ `AmazonReviews2023` | genrec: Latte + PSID only | ❌ |
| ⭐ [`TangJiakai/ReaRec`](https://github.com/TangJiakai/ReaRec) | ✅ | own method (ERL/PRL) | ❌ |
| ⭐ [`YRYangang/RRec`](https://github.com/YRYangang/RRec) | ✅ | own LLM method (gemma/qwen) | ❌ |
| [`HKUDS/RecGPT`](https://github.com/HKUDS/RecGPT) | ✅ `load_dataset("McAuley-Lab/Amazon-Reviews-2023")` | own method (`model.py`) | ❌ |
| `RUCAIBox/MTGRec`·`CCFRec`·`DeepRec`, `HappyPointer/SIDReasoner` | ⚠️ data on Google Drive (version not stated in-repo) | own method only (`model.py`) | ❌ |

**So the reliable way to *borrow runnable baseline code* is unchanged:** classical / sequential / graph → **RecBole + the McAuley benchmark** (Rec-R1 literally re-bundles it — proof this is the common path); generative / semantic-ID → each baseline's **own** repo (`RUCAIBox/LC-Rec`, `VQ-Rec`, `UniSRec`, `TedRec`, `ETEGRec`) + GRID (TIGER) + MiniOneRec (SID tokenizer); LLM → each own repo. Use the index below for **reference numbers + identical 2023 splits**, *not* as a baseline-code source.

### Reverse index — which code-released Amazon-2023 papers *report* each baseline

> `#` = number of code-released corpus papers that **report** that baseline on Amazon-2023. Use these for **identical 2023 data splits + reference numbers + hyper-params**. ⚠️ As shown above, most of these repos ship only their *own* method — for the **baseline's runnable code** use RecBole (classical) or the baseline's own repo (generative/LLM). **★** = repo whose Amazon-2023 data pipeline I verified directly.

| Baseline | #papers reporting on A2023 | Example code-released papers (splits/numbers; ★=verified 2023 data) |
|---|---:|---|
| **SASRec** | 32 | ★`RUCAIBox/UTGRec`, ★`AkaliKong/MiniOneRec`, ★`FuCongResearchSquad/ReSID` |
| **GRU4Rec** | 18 | ★`RUCAIBox/UTGRec`, ★`hyp1231/Latte`, ★`AkaliKong/MiniOneRec` |
| **BERT4Rec** | 16 | ★`TangJiakai/ReaRec`, ★`RUCAIBox/UTGRec`, ★`hyp1231/Latte` |
| **Caser** | 9 | ★`AkaliKong/MiniOneRec`, ★`YRYangang/RRec`, `HappyPointer/SIDReasoner` |
| **FMLP-Rec** | 8 | ★`RUCAIBox/UTGRec`, ★`hyp1231/Latte`, `RUCAIBox/DeepRec` |
| **S³-Rec** | 7 | ★`RUCAIBox/UTGRec`, ★`hyp1231/Latte`, ★`FuCongResearchSquad/ReSID` |
| **FDSA** | 7 | ★`RUCAIBox/UTGRec`, ★`hyp1231/Latte`, `RUCAIBox/CCFRec` |
| **DuoRec** | 4 | `YoungZ365/Pctx`, `HKUDS/RecGPT`, `RUCAIBox/CCFRec` |
| **HGN** | 3 | ★`FuCongResearchSquad/ReSID`, `RUCAIBox/MTGRec`, `YoungZ365/Pctx` |
| **TIGER** | 14 | ★`RUCAIBox/UTGRec`, ★`hyp1231/Latte`, ★`AkaliKong/MiniOneRec` |
| **HSTU** | 6 | ★`hyp1231/Latte`, ★`AkaliKong/MiniOneRec`, `HappyPointer/SIDReasoner` |
| **LETTER** | 8 | ★`RUCAIBox/UTGRec`, ★`hyp1231/Latte`, ★`FuCongResearchSquad/ReSID` |
| **LC-Rec** | 5 | ★`AkaliKong/MiniOneRec`, `Starrylay/GenRecEdit`, `HappyPointer/SIDReasoner` |
| **VQ-Rec** | 5 | ★`RUCAIBox/UTGRec`, `Starrylay/GenRecEdit`, `RUCAIBox/CCFRec` |
| **ETEGRec** | 2 | ★`FuCongResearchSquad/ReSID`, `yliuaa/DECOR` |
| **ActionPiece** | 2 | ★`hyp1231/Latte`, `YoungZ365/Pctx` |
| **UniSRec** | 7 | ★`TangJiakai/ReaRec`, ★`RUCAIBox/UTGRec`, `HonghuiBao2000/HUM` |
| **RecFormer** | 4 | `Sein-Kim/LLM-SRec`, `HonghuiBao2000/HUM`, `yunzhel2/LLM-RecG` |
| **TedRec** | 2 | `RUCAIBox/DeepRec`, `RUCAIBox/CCFRec` |
| **LightGCN** | 10 | `minseojeonn/AlphaFree`, `giuspillo/EcoAmazon`, `legenduck/PERSONA4REC` |
| **BPR / MF** | 6 | `giuspillo/EcoAmazon`, `legenduck/PERSONA4REC`, `UFSCar-LaSID/bandits_blind_spot` |
| **NCF / NeuMF** | 3 | `tsinghua-fib-lab/AgentSocietyChallenge`, `Sein-Kim/self_evolverec`, `andersvestrum/carbon-aware-recsys` |
| **TALLRec** | 5 | `legenduck/PERSONA4REC`, `Sein-Kim/LLM-SRec` |
| **BIGRec** | 1 | ★`AkaliKong/MiniOneRec` |
| **LLaRA** | 5 | `Sein-Kim/LLM-SRec`, `sony/ds-research-code` (recsys25-IntervalLLM) |
| **S-DPO** | 2 | ★`AkaliKong/MiniOneRec` |
| **D3** | 1 | ★`AkaliKong/MiniOneRec` |
| **AlphaRec** | 4 | `wangyu0627/IRLLRec`, `minseojeonn/AlphaFree`, `jaewan7599/L3AE_CIKM2025` |
| **RLMRec** | 3 | `AI-Santiago/GenAIR`, `minseojeonn/AlphaFree`, `Hugo-Chinn/AlphaFuse` |

*(Counts from joining `Freq_132_Amazon-2023/*.md` "Baselines Used" with the 72 code rows in `Amazon-2023_Code.md`; anonymized `4open.science` repos omitted from the "borrow" column in favor of GitHub.)*

---

## 📋 Per-baseline code path (full ≥2 list)

**One most-reliable code path per baseline**, chosen by priority **official repo → runs on Amazon-2023 → runs on other data**. Type: `Official`=author repo · `Official·2023`=author repo native to Amazon-2023 · `RecBole(-DA/GNN)`=in the framework (no/again official) · `Reproduction`=community reproduction · `Library`=general library · `API`=closed model · `❌`=no public code verified. All GitHub URLs HTTP-200 verified Jun 2026. "Run on A2023" = the practical route.

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

> **5 named baselines have no runnable code:** `CoST`, `Chat-Rec`, `LLM-Rec`, `QARM`, `CTRL` (no official/public implementation found — reimplement from the paper). The `Other / specialized` family is mostly paper-specific ablations (Centric / Temp-Fusion / Retrain …) with no general code, not listed individually.

---

## At a glance

| | |
|---|---:|
| 🧩 Baselines assessed (≥3 papers + newest) | ~45 |
| ✅ Have public/usable code | 43 |
| ❌ No usable code (implement from paper) | **CoST, ReRe** |
| 🟢 Runnable via **RecBole** (core/DA/GNN) | ~22 |
| 🛒 Ship **native Amazon-2023** code | **BLAIR, ReaRec, R²ec, Rec-R1, MiniOneRec** |
| 🟢 Easy · 🟡 Medium · 🔴 Hard | 14 · 17 · 14 |

---

## Tier 1 · 🟢 Easy — built into RecBole (run on Amazon-2023 with one data conversion)

> `python run_recbole.py --model=<Model> --dataset=amazon2023_<cat>` after exporting your 5-core/last-out splits to a `.inter` atomic file. The McAuley benchmark / your `process_amazon2023.py` already produces the right splits.

| Baseline (uses) | arXiv | RecBole class | Original repo (reference) |
|---|---|---|---|
| **SASRec** (55) | [1808.09781](https://arxiv.org/abs/1808.09781) | `SASRec` | [kang205/SASRec](https://github.com/kang205/SASRec) |
| **GRU4Rec** (29) | [1511.06939](https://arxiv.org/abs/1511.06939) | `GRU4Rec` | [hidasib/GRU4Rec](https://github.com/hidasib/GRU4Rec) |
| **BERT4Rec** (27) | [1904.06690](https://arxiv.org/abs/1904.06690) | `BERT4Rec` | [FeiSun/BERT4Rec](https://github.com/FeiSun/BERT4Rec) |
| **Caser** (15) | [1809.07426](https://arxiv.org/abs/1809.07426) | `Caser` | [graytowne/caser_pytorch](https://github.com/graytowne/caser_pytorch) |
| **HGN** (4) | [1906.09217](https://arxiv.org/abs/1906.09217) | `HGN` | [allenjack/HGN](https://github.com/allenjack/HGN) |
| **NextItNet** (3) | [1808.05163](https://arxiv.org/abs/1808.05163) | `NextItNet` | [fajieyuan/WSDM2019-nextitnet](https://github.com/fajieyuan/WSDM2019-nextitnet) |
| **LightGCN** (15) | [2002.02126](https://arxiv.org/abs/2002.02126) | `LightGCN` | [gusye1234/LightGCN-PyTorch](https://github.com/gusye1234/LightGCN-PyTorch) |
| **NGCF** (3) | [1905.08108](https://arxiv.org/abs/1905.08108) | `NGCF` | [xiangwang1223/neural_graph_collaborative_filtering](https://github.com/xiangwang1223/neural_graph_collaborative_filtering) |
| **BPR / MF / BPR-MF** (4/7/5) | [1205.2618](https://arxiv.org/abs/1205.2618) | `BPR` | — (no maintained repo; use RecBole) |
| **NCF / NeuMF** (5/2) | [1708.05031](https://arxiv.org/abs/1708.05031) | `NeuMF` | [hexiangnan/neural_collaborative_filtering](https://github.com/hexiangnan/neural_collaborative_filtering) |
| **Popularity** (9) · **ItemKNN** (2) · **DMF** (2) | — | `Pop` · `ItemKNN` · `DMF` | — (RecBole built-ins) |
| **CORE** (2) · **FEARec** (2) *(bonus, also ≥2)* | [2204.11067](https://arxiv.org/abs/2204.11067) · [2304.09184](https://arxiv.org/abs/2304.09184) | `CORE` · `FEARec` | — (RecBole built-ins) |

---

## Tier 2 · 🟡 Medium — RecBole built-in but needs item features / extension, or RecBole-compatible repo

| Baseline (uses) | arXiv | Code / framework | Why Medium |
|---|---|---|---|
| **S³-Rec** (10) | [2008.07873](https://arxiv.org/abs/2008.07873) | RecBole `S3Rec` · [RUCAIBox/CIKM2020-S3Rec](https://github.com/RUCAIBox/CIKM2020-S3Rec) | Two-phase: pre-train with item attributes (need `.item` features) then fine-tune. Amazon-2023 metadata satisfies this. |
| **FDSA** (8) | IJCAI'19 (no arXiv) | RecBole `FDSA` (no standalone repo) | Needs item feature fields (category/brand/price) in the `.item` file. |
| **DIN** (3) | [1706.06978](https://arxiv.org/abs/1706.06978) | RecBole `DIN` · [zhougr1993/DeepInterestNetwork](https://github.com/zhougr1993/DeepInterestNetwork) | CTR-style: needs labeled `.inter` (pos/neg) + item features, not pure sequences. |
| **CL4SRec** (3) | [2010.14395](https://arxiv.org/abs/2010.14395) | [RecBole-DA](https://github.com/RUCAIBox/RecBole-DA) `CL4SRec` | Same atomic files, but install the RecBole-DA extension (no standalone author repo). |
| **DuoRec** (8) | [2110.05730](https://arxiv.org/abs/2110.05730) | [RecBole-DA](https://github.com/RUCAIBox/RecBole-DA) `DuoRec` · [RuihongQiu/DuoRec](https://github.com/RuihongQiu/DuoRec) | RecBole-DA extension; DuoRec repo also runs CL4SRec. |
| **SimGCL** (2) *(bonus)* | [2112.08679](https://arxiv.org/abs/2112.08679) | [RecBole-GNN](https://github.com/RUCAIBox/RecBole-GNN) `SimGCL` | One GNN extension install. |
| **UniSRec** (11) | [2206.05941](https://arxiv.org/abs/2206.05941) | [RUCAIBox/UniSRec](https://github.com/RUCAIBox/UniSRec) (on RecBole) | RecBole-native; re-extract PLM/BLAIR text embeddings for 2023 items. **The McAuley benchmark ships this exact pipeline.** |
| **VQ-Rec** (7) | [2210.12316](https://arxiv.org/abs/2210.12316) | [RUCAIBox/VQ-Rec](https://github.com/RUCAIBox/VQ-Rec) (on RecBole) | RecBole-native; extract PLM embeddings → rebuild PQ codes (faiss). |
| **TedRec** (3) | [2402.18166](https://arxiv.org/abs/2402.18166) | [RUCAIBox/TedRec](https://github.com/RUCAIBox/TedRec) (on RecBole) | RecBole-native; needs frozen BERT item embeddings. |
| **VBPR** (3) | [1510.01784](https://arxiv.org/abs/1510.01784) | **Cornac** library ([`PreferredAI/cornac`](https://github.com/PreferredAI/cornac)) — *not* in RecBole (verified: no `vbpr.py`); no original-author repo | Needs product-image visual features — Amazon-2023 has images to extract; Cornac has a ready `VBPR` class. |
| **FMLP-Rec** (11) | [2202.13556](https://arxiv.org/abs/2202.13556) | [Woeee/FMLP-Rec](https://github.com/Woeee/FMLP-Rec) | Standalone; custom format w/ 99 pre-sampled negatives. Convert 2023 data + negatives. |
| **BSARec** (2)* | [2312.10325](https://arxiv.org/abs/2312.10325) | [yehjin-shin/BSARec](https://github.com/yehjin-shin/BSARec) | Standalone (FMLP-Rec data format); bonus: also runs SASRec/BERT4Rec/GRU4Rec/FMLP/DuoRec. |

---

## Tier 3 · 🛒 Native Amazon-2023 (repo already targets 2023 — but heavier compute)

| Baseline (uses) | arXiv | Official repo | Compute |
|---|---|---|---|
| **BLAIR** (3) | [2403.03952](https://arxiv.org/abs/2403.03952) | [hyp1231/AmazonReviews2023 `blair/`](https://github.com/hyp1231/AmazonReviews2023) | 🟡 *Designed for Amazon-2023.* Pre-trained checkpoints on HF (`hyp1231/blair-roberta-base`) → use as frozen text encoder = Easy. Re-training = multi-GPU contrastive. |
| **ReaRec** (2)* | [2503.22675](https://arxiv.org/abs/2503.22675) | [TangJiakai/ReaRec](https://github.com/TangJiakai/ReaRec) | 🟡 Uses official 2023 timestamp split (Video Games, Software, CDs, Baby). Needs LLaMA-3.1-8B item encoding; benched on 8×A100. |
| **R²ec** (3)* | [2505.16994](https://arxiv.org/abs/2505.16994) | [YRYangang/RRec](https://github.com/YRYangang/RRec) | 🔴 `preprocess.py` pulls `amazon_2023/` directly. Gemma-2-2B/Qwen2.5-3B full FT + RecPO RL, 4×GPU DeepSpeed. |
| **Rec-R1** (2)* | [2503.24289](https://arxiv.org/abs/2503.24289) | [linjc16/Rec-R1](https://github.com/linjc16/Rec-R1) | 🔴 `process_amazon_2023.py` loads `McAuley-Lab/Amazon-Reviews-2023` from HF. Qwen2.5-3B PPO via veRL+vLLM+Ray, 2–4 GPU. |
| **MiniOneRec** (3)* | [2510.24431](https://arxiv.org/abs/2510.24431) | [AkaliKong/MiniOneRec](https://github.com/AkaliKong/MiniOneRec) | 🔴 Ships `data/amazon23_data_process.*`. Qwen2.5 SID→SFT→GRPO RL, 4–8×A100 80GB. |

---

## Tier 4 · 🔴 Standalone / LLM repos — code exists but must be ported from 2014/2018 to 2023

### Generative retrieval / semantic-ID
| Baseline (uses) | arXiv | Official repo | Note |
|---|---|---|---|
| **TIGER** (23) | [2305.05065](https://arxiv.org/abs/2305.05065) | — *(no official)* | Best reproduction: [EdoardoBotta/RQ-VAE-Recommender](https://github.com/EdoardoBotta/RQ-VAE-Recommender) (Amazon-2014). RQ-VAE → seq decoder, 2-stage. |
| **HSTU** (13) | [2402.17152](https://arxiv.org/abs/2402.17152) | [meta-recsys/generative-recommenders](https://github.com/meta-recsys/generative-recommenders) | `amzn-books` preprocessor = old Amazon; write a 2023 loader. TorchRec/fbgemm stack. |
| **LETTER** (11) | [2405.07314](https://arxiv.org/abs/2405.07314) | [HonghuiBao2000/LETTER](https://github.com/HonghuiBao2000/LETTER) | Wraps TIGER + LC-Rec backends; RQ-VAE + item text embeddings; multi-GPU (deepspeed). |
| **LC-Rec** (8) | [2311.09049](https://arxiv.org/abs/2311.09049) | [RUCAIBox/LC-Rec](https://github.com/RUCAIBox/LC-Rec) | LLaMA-7B, 8-GPU deepspeed; gated base model. |
| **P5** (4) | [2203.13366](https://arxiv.org/abs/2203.13366) | [jeykigung/P5](https://github.com/jeykigung/P5) (+ [OpenP5](https://github.com/agiresearch/OpenP5)) | T5 multi-GPU pre-train; per-dataset prompt templates. |
| **ETEGRec** (3) | [2409.05546](https://arxiv.org/abs/2409.05546) | [RUCAIBox/ETEGRec](https://github.com/RUCAIBox/ETEGRec) | End-to-end tokenizer+rec; needs SASRec/PLM item embeddings; 1–2 GPU. |
| **ActionPiece** (3)* | [2502.13581](https://arxiv.org/abs/2502.13581) | [google-deepmind/action_piece](https://github.com/google-deepmind/action_piece) | Hardcoded `AmazonReviews2014/config.yaml`; add a 2023 config. Single-GPU, no LLM. |
| **CoST** (2)* | [2404.14774](https://arxiv.org/abs/2404.14774) | — **none found** | No public repo as of Jun 2026 — implement from paper. |

### Text- & multimodal-enhanced
| Baseline (uses) | arXiv | Official repo | Note |
|---|---|---|---|
| **RecFormer** (6) | [2305.13731](https://arxiv.org/abs/2305.13731) | [AaronHeee/RecFormer](https://github.com/AaronHeee/RecFormer) *(author-endorsed replication; [official](https://github.com/JiachengLi1995/Recformer) withholds code "Amazon policy")* | Longformer pre-train (multi-GPU); scripts target Amazon-2018; checkpoints available. |
| **MoRec** (4) | [2303.13835](https://arxiv.org/abs/2303.13835) | [westlake-repl/IDvs.MoRec](https://github.com/westlake-repl/IDvs.MoRec) | Uses HM/Bili/MIND — **no Amazon at all**; full dataset swap + image/text embedding. |

### LLM-based recommenders
| Baseline (uses) | arXiv | Official repo | Base LLM / cost |
|---|---|---|---|
| **TALLRec** (7) | [2305.00447](https://arxiv.org/abs/2305.00447) | [SAI990323/TALLRec](https://github.com/SAI990323/TALLRec) | LLaMA-7B LoRA, 1 GPU; convert to instruction JSON. |
| **S-DPO** (7) | [2406.09215](https://arxiv.org/abs/2406.09215) | [chenyuxin1999/S-DPO](https://github.com/chenyuxin1999/S-DPO) | LLaMA SFT+DPO LoRA, 4-GPU torchrun; only LastFM sample shipped. |
| **BIGRec** (6) | [2308.08434](https://arxiv.org/abs/2308.08434) | [SAI990323/BIGRec](https://github.com/SAI990323/BIGRec) | LLaMA-7B / Qwen2-0.5B LoRA; data = amazon_v2 (2018). |
| **LLaRA** (6) | [2312.02445](https://arxiv.org/abs/2312.02445) | [ljy0ustc/LLaRA](https://github.com/ljy0ustc/LLaRA) | LLaMA-2-7B LoRA; couples CF (SASRec/Caser/GRU4Rec) embeddings → must train CF on 2023 first. |
| **D3** (5) | [2406.14900](https://arxiv.org/abs/2406.14900) | [SAI990323/DecodingMatters](https://github.com/SAI990323/DecodingMatters) | Qwen2-0.5B LoRA, 1 GPU; pretrained weights on HF; closest LLM repo to 2023-ready. |
| **RLMRec** (4) | [2310.15950](https://arxiv.org/abs/2310.15950) | [HKUDS/RLMRec](https://github.com/HKUDS/RLMRec) | LLM inference (profiles) + light CF train; no LLM FT. |
| **AlphaRec** (4) | [2407.05441](https://arxiv.org/abs/2407.05441) | [LehengTHU/AlphaRec](https://github.com/LehengTHU/AlphaRec) | Frozen LLM embeddings + MLP/GCN; data = amazon_book_2014. Light once embedded. |
| **LLMRank** (3) | [2305.08845](https://arxiv.org/abs/2305.08845) | [RUCAIBox/LLMRank](https://github.com/RUCAIBox/LLMRank) | OpenAI API zero-shot, no GPU; RecBole `.inter` input. API cost. |
| **AgentCF** (3) | [2310.09233](https://arxiv.org/abs/2310.09233) | [RUCAIBox/AgentCF](https://github.com/RUCAIBox/AgentCF) | GPT-4 agent, no training; expensive at scale. |
| **KAR** (3) | [2306.10933](https://arxiv.org/abs/2306.10933) | [YunjiaXi/Open-World-Knowledge-Augmented-Recommendation](https://github.com/YunjiaXi/Open-World-Knowledge-Augmented-Recommendation) | LLM knowledge gen + small CF; 1 GPU. |
| **InteRecAgent** (3) | [2308.16505](https://arxiv.org/abs/2308.16505) | [microsoft/RecAI](https://github.com/microsoft/RecAI) (`InteRecAgent/`) | GPT-4 agent + tools; data-engineering to wire a new dataset. |
| **LatentR³** (2)* | [2505.19092](https://arxiv.org/abs/2505.19092) | [xuwenxinedu/R3](https://github.com/xuwenxinedu/R3) | LLaMA LoRA + custom GRPO, 2×A100; data = amazon_v2 (2018). |
| **LLMInit** (2)* | [2503.01814](https://arxiv.org/abs/2503.01814) | [DavidZWZ/LLMInit](https://github.com/DavidZWZ/LLMInit) | Frozen LLM init for LightGCN/SGL (RecBole); export 2023 to `.inter`. |
| **ReRe** (2)* | [2510.12211](https://arxiv.org/abs/2510.12211) | — **none verified** | No public code as of Jun 2026 (v1 only). |

\* = newest 2025–26 baseline (included regardless of frequency). General-purpose API LLMs (`GPT-4o`, `GPT-4o-mini`, `Claude 3.5`, `Gemini 2.5`) need no repo — just API access + a prompt.

---

## How to actually run them (recommended plan)

**Phase 1 — RecBole core (≈1 day, 1 GPU).** Export your `amazon_2023/processed/` 5-core/last-out splits to RecBole atomic files (or reuse `hyp1231/AmazonReviews2023 → seq_rec_results/dataset/process_amazon_2023.py`). Then loop:
```bash
for M in SASRec GRU4Rec BERT4Rec Caser S3Rec FDSA HGN NextItNet CORE FEARec \
         BPR NeuMF LightGCN NGCF Pop ItemKNN DMF DIN; do
  python run_recbole.py --model=$M --dataset=amazon2023_video_games \
    --config_files=overall.yaml   # Recall@{5,10}, NDCG@{5,10}, full ranking
done
```
Add `pip install recbole-gnn` (SimGCL) and the RecBole-DA repo (CL4SRec, DuoRec).

**Phase 2 — text/RecBole-compatible.** Generate BLAIR (`hyp1231/blair-roberta-base`) item embeddings once, then run **UniSRec / VQ-Rec / TedRec** (same atomic files + `.item` embeddings). The McAuley benchmark's `run.py -m UniSRec` is the template.

**Phase 3 — newest, native-2023 (needs GPUs).** Clone **ReaRec / R²ec / Rec-R1 / MiniOneRec** — they already point at Amazon-2023; just set categories. Budget 4–8×A100 for the RL ones.

**Phase 4 — standalone + LLM (port data).** FMLP-Rec, BSARec, P5, LC-Rec, LETTER, ETEGRec, ActionPiece, HSTU, RecFormer + LLM repos (TALLRec, BIGRec, D3, LLaRA, S-DPO, RLMRec, AlphaRec, KAR, LLMInit) — each needs a 2018→2023 data adapter. Start with **D3** (Qwen2-0.5B, 1 GPU, pretrained weights) as the lightest LLM baseline.

**Skip / implement-yourself:** **CoST**, **ReRe** (no code); **TIGER** (use the RQ-VAE-Recommender reproduction).

---

## Methodology & caveats

- Baseline set + frequencies from [`README.md §2.2`](README.md#22--baselines-in-each-family); "uses (N)" = papers using that baseline.
- Repo existence verified via GitHub (Jun 2026). RecBole coverage verified directly against `recbole/model/{sequential,general,context_aware}_recommender/` and RecBole-GNN/RecBole-DA model lists.
- "Native Amazon-2023" = the repo's own scripts download/process the McAuley-Lab 2023 release; all others target Amazon-2014 (`jmcauley.ucsd.edu`) or Amazon-2018 v2 (`amazon_v2`).
- Uncertain dataset versions (not stated in repo): **ETEGRec**, **TedRec**, **LETTER** — likely older Amazon; check the bundled `.item` ASIN format to confirm.
- `—` = none found / not applicable.

<div align="center"><sub>Companion to <a href="Amazon-2023_Code.md">Amazon-2023_Code.md</a> · corpus on <a href="https://huggingface.co/datasets/yufan/recsys-papers-2025-2026">Hugging Face</a></sub></div>
