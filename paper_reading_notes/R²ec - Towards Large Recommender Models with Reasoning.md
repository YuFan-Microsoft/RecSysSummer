# R²ec: Towards Large Recommender Models with Reasoning

**Authors:** Runyang You, Yongqi Li, Xinyu Lin, Xin Zhang, Wenjie Wang, Wenjie Li, Liqiang Nie

**arXiv:** https://arxiv.org/abs/2505.16994 (v3)

**PDF:** https://arxiv.org/pdf/2505.16994

**Venue:** Accepted by Neurips 2025

**Categories:** cs.IR (primary), cs.AI, cs.CL

**Published:** 2025-05-22 · **Updated:** 2025-10-31

---

<!-- Reading progress: abstract, plus §1 Introduction, §2 Preliminaries, and §3.1–3.2 (model design + the RecPO reward). §4 experiments and the nine analyses still to read. Verified against the PDF. Statements are the paper's unless marked (inference). -->

## TL;DR

R²ec is a single decoder-only LLM that "thinks, then recommends." It carries two
output heads on one shared backbone: a language-modeling head (`lm_head`) that
autoregressively writes a natural-language reasoning chain, and a recommendation
head (`rec_head`) that turns the *final* hidden state of that chain into a
one-step similarity score against a table of item embeddings. Because there is no
annotated reasoning to imitate, the whole model is trained by reinforcement
learning (RecPO) with a fused reward that mixes a discrete ranking signal with a
continuous similarity signal. The paper stands or falls on one claim: that
letting a single model reason and rank *jointly and end-to-end* beats bolting a
separate reasoning module onto a recommender.

## Where it sits

The paper positions itself against two things at once: prior "reasoning for
recommendation" work that runs reasoning as an *external* module feeding a
separate recommender, and generative recommenders that decode item IDs token by
token. R²ec's pitch is to be *unified* on both axes — one model, and one-step
item scoring instead of ID decoding.

It reads best next to the other two notes in this folder:

| | item representation | reasoning form | backbone | training |
|---|---|---|---|---|
| **ReaRec** | ID embeddings | *implicit* latent steps (feed the last hidden state back in) | SASRec-style, **not** an LLM | supervised (ERL / PRL) |
| **R²ec** (this paper) | **natural-language** item text → LLM-encoded embedding | *explicit* textual chain-of-thought | pretrained decoder-only LLM | **RL** (RecPO), no reasoning labels |
| **SIDReasoner** | Semantic IDs (discrete tokens) | reasoning over SID tokens | LLM | multi-task alignment + RL |

The clean contrast: ReaRec reasons in *latent space on a non-LLM*, SIDReasoner
reasons over *Semantic IDs*, and R²ec reasons in *natural language while scoring
items as embeddings*.

## What the paper actually does (correcting the easy misreadings)

### The dual head is unification, not disentanglement

It is tempting to read "two heads, one for reasoning and one for recommendation"
as *separating* the two jobs. The paper argues the exact opposite, and this is
its whole thesis.

What actually gets *decoupled* is the **prior work**: it trains a large reasoning
model and a recommender as two modules and can only update one while freezing the
other, so gradients never flow across the pipeline (§1). R²ec instead puts both
heads on **one shared decoder backbone that reads the same hidden-state space**.
The `lm_head` writes the reasoning tokens $o_1, \dots, o_T$, and then the *final*
hidden state $\mathbf{h}_T$ is handed to the `rec_head`. The paper calls this a
"tight reasoning–recommendation coupling," because the act of reasoning literally
reshapes $\mathbf{h}_T$, and that reshaped vector is exactly what scores items. So
the two heads are the opposite of disentangled — they are welded to the same
representation and optimized jointly.

A clean way to see the symmetry: **both heads are just a hidden state projected
onto an embedding table**. The `lm_head` projects onto the token table
$H_T \in \mathbb{R}^{|T| \times d}$ to give a token distribution; the `rec_head`
projects onto the item table $H_V \in \mathbb{R}^{|V| \times d}$ to score items.
Because it is structurally the *same* operation, one backbone's hidden state
$\mathbf{h}_T$ feeds either head with no friction — and items stay editable as
plain rows in $H_V$, which is exactly what makes the "add/delete/replace a vector"
property fall out for free.

### Items are natural language encoded into an embedding table, not Semantic IDs

