<div align="center">

# Classical CF

**34 papers · 10 baselines** — MF, neighborhood & neural collaborative filtering

</div>

Non-sequential collaborative filtering: popularity, matrix factorization, neighborhood, and neural CF. **All run directly in [RecBole](https://github.com/RUCAIBox/RecBole)** except `SVD` / `ALS`, which come from standalone libraries.

> **Fastest path:** RecBole `Pop` / `BPR` / `ItemKNN` / `DMF` / `NeuMF` on the McAuley-Lab Amazon-2023 atomic files. `SVD` → [`cornac`](https://github.com/PreferredAI/cornac), `ALS` → [`implicit`](https://github.com/benfred/implicit).

| Baseline | Papers | Code path | Type | Run on Amazon-2023 |
|---|---:|---|---|---|
| Popularity | 9 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `Pop` | RecBole | direct |
| MF | 7 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `BPR` | RecBole | direct |
| [NCF](https://arxiv.org/abs/1708.05031) | 5 | [hexiangnan/neural_collaborative_filtering](https://github.com/hexiangnan/neural_collaborative_filtering) | Official (Keras) | RecBole `NeuMF` |
| [BPR-MF](https://arxiv.org/abs/1205.2618) | 5 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `BPR` | RecBole | direct |
| [BPR](https://arxiv.org/abs/1205.2618) | 4 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `BPR` | RecBole | direct |
| DMF | 2 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `DMF` | RecBole | direct |
| SVD | 2 | [PreferredAI/cornac](https://github.com/PreferredAI/cornac) `SVD` | Library | direct |
| ALS | 2 | [benfred/implicit](https://github.com/benfred/implicit) | Library | direct |
| ItemKNN | 2 | [RUCAIBox/RecBole](https://github.com/RUCAIBox/RecBole) `ItemKNN` | RecBole | direct |
| [NeuMF](https://arxiv.org/abs/1708.05031) | 2 | [hexiangnan/neural_collaborative_filtering](https://github.com/hexiangnan/neural_collaborative_filtering) | Official | RecBole `NeuMF` |
