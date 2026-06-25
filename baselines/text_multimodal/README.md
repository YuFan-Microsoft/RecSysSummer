<div align="center">

# Text- & multimodal-enhanced

**34 papers · 9 baselines** — items represented by text / image content

</div>

Recommenders that fuse **item text (or image)** content with collaborative signal — transferable text encoders, modality encoders, and the **BLAIR** Amazon-2023 text model. Mix of RecBole-family methods and standalone libraries.

> **Heads up:** these need item-text (or image) embeddings. `UniSRec` text embeddings (BLAIR) ship inside the McAuley-Lab benchmark [`hyp1231/AmazonReviews2023`](https://github.com/hyp1231/AmazonReviews2023).

| Baseline | Papers | Code path | Type | Run on Amazon-2023 |
|---|---:|---|---|---|
| [UniSRec](https://arxiv.org/abs/2206.05941) | 11 | [RUCAIBox/UniSRec](https://github.com/RUCAIBox/UniSRec) | Official (RecBole) | needs text emb (BLAIR); in McAuley benchmark |
| [RecFormer](https://arxiv.org/abs/2305.13731) | 6 | [AaronHeee/RecFormer](https://github.com/AaronHeee/RecFormer) | Reproduction ([official](https://github.com/JiachengLi1995/Recformer) withholds code) | adapt (from 2018) |
| [MoRec](https://arxiv.org/abs/2303.13835) | 4 | [westlake-repl/IDvs.MoRec](https://github.com/westlake-repl/IDvs.MoRec) | Official | full data swap (non-Amazon) |
| BM25 | 4 | [dorianbrown/rank_bm25](https://github.com/dorianbrown/rank_bm25) | Library | direct (also in Rec-R1) |
| [VBPR](https://arxiv.org/abs/1510.01784) | 3 | [PreferredAI/cornac](https://github.com/PreferredAI/cornac) `VBPR` | Library (⚠️ not in RecBole) | needs product-image emb |
| [BLAIR-BASE](https://arxiv.org/abs/2403.03952) | 3 | [hyp1231/AmazonReviews2023](https://github.com/hyp1231/AmazonReviews2023) (`blair/`) | Official·2023 | HF `hyp1231/blair-roberta-base` |
| [TedRec](https://arxiv.org/abs/2402.18166) | 3 | [RUCAIBox/TedRec](https://github.com/RUCAIBox/TedRec) | Official (RecBole) | needs BERT item emb |
| [QARM](https://arxiv.org/abs/2411.11739) | 2 | — | ❌ no official repo | implement from paper |
| [BLAIR-LARGE](https://arxiv.org/abs/2403.03952) | 2 | [hyp1231/AmazonReviews2023](https://github.com/hyp1231/AmazonReviews2023) | Official·2023 | HF `hyp1231/blair-roberta-large` |
