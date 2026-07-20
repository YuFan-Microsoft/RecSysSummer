# TokenMinds — §4 Experiments (TEMP, to merge)

<!-- TEMP note: this file holds only the §4 experiments reflection, written on a
machine that is not synced with the main note. Merge into
`TokenMinds - Pretrained User Tokens and Embeddings for User Understanding in Large Recommender Systems.md`
(append under its body, then delete this file). -->

<!-- Reading progress: §4 experiments, read together with the user. Verified against the PDF. Statements are the paper's unless marked (inference) or (open). -->

## Experiments

### The three research questions (§4)

Reassuringly, the questions that came out of the first read map almost exactly
onto the three RQs the paper itself sets up, which is a good sign that the
earlier sections framed the right tensions.

- **RQ1 — Token Adaptation & Viability.** This is really two sub-questions in
  one. *Adaptation*: how should the discrete SID user tokens be turned into
  something a downstream **continuous** ranker can consume — evaluated offline
  across the three token-to-embedding methods from §3.4 (Prefix Embedding
  Mapping, N-gram, SPM). *Viability*: do they then produce **measurable gains on
  industrial-scale surfaces** — answered by the online A/B in §4.3. So "how to
  integrate" and "does it actually pay off in production" are deliberately kept
  as separate burdens of proof.
- **RQ2 — Complementary Values.** Does the **dual output** genuinely pull its
  weight — i.e. does emitting a dense embedding *and* discrete SID tokens beat
  either one alone, showing the two carry complementary signal rather than
  redundant copies of the same user summary.
- **RQ3 — Cross-Scenario Modeling Impact.** Jointly training LFV and SFV in one
  unified model. The bet here is **two-sided**, and it is worth stating
  precisely: the claim is not merely "joint training does not hurt", but
  "**joint training buys a computational-efficiency gain** (one shared model /
  shared SID vocabulary instead of one per scenario) **without compromising**
  downstream recommendation quality". The risk being tested is negative transfer
  between the two very different video formats.

<!-- Reflections / reading notes go here — RQ1/RQ2/RQ3 findings next -->

### §4.1 Setup — the numbers that matter

The concrete configuration is worth pinning down, because several of these
choices are exactly what the ablations later justify.

- **Input per user.** The most recent **1,200 watches**, interleaved with
  **$S = 10$** textual search queries (§3.3). Maximum input sequence length is
  **1,024 tokens**.
- **Per-watch token layout.** Each watch is encoded as one **condition token**
  (the `<LFV>`/`<SFV>` scenario marker) + the **prefix-$L = 4$** SID tokens +
  **$M = 1$** soft token that packs all the non-SID features. Using a single
  soft token trades away roughly **5% offline recall** in exchange for a large
  cut in sequence length — a deliberate length-versus-fidelity bargain.
- **Target.** Up to **$N = 15$** target watches sampled from a **24-hour
  look-ahead window** (not next-watch prediction — this is the look-ahead design
  the ablation shows is critical for cold-start).
- **Model.** Encoder-decoder built on **Gemini V1.5**: a **370M-parameter MoE
  encoder** plus a **370M-parameter dense decoder**, both initialized from
  **CPT** checkpoints.
- **Training.** Continuous daily training on the freshest data, ~millions of
  examples per day, which the paper frames as far more sample-efficient than
  traditional LEMs that need billions of interactions. Learning rate is
  grid-searched over $[10^{-6}, 10^{-3}]$; warmup + cosine decay with cyclic
  restarts peaks on same-day metrics, but a **constant LR is more robust** to
  day-to-day distribution shift under continuous training.
- **Serving.** Per user, extract a **1,152-dimensional dense embedding** from the
  encoder, and decode **$B = 40$** SID sequences by beam search — importantly
  split **20 LFV + 20 SFV** — each at prefix length $L$, to form the discrete
  user-token representation. Refresh cadence is **24 hours** (§3.5 async infra).

