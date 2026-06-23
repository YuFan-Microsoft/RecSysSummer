# Amazon Reviews 2023 — Data Processing Protocol

This document defines the data-processing and evaluation protocol we adopt for
sequential / generative recommendation experiments on the **Amazon Reviews 2023**
corpus. The protocol is deliberately aligned with the **majority practice** observed
across recent papers (2025–2026) that evaluate on the five Amazon-2023 categories we
focus on: **Video Games, Industrial & Scientific, Beauty, Musical Instruments, Books**.

> **TL;DR — the locked scheme:**
> Official **5-core / `last_out`** splits → **5-core** filtering → per-user
> **chronologically ordered** sequences (max length **20**, or **50** for ID-based
> sequential models) → **leave-one-out** split (last = test, second-to-last =
> validation, rest = train) → **full-ranking** evaluation over the entire item
> catalogue → report **Recall@K** and **NDCG@K**, `K ∈ {5, 10}`.

---

## 0. Why this protocol (empirical basis)

We manually inspected the *Data Processing* description of **86 papers** in our corpus
that evaluate on at least one of the five target categories. Among the **63 papers that
use a standard next-item split**, the distribution is:

| Split method                         | Papers | Share (of the 63) |
|--------------------------------------|:------:|:-----------------:|
| **Leave-one-out** (last item held out) | **42**† | **67%** |
| Global / per-user temporal split      | 18     | 29% |
| Random split                          | 3      | 5%  |

† 36 of these state leave-one-out **explicitly** (i.e. "last item = test, second-to-last
= validation"); the other 6 are *inferred* (they "follow prior work" or hold out the
last positive interaction). **Even counting only the 36 explicit cases, leave-one-out
still leads the temporal split by ~2 : 1**, so the majority finding is robust to this
judgement call.

(The remaining 23 papers do not use a clearly-described standard next-item leave-one-out
or temporal split: most are agent simulations, benchmark construction, cross-domain,
rating-prediction or retrieval works; a few use an unspecified or random ratio split.)

Secondary dimensions among these papers (counting only papers that state each setting):
- **Filtering:** *5-core* is dominant (**36** papers), versus 10-core (8) or higher user
  thresholds (5).
- **Max sequence length:** **20** is the most common (**13** papers; generative /
  semantic-ID models), followed by **50** (6 papers; ID-based SASRec-style models) and
  10 (5 papers).
- **Evaluation:** among papers that explicitly state a *test-time* ranking protocol,
  **full ranking** over the whole item set (**~15** papers) is slightly more common than
  **sampled-negative** evaluation (**~12** papers) — a narrow plurality, not a landslide.
  (Many further papers use negative *sampling during training* only, which is not an
  evaluation protocol and is excluded from this count.)

**Conclusion:** for these five categories — which are the canonical sequential /
generative-recommendation benchmarks — **5-core + leave-one-out** is the clear majority
protocol (with **full ranking** the most common, though not dominant, evaluation
choice), and it is directly reproducible from the official Amazon Reviews 2023 release.
We therefore adopt it as our standard.

---

## 1. Data source

- **Corpus:** Amazon Reviews 2023, `McAuley-Lab/amazon-reviews-2023` on Hugging Face.
- **Official splits:** use the benchmark **`5core_last_out_w_his`** configuration (the
  leave-one-out split). The parallel **`5core_timestamp_w_his`** configuration provides
  the temporal-split variant (see §8, *Alternative*).
- **Categories used (official identifiers):** `Video_Games`, `Industrial_and_Scientific`,
  `Musical_Instruments`, `Books`, and `Beauty_and_Personal_Care` / `All_Beauty`.

**Reference:**
- *Bridging Language and Items for Retrieval and Recommendation* — Hou et al., 2024
  (the Amazon Reviews 2023 dataset & benchmark). https://arxiv.org/abs/2403.03952 ·
  dataset site: https://amazon-reviews-2023.github.io/

---

## 2. Filtering — 5-core

Iteratively remove users and items with fewer than **5** interactions until every
remaining user and item has at least 5 interactions (the standard *5-core* setting).
This matches the official `5core` benchmark splits, so no custom filtering is required
when the official splits are used.

