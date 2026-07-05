# DAST: Difficulty-Adaptive Slow-Thinking for Large Reasoning Models

**Authors:** Yi Shen, Jian Zhang, Jieyun Huang, Shuming Shi, Wenjing Zhang, Jiangze Yan, Ning Wang, Kai Wang, Zhaoxiang Liu, Shiguo Lian

**arXiv:** https://arxiv.org/abs/2503.04472 (v3)

**PDF:** https://arxiv.org/pdf/2503.04472

**Venue:** EMNLP 2025 Industry Track

**Categories:** cs.LG (primary), cs.AI

**Published:** 2025-03-06 · **Updated:** 2026-01-12

---

<!-- Reading progress: abstract, §1 intro, §3.1 (TLB definition) and §3.2 (reward calibration) read together. §3.3–3.4 preference training and §4 experiments still to read. Text verified against the PDF. Statements are the paper's unless marked (inference) / (my idea). -->

## TL;DR

DAST makes a slow-thinking reasoning model spend tokens *in proportion to
problem difficulty* — short chains on easy problems, long chains on hard ones —
instead of the usual one-size-fits-all compression that shortens everything
indiscriminately. The whole method pivots on a single quantity, the **Token
Length Budget (TLB)**, which does double duty as (a) a per-problem difficulty
score and (b) the target length the model is rewarded for matching. The paper
stands or falls on whether that one budget number is a good enough proxy for
"how long *should* this problem's reasoning be."

## Motivation (from the abstract)

The problem is **overthinking**: slow-thinking models (o1, DeepSeek-R1) burn
huge amounts of compute generating redundant reasoning for easy problems. The
running example (Figure 1) is telling — DeepSeek-V3 answers "3x + 7 = 22" in 58
tokens, while DeepSeek-R1 spends 1000+ tokens on the same question.

The key framing, which is easy to misread:

- Existing mitigations are **one-size-fits-all**: they uniformly cut reasoning
  tokens across *all* problems (whether by prompt instructions, SFT on shortest
  answers, or length-penalty RL). This is not just "a length penalty" — it is
  indiscriminate compression.
- The failure mode is specific: uniform cutting **degrades hard problems** that
  genuinely need extended reasoning.
- DAST's answer is therefore **bidirectional**, not a smarter penalty. It
  *penalizes* overlong responses on simple tasks *and* *incentivizes* more
  reasoning on complex ones. Reward and punishment both exist.

Headline claim: **>30% average token reduction** while preserving (sometimes
improving) accuracy on complex problems. Two named implementation pieces:
*budget-aware reward shaping* and *budget preference optimization*.

## Method (as we read it)

### §3.1 — Token Length Budget (TLB)

The budget for a question is a linear interpolation — weighted by the model's own
sampling accuracy — between how long its *correct* answers run and the maximum
generation length:

$$L_{budget} = p \cdot L_r + (1 - p) \cdot L_{max}, \qquad p = \frac{c}{N}$$

Here $c$ is the number of correct samples out of $N$ drawn from the backbone
model, $L_r$ is the average token length of those correct samples, and $L_{max}$
is the maximum generation length. Two limiting cases fix the intuition. When the
model almost always solves the problem, so $p \to 1$, the budget collapses to the
length its correct answers actually take, $L_r$. When it never solves it, so
$p \to 0$, the budget saturates at $L_{max}$, telling the model to think as long
as it is allowed. One number is therefore simultaneously a *difficulty score*
(higher means harder) and a *target length*.

### §3.2 — Reward calibration (budget-aware reward shaping)

The rule-based correctness reward is *calibrated* by how far a response's length
deviates from the budget. Writing the relative deviation as
$\lambda = (L_i - L_{budget}) / L_{budget}$, the calibrated reward is:

$$
\text{reward}(i) =
\begin{cases}
\max(-0.5\lambda + 0.5,\,0.1), & \text{if correct}\\
\min(0.9\lambda - 0.1,\,-0.1), & \text{if incorrect}
\end{cases}
$$

Reading the two branches carefully is exactly what settles the "ceiling vs
floor" question:

- **Correct answers** score highest when they are *shorter* than the budget
  ( $\lambda < 0$ lifts the reward above 0.5, up toward 1.0) and *decay* as they
  exceed it ( $\lambda > 0$ ), floored at 0.1. For a correct answer the budget is
  a soft **ceiling** — overshooting only loses reward.
- **Incorrect answers** are always penalized, but the penalty *shrinks* as length
  grows toward the budget ( $\lambda \to 0^-$ gives $-0.1$, the least-bad score)
  and **saturates** once the budget is reached — going past it earns nothing
  more. The budget is a **target approached from below**, never a floor to exceed.