### §4.2 Representation Quality (RQ1, offline)

**Two accuracy protocols.** Both score the top-10 beam-searched SID sequences at
prefix-$L$ granularity, i.e. **Recall@10**.

- **Session Recall** — feed the near-complete history $[W_1, \dots, W_{n-1}]$ and
  predict the final watch $W_n$. This tests "given almost everything, do you nail
  the very next thing".
- **Cold-Start Recall** — feed a **truncated** history $[W_1, \dots, W_t]$ and
  predict a *randomly sampled* watch from the future $\{W_{t+1}, \dots, W_n\}$.
  This tests generalization from little history to a longer-horizon interest.

**Training ablation (Table 1).** Each row removes one design and confirms it
helps, and the pattern is informative — the two horizon-related choices matter
most for cold-start:

- **Multiple targets ($N = 15$ vs $1$).** Sampling 15 look-ahead targets beats a
  single target: −8.9% Session / −3.3% Cold-Start when reduced to one.
- **Look-ahead window vs plain next-watch.** Replacing look-ahead sampling with
  standard next-watch prediction costs −4.5% Session but **−10.0% Cold-Start** —
  predicting a *window* of the future, not just the immediate next item, is what
  generalizes.
- **SID truncation (prefix-$L$ vs full $L_{full}$).** Training on full-length
  SIDs instead of the coarse prefix is the *most* damaging: −15.1% Session /
  **−17.1% Cold-Start**. Coarse interest regions generalize; fine full-SIDs
  memorize.

**Initialization + search (Table 2).** All deltas are relative to a *Random-init,
no-search* baseline. Two clean orderings fall out:

- **Init:** CPT > Pre-Trained Gemini > Random, consistently. The SID-specific
  semantic grounding baked in during CPT helps downstream fine-tuning beyond the
  base LLM's generic sequence modeling.
- **Search queries:** adding the $S = 10$ interleaved queries helps across *every*
  init, and the benefit is **amplified by stronger init** (CPT+search is best at
  +23.5% Session / +31.5% Cold-Start) — an aligned SID backbone is better able to
  fuse textual intent with behavioral history.

**Token diversity (Fig. 5) — the metric that needs unpacking.** Because each of
the $B = 40$ beams is supposed to be a *distinct* interest signal, beam collapse
(many beams converging to near-identical outputs) would waste representational
capacity. Two redundancy metrics check this:

- **SID Token Collision Rate at position $x$** — how often the code at a *single*
  level $x$ is identical across beams. High collision at a level = **semantic
  beam collapse** at that granularity.
- **SID Prefix Duplication Rate up to $x$** — the fraction of beams whose *entire*
  prefix path $[1 \dots x]$ is identical. High duplication = beams all walking one
  **single branch** of the SID tree (isolated exploration).

The distinction: token collision is per-level agreement (ignoring the rest of the
path); prefix duplication is whole-path agreement (stricter, and naturally falls
as $x$ grows because a longer path is harder to match exactly.)

Crucially the **benchmark is the ground truth, not zero redundancy.** Real future
behavior has natural repetition, so the goal is to *match reality*, not to
maximize spread. The comparison is **per user, between two SID sets**: for each
user, both metrics measure the *internal redundancy of a set* — computed once on
the **generated** set (that user's $B = 40$ decoded beams, i.e. decoding
diversity) and once on the **ground-truth** set (that user's actual watches in the
same 24-hour look-ahead window, converted to SIDs, i.e. the diversity of what the
user really consumed). Because a user's real-watch count is not $40$, the larger
set is down-sampled to the smaller (repeated 10× and averaged for fairness). The
per-user scores are then aggregated across 5K users into **CDFs**, and the
generated-side curve sits **on par with the ground-truth curve** — so the beams
are as diverse as the user's genuine consumption: neither collapsed nor
artificially over-spread.

