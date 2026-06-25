<div align="center">

# Sequential / session-based

**64 papers · 19 baselines** — next-item prediction from interaction order

</div>

Transformer / RNN / CNN / MLP encoders over a user's chronological item sequence. **Most run directly in [RecBole](https://github.com/RUCAIBox/RecBole)** (`--model=X`); a handful keep a custom data format and need a small adapter.

> **Fastest path:** the McAuley-Lab benchmark [`hyp1231/AmazonReviews2023`](https://github.com/hyp1231/AmazonReviews2023) ships Amazon-2023 in RecBole format. `SASRec`, `GRU4Rec`, `BERT4Rec`, `Caser`, `NextItNet`, `CORE`, `FEARec`, `HGN` run out of the box.

| Baseline | Papers | Code path | Type | Run on Amazon-2023 |
|---|---:|---|---|---|
| [SASRec](https://arxiv.org/abs/1808.09781) | 55 | [kang205/SASRec](https://github.com/kang205/SASRec) | Official (TF) | RecBole `SASRec` (direct) |
| [GRU4Rec](https://arxiv.org/abs/1511.06939) | 29 | [hidasib/GRU4Rec](https://github.com/hidasib/GRU4Rec) | Official | RecBole `GRU4Rec` |
| [BERT4Rec](https://arxiv.org/abs/1904.06690) | 27 | [FeiSun/BERT4Rec](https://github.com/FeiSun/BERT4Rec) | Official (TF) | RecBole `BERT4Rec` |
| [Caser](https://arxiv.org/abs/1809.07426) | 15 | [graytowne/caser_pytorch](https://github.com/graytowne/caser_pytorch) | Official | RecBole `Caser` |
| [FMLP-Rec](https://arxiv.org/abs/2202.13556) | 11 | [Woeee/FMLP-Rec](https://github.com/Woeee/FMLP-Rec) | Official | adapt (custom format + 99 negatives) |
| [S3-Rec](https://arxiv.org/abs/2008.07873) | 10 | [RUCAIBox/CIKM2020-S3Rec](https://github.com/RUCAIBox/CIKM2020-S3Rec) | Official | RecBole `S3Rec` (needs item attrs) |
| [DuoRec](https://arxiv.org/abs/2110.05730) | 8 | [RuihongQiu/DuoRec](https://github.com/RuihongQiu/DuoRec) | Official | RecBole-DA `DuoRec` |
| FDSA | 8 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `FDSA` | RecBole (no official) | direct (needs item features) |
| [HGN](https://arxiv.org/abs/1906.09217) | 4 | [allenjack/HGN](https://github.com/allenjack/HGN) | Official | RecBole `HGN` |
| [CL4SRec](https://arxiv.org/abs/2010.14395) | 3 | [RUCAIBox/RecBole-DA](https://github.com/RUCAIBox/RecBole-DA) `CL4SRec` | RecBole-DA (no official) | direct |
| [NextItNet](https://arxiv.org/abs/1808.05163) | 3 | [fajieyuan/WSDM2019-nextitnet](https://github.com/fajieyuan/WSDM2019-nextitnet) | Official (TF) | RecBole `NextItNet` |
| [MAERec](https://arxiv.org/abs/2305.04619) | 3 | [HKUDS/MAERec](https://github.com/HKUDS/MAERec) | Official | adapt (custom pkl + graph) |
| [FEARec](https://arxiv.org/abs/2304.09184) | 2 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `FEARec` | RecBole | direct |
| [DiffuRec](https://arxiv.org/abs/2304.00686) | 2 | [WHUIR/DiffuRec](https://github.com/WHUIR/DiffuRec) | Official | adapt |
| [CoST](https://arxiv.org/abs/2404.14774) | 2 | — | ❌ no public code | implement from paper |
| [LRURec](https://arxiv.org/abs/2310.02367) | 2 | [yueqirex/LRURec](https://github.com/yueqirex/LRURec) | Official | adapt |
| [CORE](https://arxiv.org/abs/2204.11067) | 2 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `CORE` | RecBole | direct |
| [BSARec](https://arxiv.org/abs/2312.10325) | 2 | [yehjin-shin/BSARec](https://github.com/yehjin-shin/BSARec) | Official | adapt (FMLP format) |
| [ReaRec](https://arxiv.org/abs/2503.22675) | 2 | [TangJiakai/ReaRec](https://github.com/TangJiakai/ReaRec) | Official·2023 | native (needs LLaMA-3.1-8B emb) |

<sub>`SASRec Base` (2) and `BERT4Rec Base` (2) are aliases of SASRec / BERT4Rec. `ERL` / `PRL` are ReaRec ablations.</sub>