Two consequences worth recording:

- **This resolves the "ceiling vs floor" question.** In *both* branches,
  exceeding the budget is never rewarded. Hard problems reason long only because
  their budget is itself large ( $p \to 0$ makes $L_{budget} \to L_{max}$ ), so
  "approach the budget" already means "reason a lot." The right slogan is *big
  budget for hard problems, reward for filling it*, not *reward for overshooting*.
  (The earlier read-ahead hypothesis is confirmed.)
- **Correctness strictly dominates length** *(my idea)*. A correct answer always
  scores in $[0.1, 1.0]$ and an incorrect one always in $[-1.0, -0.1]$ — there is
  a sign gap at zero, so no amount of ideal sizing lets a *wrong* answer outscore
  a *right* one. This is structurally why DAST can compress without hurting
  accuracy: the reward can never trade correctness for brevity. The specific
  constants (0.5, 0.9, the 0.1 floor and −0.1 cap) are hand-tuned magic numbers,
  and the piecewise-linear shape is a design choice, not a derived one — which
  reinforces the earlier "why not learn the target?" critique.

### Reader's critique — why a first-order rule and not a learned budget? *(my idea)*

The TLB is a hand-written, first-order (linear-in-accuracy) rule, and it is worth
asking why the length target is not itself *learned*. There are two honest sides.

**Why simple may be enough here.** The TLB is never a hard cap at inference; it is
used only *offline*, to rank sampled responses into preference pairs, and SimPO
consumes only the *ordering* within a pair, not the budget's absolute value. So
the budget mainly needs to be monotonic in difficulty rather than precise. And
*learning* a length predictor faces a circular-supervision problem: there is no
ground-truth "ideal length" to regress onto — the only signals available are
accuracy and observed lengths, which is exactly what this rule already consumes.

**Where the rule is genuinely shaky.**

- The hard-side anchor is $L_{max} = 4096$ used while sampling for TLB, but
  inference is allowed 32768 tokens (§4.1) — an 8x mismatch, so hard-problem
  budgets look systematically underestimated.
- A linear function of accuracy pours the *largest* budget into $p = 0$ problems,
  which may be the ones that are simply unsolvable for this model; spending the
  most tokens on the least learnable problems is arguably a misallocation.
- The $L_r$ term is a high-variance, single-sample estimate exactly when $p$ is
  small, which is where the budget most needs to be trustworthy.
- Linearity in $p$ is assumed, not derived; there is no argument that ideal length
  is linear in accuracy.

**The authors half-concede the point.** Their Limitations section flags the
off-policy, pre-constructed-data nature as a ceiling relative to online RL and
plans an on-policy variant built on this same reward — that is, learning the
length signal online, which is precisely the direction this critique points to.

## Points deferred for joint verification

- **[RESOLVED in §3.2] Is the budget a ceiling or a floor?** *Ceiling.* The
  reward curve rewards correct answers for staying *below* the budget and rewards
  incorrect answers for *approaching* it (saturating at the budget); in neither
  branch is *exceeding* it rewarded. Hard problems reason long only because their
  budget is itself large. The earlier "exceeding is encouraged" reading is wrong.
- **[still open — §4.1] Is TLB computed at inference or offline?** One reading is
  that a length predictor estimates a target length for each new problem at
  inference time. The competing reading is that TLB is computed offline by
  sampling on the training set, with the difficulty-adaptive behavior trained into
  the weights via SimPO (nothing budget-related fed at test time). §3.1 already
  shows TLB is a *sampling-based rule*, not a learned predictor; confirm the
  training-set / inference-time details in §4.1.

## Open questions the body must settle

These are the questions the abstract raises; we will answer them as we read on.

- **§3.1 — TLB.** How is the Token Length Budget actually computed, and *why*
  can one number serve both as a difficulty measure and as a target length?
- **§3.2 — reward shaping.** The abstract promises it *incentivizes* more
  reasoning on hard problems, not only penalizes length. How is that incentive
  realized in the reward, concretely?
- **§3.3–3.4 — budget preference optimization.** What is the preference-learning
  setup — what pairs are built, and which algorithm optimizes them?
- **§4 — evidence.** Is the >30% reduction with preserved accuracy real across
  model scales, and does the method *actually behave adaptively* (i.e. keep hard
  problems long rather than shortening everything)?

<!-- To be continued: §3.1 and §3.2 done (budget confirmed to be a ceiling/target). Read §3.3–3.4 next (preference data: DCP/DICP pairs + SimPO objective), then §4 (experiments). -->