**Representative references:**
- *Universal Item Tokenization for Transferable Generative Recommendation* — Tencent,
  2025. https://arxiv.org/abs/2504.04405
- *LARES: Latent Reasoning for Sequential Recommendation* — Meituan, 2025.
  https://arxiv.org/abs/2505.16865
- *Pre-training Generative Recommender with Multi-Identifier Item Tokenization* —
  Huawei (SIGIR 2025). https://arxiv.org/abs/2504.04400

---

## 3. Feedback and interactions

- **Default:** treat every retained review as an **implicit positive** interaction.
- **Explicit-feedback variant (optional):** if positive/negative labels are required,
  treat `rating ≥ 4` as positive.
- Keep only `user_id`, `parent_asin` (item id) and `timestamp` for the interaction log;
  item text fields (title, features, categories, description) are used separately for
  content / semantic-ID models.

---

## 4. Sequence construction

- Group interactions by user and **sort chronologically by `timestamp`** (earliest
  first).
- **Maximum sequence length:** **20** items (semantic-ID / generative models). Use
  **50** for ID-based sequential models (e.g. SASRec-style) where a longer history is
  standard. Longer histories are truncated to the most recent `L` items; shorter ones
  are left-padded.

**Representative references:**
- Max length **20**: *DeepRec* — Tencent, 2025. https://arxiv.org/abs/2505.16810 ·
  *MLPs are Efficient Distilled Generative Recommenders* — Snap, 2026.
  https://arxiv.org/abs/2605.12617
- Max length **50**: *A Novel Mamba-based Sequential Recommendation Method* — Huawei,
  2025. https://arxiv.org/abs/2504.07398

---

## 5. Train / validation / test split — Leave-one-out

For each user's chronologically ordered sequence:

| Split        | Item                              |
|--------------|-----------------------------------|
| **Test**     | the **last** interaction          |
| **Validation** | the **second-to-last** interaction |
| **Train**    | all remaining (earlier) interactions |

This is the *leave-one-out* (a.k.a. *leave-last-out*) protocol and corresponds exactly
to the official **`5core_last_out`** benchmark split.

**Representative references:**
- *Bridging Textual-Collaborative Gap through Semantic Codes for Sequential
  Recommendation* — KDD 2025. https://arxiv.org/abs/2503.12183
- *Not Just What, But When: Integrating Irregular Intervals to LLM for Sequential
  Recommendation* — RecSys 2025. https://arxiv.org/abs/2507.23209
- *Generative Recommendation with Semantic IDs: A Practitioner's Handbook* — Snap, 2025.
  https://arxiv.org/abs/2507.22224
- *RecCocktail: A Generalizable and Efficient Framework for LLM-Based Recommendation* —
  Kuaishou (AAAI 2025). https://arxiv.org/abs/2502.08271

---

## 6. Evaluation — full ranking

- Score the held-out target item against the **entire item catalogue** (no negative
  sampling). This avoids the well-known bias of sampled-metric evaluation. It is the
  most common evaluation choice among the surveyed papers (~15, vs ~12 that rank against
  a small sampled-negative candidate set), so we adopt it as the default — while noting
  that sampled-negative evaluation remains a sizeable minority.

**Representative references:**
- *Universal Item Tokenization for Transferable Generative Recommendation* — Tencent,
  2025. https://arxiv.org/abs/2504.04405
- *LARES: Latent Reasoning for Sequential Recommendation* — Meituan, 2025.
  https://arxiv.org/abs/2505.16865

---

## 7. Metrics

- Report **Recall@K** (a.k.a. Hit Rate@K) and **NDCG@K** for `K ∈ {5, 10}`
  (optionally add `K = 20`).
- When a model is stochastic, average over multiple seeds.

---

## 8. Settings summary & the foundational protocol

| Component        | Setting                                                        |
|------------------|----------------------------------------------------------------|
| Source           | `McAuley-Lab/amazon-reviews-2023`, `5core_last_out_w_his`       |
| Filtering        | 5-core (users & items with ≥ 5 interactions)                   |
| Feedback         | all interactions implicit (or `rating ≥ 4` for explicit)       |
| Ordering         | per-user, ascending `timestamp`                                |
| Max seq length   | 20 (generative / semantic-ID) · 50 (ID-based sequential)       |
| Split            | leave-one-out (last = test, 2nd-last = val, rest = train)      |
| Evaluation       | full ranking over the entire item catalogue                    |
| Metrics          | Recall@K, NDCG@K, `K ∈ {5, 10}` (optionally 20)                |