<!-- To be continued: §4.2 Embedding Quality, §4.3 Downstream Cost + Cross-Scenario (RQ3), and §4.4 Model Variants & Capacity Allocation. -->

### §4.3 Online Performance (RQ1 viability + RQ2 complementary)

Live 7-day A/B on production **ranking** models (TokenMinds is also in retrieval
and LLM systems, but this paper reports ranking). Two quality metrics on both
surfaces: **Engaged Users** and **Satisfied Engagement**; bold in the tables =
statistically significant at 95%.

**Token adaptation: LE beats fixed EM (answers the first half of RQ1).** A
lightweight 110M pivot on SFV compared the *static* **Prefix Embedding Mapping
(EM)** against a **Learnable Embedding (LE)** (Unigram, $N = 1$, matching that
surface's item tokenization):

| Strategy | Engaged Users | Satisfied Engagement |
| --- | --- | --- |
| EM (static) | +0.07% | −0.02% |
| LE (learnable) | +0.08% | **+0.22%** |

LE wins, and the gap is almost entirely on Satisfied Engagement (EM is even
slightly negative there) — letting the downstream model *learn* its own embedding
space adapts better than a frozen mapping. LFV with SPM-based LE showed the same
trend, so **LE is used for all full-scale runs**.

**Complementary value: Embed + Token is best (answers RQ1's second half + RQ2).**
Comparing continuous embedding alone, discrete SID tokens alone (via LE), and both
(Table 4):

| Surface | Representation | Engaged Users | Satisfied Engagement |
| --- | --- | --- | --- |
| SFV | Embed-only | 0.00% | +0.05% |
| SFV | Token-only | +0.04% | +0.40% |
| SFV | Embed+Token | **+0.11%** | **+0.62%** |
| LFV | Embed-only | +0.04% | +0.03% |
| LFV | Token-only | +0.01% | +0.04% |
| LFV | Embed+Token | +0.02% | +0.08% |

Two findings. First, **SID tokens carry additive value on their own** (token-only
already beats embed-only on Satisfied Engagement, dramatically so on SFV:
+0.40% vs +0.05%) — the latter half of RQ1. Two extra LFV surfaces confirmed
token-only generalizes (significant +0.04%/+0.16% Engaged, +0.07%/+0.11%
Satisfied). Second, **combining them amplifies the gain**, validating **RQ2**: on
SFV the effect is clean and monotone with Embed+Token best on both metrics
(+0.11% / +0.62%). On LFV the deltas are smaller and noisier (on Engaged Users,
embed-only is actually marginally ahead), but Embed+Token still tops Satisfied
Engagement — so the complementary story is strong on SFV and directionally
present, if weaker, on LFV.

### §4.4 Scaling Studies (partial — input length & batch size)

These use an **accelerated offline protocol**: train on 7 randomly shuffled days,
evaluate on the sequential **8th day** (so all numbers here are *8th-Day
Recall@10*).

**Input length (user history) scaling.** 8th-Day Recall@10 for both LFV and SFV
climbs as history grows but **saturates at roughly 1K watches**. Pushing to **2K**
gives only comparable or **slightly degraded** performance, and the degradation
shows up specifically on **SFV**. So longer history helps up to a point; past ~1K
there is no free lunch, which matters for compute-optimal sizing (the 1,024-token
input cap in §4.1 is consistent with this).

**Batch size scaling.** Batches of **4K / 8K / 16K**, with **8K as the tuned
anchor** and other sizes reached by scaling the learning rate via the standard
**$\sqrt{N}$ rule**. Relative to the 4K baseline, 8th-Day Recall@10 improves by
**+2.5% / +5.5% (SFV / LFV) at 8K** and **+7.6% / +13.7% at 16K**. Larger batches
accelerate convergence and yield stronger representations within the same training
window (consistent with PLUM), so the practical takeaway is to **max out batch
size up to hardware capacity**.
