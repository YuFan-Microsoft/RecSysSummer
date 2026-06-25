<div align="center">

# Generative retrieval / semantic-ID

**43 papers · 12 baselines** — generate item identifiers token-by-token

</div>

Items are encoded as **semantic IDs** (e.g. RQ-VAE codes) and a seq2seq / decoder model **generates** the next item's ID. No single framework covers these — clone each method's **own repo**. TIGER has no official release; the community standard is to run it through **GRID**.

> **Heads up:** most need item-text embeddings (PLM/LLM) and multi-GPU training. Supply your Amazon-2023 atomic files from [`../../amazon_2023/`](../../amazon_2023/).

| Baseline | Papers | Code path | Type | Run on Amazon-2023 |
|---|---:|---|---|---|
| [TIGER](https://arxiv.org/abs/2305.05065) | 23 | [snap-research/GRID](https://github.com/snap-research/GRID) | in a 2023 repo (no official) | run via GRID (supply 2023 atomic files) |
| [HSTU](https://arxiv.org/abs/2402.17152) | 13 | [meta-recsys/generative-recommenders](https://github.com/meta-recsys/generative-recommenders) | Official | write a 2023 preprocessor |
| [LETTER](https://arxiv.org/abs/2405.07314) | 11 | [HonghuiBao2000/LETTER](https://github.com/HonghuiBao2000/LETTER) | Official | needs item-text emb, multi-GPU |
| [LCRec](https://arxiv.org/abs/2311.09049) | 8 | [RUCAIBox/LC-Rec](https://github.com/RUCAIBox/LC-Rec) | Official | LLaMA-7B, 8×GPU |
| [VQ-Rec](https://arxiv.org/abs/2210.12316) | 7 | [RUCAIBox/VQ-Rec](https://github.com/RUCAIBox/VQ-Rec) | Official (RecBole) | needs PLM emb + faiss PQ |
| [P5](https://arxiv.org/abs/2203.13366) | 4 | [jeykigung/P5](https://github.com/jeykigung/P5) | Official | multi-GPU retrain + prompts |
| [MiniOneRec](https://arxiv.org/abs/2510.24431) | 3 | [AkaliKong/MiniOneRec](https://github.com/AkaliKong/MiniOneRec) | Official·2023 | native (4–8×A100) |
| [ETEGRec](https://arxiv.org/abs/2409.05546) | 3 | [RUCAIBox/ETEGRec](https://github.com/RUCAIBox/ETEGRec) | Official | needs SASRec/PLM emb |
| [ActionPiece](https://arxiv.org/abs/2502.13581) | 3 | [google-deepmind/action_piece](https://github.com/google-deepmind/action_piece) | Official | add a 2023 data config |
| [P5-CID](https://arxiv.org/abs/2305.06569) | 2 | [Wenyueh/LLM-RecSys-ID](https://github.com/Wenyueh/LLM-RecSys-ID) | Official (Hua et al.) | adapt |
| RK-Means | 2 | [snap-research/GRID](https://github.com/snap-research/GRID) `rkmeans_*` | in a 2023 repo | run via GRID |
| [GenRec](https://arxiv.org/abs/2307.00457) | 2 | [rutgerswiselab/GenRec](https://github.com/rutgerswiselab/GenRec) | Official | adapt |
