<div align="center">

# CTR / feature-interaction

**6 papers · 2 baselines** — click-through-rate models with explicit feature crosses

</div>

Click-through-rate predictors that model **feature interactions** (and, for DIN, attention over behavior history). `DIN` runs in [RecBole](https://github.com/RUCAIBox/RecBole) as a context-aware model; `CTRL` has no official release.

> **Heads up:** CTR models need **labeled (click) data** and feature fields, not just positive interactions — build a CTR view of Amazon-2023 (negative sampling + item/user features) before training.

| Baseline | Papers | Code path | Type | Run on Amazon-2023 |
|---|---:|---|---|---|
| [DIN](https://arxiv.org/abs/1706.06978) | 3 | [zhougr1993/DeepInterestNetwork](https://github.com/zhougr1993/DeepInterestNetwork) | Official (TF) | RecBole `DIN` (needs CTR labels) |
| [CTRL](https://arxiv.org/abs/2306.02841) | 2 | — | ❌ no official repo | implement from paper |