Each item's row $\mathbf{h}_v$ in the recommendation table $H_V$ is obtained by
feeding the item's textual description through the *same* model and taking its
final hidden state. Prediction is then a single inner product
$s(v) = \mathbf{h}_T^\top \mathbf{h}_v$ over all candidates, followed by a rank.
This is precisely the axis where R²ec departs from SID / generative recommenders:
there is no hard-coded item tokenization, and items can be added, deleted, or
replaced by simply editing vectors in the table. The paper sells this as
zero-shot generalization and large-catalog friendliness.

### Serving cost — the intuition is right in direction, but needs a caveat

Yes, the *item-prediction step* is cheap: one embedding and a dot product instead
of the slow autoregressive decoding of an item ID, and it is one model instead of
two. But R²ec still autoregressively generates the whole reasoning chain
$o_{1:T}$, and *that* is the real latency, not the final scoring. So the paper's
efficiency claim is carefully scoped: "competitive efficiency **among LLM-based**
recommenders," and lower latency than reasoning-augmented and conventional
LLM-based baselines — **not** lower than a plain embedding recommender such as
SASRec. *(inference)* Relative to SASRec, R²ec is certainly more expensive; its
efficiency story is only about beating other LLM-based and two-module reasoning
recommenders.

### Inference is reason-then-score, not embedding-only

A natural misreading is that, at test time, R²ec simply emits an embedding. It
does not. Inference runs in two stages (§3.1, Appendix E): the model first
*greedily and deterministically* generates a full reasoning chain $o_{1:T}$ with
the `lm_head`, and only then is the trailing hidden state $\mathbf{h}_T$ scored
against the item table by a single inner product
$s(v) = \mathbf{h}_T^\top \mathbf{h}_v$. The "one embedding" describes only the
final recommendation step; the reasoning text is generated on every request and
cannot be skipped. Item embeddings $H_V$ are precomputed once offline, so only
the user-side reasoning is paid at request time.

This is not just an architectural claim — an ablation nails it. The "w/o
Reasoning" variant (reasoning tokens removed, model trained with plain in-batch
contrastive loss) is about **15% worse on average** than full R²ec, and a "w/
ClsHead" variant (a separate classification head on the reasoning tokens instead
of the shared `rec_head`) is far worse still. So reasoning genuinely contributes
at inference, and the tight coupling — not a bolt-on head — is what carries it.

### Efficiency, honestly (Table 4)

So is serving slow? The reader's instinct is right: generating a reasoning chain
is strictly more expensive than a retrieval recommender, and the paper concedes
exactly this in its Limitations — "explicit reasoning generation inevitably
increases inference latency due to additional autoregressive decoding steps." The
measured latencies (single RTX 3090, batch 1, 100 queries × 3 runs, §4.6) are:

| Method | Latency (s) |
|---|---|
| SASRec (retrieval, no LLM) | 0.014 |
| LangPTune | 1.90 |
| D3 | 4.62 |
| LLaRA | 5.23 |
| **R²ec** | **1.67** |
| **R²ec + VLLM** | **0.0945** |

Two honest readings:

- **Within LLM-based recommenders, R²ec really is the fastest** (1.67 s versus
  1.90 / 4.62 / 5.23). The large gap over D3 and LLaRA comes from *not*
  autoregressively decoding item IDs over a large vocabulary — the `rec_head`
  scores the whole catalog in a single matrix product — plus running as one model
  instead of two.
- **Against SASRec it is still about 120× slower** in the naive setting, and only
  VLLM serving pulls it to 0.0945 s (~7× SASRec, same order of magnitude).
  *(open / caveat)* That VLLM row swaps the inference stack, and the other LLM
  baselines are not reported with VLLM, so 0.0945 s is not an apples-to-apples row
  in the same table. The fair, same-stack comparison is R²ec at 1.67 s, which is
  where the "fastest LLM recommender" claim actually lives.

**The comparison that is missing (and it matters).** A sharp objection: if the
foil is a *Semantic-ID generative* recommender, decoding an item ID is only 3–4
codebook tokens, whereas R²ec's reasoning chain is the real cost. Figures 2–3 put
the reasoning length at roughly **500–650** *(inference: these are token-scale
counts on the length axis)*. So "we avoid autoregressive item-ID decoding" cannot
be what makes R²ec fast relative to a 3–4-token SID decoder — the ~500-token chain
dwarfs those 3–4 tokens by two orders of magnitude. And tellingly, **TIGER, the
actual SID generative baseline, is absent from the efficiency Table 4**: it pits
R²ec only against D3 and LLaRA*, which do *constrained generation over the full
item corpus* (LLaRA*/SDPO* explicitly, §4.1) and are slow for *that* reason, not
because of 3–4 SID tokens. Honest reading: R²ec's one-step `rec_head` is genuinely
cheaper than generating item text or full-corpus constrained decoding, but against
a plain 3–4-token SID decoder with no reasoning, R²ec's reasoning chain would
almost certainly make it *slower* — a comparison the paper does not run.