This protocol descends from the **TIGER** semantic-ID generative-recommendation recipe,
which established 5-core + leave-one-out + full-ranking evaluation on Amazon data:

- *Recommender Systems with Generative Retrieval* (TIGER) — Rajput et al., NeurIPS 2023.
  https://arxiv.org/abs/2305.05065

### Alternative route — global temporal split

If leakage-free, time-realistic evaluation is preferred over reproducibility of the
official `last_out` split, use a **global/per-user temporal split** (sort by
`timestamp`, then split by time into e.g. 8:1:1, or use the official
**`5core_timestamp_w_his`** configuration). This is used by ~29% of the surveyed
papers and is the more realistic-but-less-standardized option.

- *DenseRec: Revisiting Dense Content Embeddings for Sequential Transformer-based
  Recommendation* — 2025 (absolute-timestamp split). https://arxiv.org/abs/2508.18442
- *Reasoning over Semantic IDs Enhances Generative Recommendation* — Tencent (KDD 2026,
  chronological 8:1:1). https://arxiv.org/abs/2603.23183
- *Reinforced Preference Optimization for Reasoning-Augmented Recommendations* —
  Kuaishou, 2026 (temporal-truncation 8:1:1). https://arxiv.org/abs/2605.21967

---

## References

**Dataset / foundational**
1. Hou et al., 2024 — *Bridging Language and Items for Retrieval and Recommendation*
   (Amazon Reviews 2023). https://arxiv.org/abs/2403.03952
2. Rajput et al., 2023 — *Recommender Systems with Generative Retrieval* (TIGER),
   NeurIPS 2023. https://arxiv.org/abs/2305.05065

**Representative papers using the adopted protocol (5-core + leave-one-out + full ranking)**
3. Tencent, 2025 — *Universal Item Tokenization for Transferable Generative
   Recommendation*. https://arxiv.org/abs/2504.04405
4. Huawei, SIGIR 2025 — *Pre-training Generative Recommender with Multi-Identifier Item
   Tokenization*. https://arxiv.org/abs/2504.04400
5. Meituan, 2025 — *LARES: Latent Reasoning for Sequential Recommendation*.
   https://arxiv.org/abs/2505.16865
6. Tencent, 2025 — *DeepRec: Towards a Deep Dive Into the Item Space with Large Language
   Model Based Recommendation*. https://arxiv.org/abs/2505.16810
7. Huawei, 2025 — *A Novel Mamba-based Sequential Recommendation Method*.
   https://arxiv.org/abs/2504.07398
8. Snap, 2026 — *MLPs are Efficient Distilled Generative Recommenders*.
   https://arxiv.org/abs/2605.12617
9. Snap, 2025 — *Generative Recommendation with Semantic IDs: A Practitioner's
   Handbook*. https://arxiv.org/abs/2507.22224
10. KDD 2025 — *Bridging Textual-Collaborative Gap through Semantic Codes for Sequential
    Recommendation*. https://arxiv.org/abs/2503.12183
11. RecSys 2025 — *Not Just What, But When: Integrating Irregular Intervals to LLM for
    Sequential Recommendation*. https://arxiv.org/abs/2507.23209
12. Kuaishou, AAAI 2025 — *RecCocktail: A Generalizable and Efficient Framework for
    LLM-Based Recommendation*. https://arxiv.org/abs/2502.08271

**Representative papers using the alternative temporal split**
13. 2025 — *DenseRec: Revisiting Dense Content Embeddings for Sequential
    Transformer-based Recommendation*. https://arxiv.org/abs/2508.18442
14. Tencent, KDD 2026 — *Reasoning over Semantic IDs Enhances Generative
    Recommendation*. https://arxiv.org/abs/2603.23183
15. Kuaishou, 2026 — *Reinforced Preference Optimization for Reasoning-Augmented
    Recommendations*. https://arxiv.org/abs/2605.21967