*(steelman — and why it fails)* One might defend R²ec by its full-item ranking
setup: the `rec_head` scores the whole catalog in one matrix product, while a SID
decoder only beam-searches a top-B list. But the reported metrics are
NDCG / Hit @{5,10,20} — top-20 cutoffs — so a beam of ~50 covers them with room to
spare, and no full-catalog scoring is actually needed. The SID decode itself is
only 3–4 codebook tokens over the beam (≈3–4 batched decoder steps), and
constrained decoding adds just a negligible per-step prefix mask — both are
rounding error next to R²ec's ~500 autoregressive reasoning steps. The lone
residual is that beam search is approximate while the matrix product is exact, too
minor to carry the story. So the "full-ranking advantage" does not rescue the
efficiency claim: against a plain SID generative recommender with no reasoning,
R²ec's chain would dominate and it would very likely be *slower*. The paper simply
never reports TIGER's latency.

Net: reasoning is not free, and the paper says so. R²ec's efficiency story is
"the cheapest way to *do reasoning* inside a recommender," not "as cheap as a
classic sequential model."

## How it is trained (RecPO, first pass)

Because there is no ground-truth reasoning to supervise, training is RL over the
entire "reasoning-then-recommend" trajectory
$x_u \to o_1 \to \dots \to o_T \to v^+$. For each user, $G$ trajectories are
sampled from the old policy and scored by a **fused reward**:

$$R = \beta R_c + (1-\beta) R_d, \qquad R_d = \text{NDCG}@k, \quad R_c = \frac{\exp(\mathbf{h}_T^\top \mathbf{h}_{v^+}/\tau)}{\sum_{v \in V} \exp(\mathbf{h}_T^\top \mathbf{h}_v / \tau)}.$$

The discrete term $R_d$ is the ranking metric itself; the continuous term $R_c$
is a softmax similarity that breaks ties between trajectories that land on the
*same* top-K rank. With $\beta \approx 0.05$ the ranking term dominates while
$R_c$ only adds resolution. The point of the continuous term is subtle but real:
without it, many trajectories of *different* reasoning quality collapse to the
*same* discrete NDCG reward, starving the policy gradient of any signal to prefer
one over another — $R_c$ is what restores that within-rank gradient. Advantages
come from GRPO or RLOO group normalization, and the objective is the usual clipped
policy-gradient ratio — so RecPO is **PPO-style, not literally PPO**. *(This
sharpens the shorthand "trained with PPO" carried in the SIDReasoner note.)* The
full objective (§3.2.3) is for the next pass.

## Reader's insights and open questions

- *(open, partly answered)* **Does the reasoning cause the gain, or is it just
  extra test-time compute?** The "w/o Reasoning" ablation (~15% drop) confirms the
  reasoning tokens *do* help, so it is not a no-op. What stays open is the deeper
  question: is the lift from *semantic* content in the chain, or merely from the
  extra forward compute that reshapes $\mathbf{h}_T$? The §4 reasoning-behavior
  case studies are where to look.
- *(open)* **Why is $\beta \approx 0.05$ so small?** The continuous reward is
  almost a pure tie-breaker. Is the model really learning from $R_c$, or is
  NDCG carrying essentially all of the signal? Check the reward ablation.
- *(partly answered)* **How long are the reasoning chains, and does length trade
  against the "low latency" pitch?** Figures 2–3 show reasoning length around
  500–650 (token-scale), which *is* the dominant serving cost — far above a 3–4
  token SID decode. This is exactly why the efficiency claim should be read as
  "cheapest among long-generating LLM recommenders," not "cheaper than SID
  generation."
- *(my idea)* Since items are just vectors in a table, could the reasoning chain
  be *reused or cached* across users with similar histories, cutting the dominant
  cost (the autoregressive reasoning) rather than the already-cheap scoring step?

<!-- To be continued: read §4 experiments (three datasets, baselines, the nine analyses — especially the efficiency profiling and the reasoning-behavior case studies), then write the §3.2.3 objective detail and a Net read verdict. -->
