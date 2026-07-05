# DAST: Difficulty-Adaptive Slow-Thinking for Large Reasoning Models

**Authors:** Yi Shen, Jian Zhang, Jieyun Huang, Shuming Shi, Wenjing Zhang, Jiangze Yan, Ning Wang, Kai Wang, Zhaoxiang Liu, Shiguo Lian

**arXiv:** https://arxiv.org/abs/2503.04472 (v3)

**PDF:** https://arxiv.org/pdf/2503.04472

**Venue:** EMNLP 2025 Industry Track

**Categories:** cs.LG (primary), cs.AI

**Published:** 2025-03-06 · **Updated:** 2026-01-12

---

<!-- Reading progress: full paper read with the user — abstract, §1, method §3.1–3.4, experiments §4 including §4.2.2–4.2.4, and Limitations. Verified against the PDF. Statements are the paper's unless marked (inference) / (my idea). -->

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

### §3.3 — Building the preference pairs (DCP / DICP)

Each question's $N$ scored responses are ranked into contrastive triples — a
prompt $x$, a winner $y_w$, a loser $y_l$ — always *within the same correctness
class*:

- **DCP (Dual-Correct Pair):** both answers are correct; the winner is the *more
  concise* one ( $|y_w| \ll |y_l|$ ). Lesson: *when right, be as short as the
  budget allows.*
- **DICP (Dual-Incorrect Pair):** both answers are wrong; the winner is the
  *longer* one ( $|y_w| \gg |y_l|$ ). Lesson: *when stuck, reason more, toward the
  budget.*

A third class, CICP (correct-vs-incorrect), is deliberately *not* used — the
paper reports it brings no gain (footnote in §3.3, revisited in §4.2.3). Pairing
only within a class means the reward's sign gap never has to arbitrate correct
against incorrect; length is compared only among equals.

### §3.3, the filter — what the truncation threshold δ is for

After taking, per question, the DCP and DICP with the largest reward margin
$\Delta R = R(y_w) - R(y_l)$, a two-stage filter runs. First, a **global δ
truncation** drops the bottom $\delta$ fraction of all candidate pairs by margin
(the least-discriminative ones). Second, a **per-question cap** keeps at most two
pairs per question, one DCP and one DICP, for balance and efficiency.

The motivation is signal quality and, above all, anti-hacking:

- A **small-margin pair is a near-tie**: the reward barely prefers $y_w$ over
  $y_l$, so the label is mostly noise. Keeping only large-margin pairs buys
  statistical significance and stable optimization.
- The dangerous small-margin pairs are **low-discriminability DICPs**: two wrong
  answers whose rewards both sit at the $-0.1$ saturation, yet whose *lengths*
  differ a lot. Labeling the much-longer one as the winner and feeding it to
  SimPO — which is length-sensitive — teaches the model to *inflate length with no
  correctness gain*: textbook length reward-hacking. The paper shows it directly —
  at $\delta = 0$ the compression ratio goes *negative* (responses grow longer
  than the original model) because these excessive-length DICPs take over (§4.2.4,
  Figure 6). δ truncation cuts exactly these.

*Aside — a genuine inconsistency in the paper.* §4.1 lists the threshold as "0.15
and 0.18 for DS-7B and DS-32B," but §4.2.4 states the optimum is $\delta = 0.15$
for **DS-32B** and 0.18 for **DS-7B** — the two models' values are swapped between
the sections. The substance is unaffected: $\delta$ is tuned per model, roughly
0.15 to 0.18.

### §3.4 — SimPO training

The filtered pairs are optimized with SimPO, chosen because it is more sensitive
to response length than DPO:

$$
\mathcal{L}_{SimPO}(\pi_\theta) = -\mathbb{E}_{(x,y_w,y_l)\sim D}\left[\log\sigma\left(\frac{\beta}{|y_w|}\log\pi_\theta(y_w \mid x) - \frac{\beta}{|y_l|}\log\pi_\theta(y_l \mid x) - \gamma\right)\right]
$$

The two $1/|y|$ factors are what make the objective length-aware: each response's
log-probability is normalized by its own length, so the preference acts on
per-token quality rather than raw sequence probability. That is also *why* a
polluted DICP set hacks so easily — the objective is built to move length.

### Why not reward *incorrect* answers for exceeding the budget? *(discussion)*

A natural objection: if a response is still wrong, maybe it needs *even more*
reasoning, so why cap the incentive at the budget instead of rewarding length
*beyond* it? Reading the design, the saturation is deliberate, for four reasons.

- **For hard problems the budget is already near $L_{max}$.** Low accuracy sends
  $L_{budget} \to L_{max}$, and even at moderate accuracy the $L_{max}$ term keeps
  the budget large, so "approach the budget" already means "use almost the whole
  generation window." The extra reasoning you want for hard problems is delivered
  by a *large budget*, not by exceeding it — there is little "beyond budget" left
  to give.
- **An uncapped length reward is a hacking magnet.** Rewarding "longer when wrong"
  without a ceiling teaches the model to ramble indefinitely whenever it is
  unsure, farming reward. The paper observes exactly this: at truncation threshold
  $\delta = 0$, over-long incorrect pairs cause "reward hacking" that reverses
  length optimization (§4.2.4). The saturation is the guardrail.
- **It would undo the point of DAST.** The budget is *defined* as the reasoning a
  problem's difficulty warrants; anything past it is overthinking by construction.
  Rewarding wrong answers for exceeding it reintroduces the unbounded growth the
  method exists to remove.
- **The wrong branch is a smaller penalty, not a reward.** Even at the budget an
  incorrect answer scores $-0.1$; it never goes positive. The lever that actually
  pays is *getting it right* (which flips to the correct branch). "Grow toward the
  budget" only says *don't give up too early*, not *write longer wrong answers*.

Where the objection does bite *(my idea)*: if the budget is *under*-estimated — a
noisy, small $L_r$, or the $L_{max}=4096$ sampling cap versus 32768 at inference —
the saturation can cut off reasoning a harder-than-estimated problem truly needs.
A possible fix is a mild positive gradient a little *beyond* the budget, capped
higher up, trading a bit of extra hacking risk for headroom on mis-estimated
problems.

**The sharpest case — a problem the model gets 100% wrong** *(my idea)*. Here
$p = 0$, so the budget equals $L_{max}$ (the 4096 sampling cap), and it is tempting
to say "give it *more* budget so it might finally solve it." Two things are true
at once.

- **The cap is a genuine limitation.** The budget is a convex combination of $L_r$
  and $L_{max}$, with $L_r \le L_{max}$, so it can *never* exceed $L_{max}$; and
  $L_{max}=4096$ is one-eighth of the 32768-token inference window — a hard
  underestimate for any problem that truly needs longer reasoning.
- **Yet raising the budget alone would not help, inside DAST's offline setup.** A
  $p=0$ problem has *no correct sample*, so the only pairs it yields are DICP
  (prefer the longer *wrong* answer). A larger budget just teaches the model to
  prefer even longer *wrong* answers — reward hacking, not solving. You cannot
  re-rank your way to a correct long trajectory you never sampled; offline
  preference learning can only pick among existing samples.

The genuine fix is *on-policy* exploration with a larger window — sample at 32768
and reinforce a long attempt on the rare occasion it succeeds — which is exactly
the online-RL direction the paper defers to future work. DAST deliberately trades
that exploration away for cheap, stable, offline training. A cheaper patch is to
raise the TLB sampling window toward the inference window so hard-problem budgets
stop being systematically capped.

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

## Experiments — main results (§4.1–4.2.1)

Two backbones (DeepSeek-R1-Distill-Qwen **7B** and **32B**), three benchmarks,
greedy decoding, a 32768-token inference window. The headline reading is that
**compression tracks difficulty** while accuracy is preserved or improved.

The difficulty ordering matters and is easy to get wrong. By these models' own
baseline accuracy — the cleanest difficulty proxy — the ranking is **GPQA
hardest, AIME in the middle, MATH-500 easiest**: on GPQA / AIME / MATH, DS-7B
scores 47.98 / 60.0 / 93.2 and DS-32B scores 65.15 / 73.3 / 94.4. Two caveats keep
this honest. GPQA is 4-choice (a 25% random floor), so its raw accuracy flatters
it — though even chance-corrected it stays hardest for both models — and GPQA is
the only *out-of-domain* set (DAST is trained on math), which confounds its
numbers. AIME, by contrast, is open-ended elite competition math (only 30
problems), brutal in an absolute sense. Compression broadly tracks this ordering —
most on MATH, least on the hard sets:

| Benchmark (difficulty) | DS-7B CR | DS-7B ACC (Origin → DAST) | DS-32B CR | DS-32B ACC (Origin → DAST) |
|---|---|---|---|---|
| MATH-500 (easiest) | 18.1% | 93.2 → 93.6 | 46.0% | 94.4 → 95.8 |
| AIME 2024 (middle) | −1.9% | 60.0 → 70.0 | 35.9% | 73.3 → 76.7 |
| GPQA (hardest by acc, OOD) | 4.2% | 47.98 → 51.51 | 13.7% | 65.15 → 65.15 |

Takeaways:

- **AIME is the star evidence for adaptivity, not a "simple" benchmark.** On the
  hardest math set, DS-7B DAST *does not compress at all* (CR −1.9%, i.e. slightly
  longer) yet accuracy jumps from 60.0 to 70.0. This is the cleanest
  demonstration that DAST "does not indiscriminately shorten … but adaptively
  allocates more reasoning for complex problems" (the paper spells it out).
  Reading AIME as "easy, large compression" inverts the actual story.
- **Accuracy is best (or tied-best) in all six cells, but DAST is *not* the
  strongest compressor.** The aggressive uniform methods compress far more and
  collapse accuracy on hard problems — e.g. DS-32B on AIME, SimPO-Shortest cuts
  76.4% of tokens but accuracy craters from 73.3 to 36.7, whereas DAST cuts 35.9%
  and *improves* to 76.7. DAST wins the accuracy–compression trade-off (the Pareto
  frontier), not the raw compression race. That is the "balance" the method is
  really selling.
- **Caveat on the ">30% average" headline.** That number is essentially the
  DS-32B story (its three-benchmark mean CR is about 32%); DS-7B averages only
  about 7%. The gap is itself consistent with the thesis — a weaker 7B model finds
  more of these problems genuinely hard, so it earns less compression.
- **The difficulty ranking exposes an out-of-domain wrinkle.** If compression
  tracked difficulty perfectly, the *hardest* set (GPQA) should be compressed
  *least*. That holds for DS-32B (least to most: GPQA 13.7%, AIME 35.9%, MATH
  46.0%) but *not* for DS-7B, which compresses the harder, out-of-domain GPQA
  *more* than in-domain AIME (4.2% versus −1.9%). In-domain AIME is treated as the
  "hardest, least compressible" set while OOD GPQA's difficulty is
  under-recognized — more support for the policy-doesn't-fully-transfer reading.

This resolves open question #4: the adaptive behavior is real (compression scales
with difficulty) and accuracy is preserved or improved — with the honest caveat
that the aggregate ">30%" is carried by the larger model.

### Finer analyses (§4.2.2–4.2.4)

These substantiate the headline claims and are mostly confirmatory:

- **§4.2.2, per-difficulty (MATH-500, DS-32B).** Compression shrinks
  monotonically as difficulty rises — about 58.5% at Level 1 down to 40.8% at
  Level 5 — while DAST keeps the best Level-5 accuracy among the compared methods.
  This is the *within-benchmark* proof of adaptivity, holding domain fixed (unlike
  the cross-benchmark view, which the GPQA discussion below shows is confounded).
- **§4.2.3, DCP/DICP ablation (DS-7B).** The two pair types are complementary and
  specialize: dropping DICP over-compresses (best CR 59.8% but −3.2% accuracy),
  dropping DCP over-inflates (+17.8% length), and only both together hit the sweet
  spot. Adding CICP (correct-vs-incorrect pairs) gives no gain — hence it is
  excluded.
- **§4.2.4, δ sensitivity.** At δ = 0 the compression ratio goes negative (reward
  hacking, as discussed under §3.3); there is a per-model optimum around
  0.15–0.18.

### GPQA — the out-of-domain case *(discussion)*

GPQA deserves separate treatment because it is the *only* out-of-domain
benchmark: DAST's preference pairs come entirely from MATH, so GPQA tests whether
the difficulty-adaptive behavior *transfers* to a domain never budget-trained. It
is also 198 PhD-level *multiple-choice* science questions (physics, chemistry,
biology; roughly a 25% random baseline), a different answer format from the
open-ended MATH/AIME.

- DS-7B: accuracy rises from 47.98 to 51.51 (+3.53%) at CR 4.2% — the paper reads
  this as domain generalization.
- DS-32B: accuracy is *exactly* unchanged (65.15 to 65.15) at CR 13.7% — here the
  gain is free compression, not accuracy.

*Open question (my idea):* a small GPQA compression is consistent with **two**
explanations this table cannot separate — (1) genuine adaptivity ("hard and
out-of-domain, so stay cautious"), or (2) the length policy simply *not
transferring* out-of-domain, leaving behavior close to the original model. The
exactly-unchanged DS-32B accuracy and near-original behavior lean toward the
milder reading: DAST does not *hurt* out-of-domain and even helps the 7B, but
GPQA is weaker evidence for domain-general adaptivity than the in-domain math
results. The multiple-choice format weakens it further, since the optimal
reasoning-length profile there differs from open-ended math.

## Points deferred for joint verification

- **[RESOLVED in §3.2] Is the budget a ceiling or a floor?** *Ceiling.* The
  reward curve rewards correct answers for staying *below* the budget and rewards
  incorrect answers for *approaching* it (saturating at the budget); in neither
  branch is *exceeding* it rewarded. Hard problems reason long only because their
  budget is itself large. The earlier "exceeding is encouraged" reading is wrong.
- **[RESOLVED — §4.1] Is TLB computed at inference or offline?** *Offline.* §4.1
  confirms the TLB is computed by sampling 20 responses per *training* question
  (max length 4096) and measuring accuracy and correct-length; nothing
  budget-related is fed at inference. The difficulty-adaptive behavior is baked
  into the weights by offline SimPO — DAST is fully off-policy, which the
  Limitations section flags as its main ceiling.

## Reader's follow-up ideas — toward an on-policy successor *(my ideas)*

The natural next step, and the one the paper's own Limitations point to, is to
make the length signal *on-policy and learned* instead of an offline hard rule.
A few threads, aligned to existing work so as not to reinvent it.

### Don't reinvent — two mechanisms already exist

- **Decoding intervention to keep reasoning going** is essentially **s1's "budget
  forcing"** (Muennighoff et al. 2025, cited by DAST): suppress the
  end-of-thinking delimiter and append "Wait" to extend the chain, or force the
  delimiter to cut it. It is a *test-time* length knob — usable as the actuator
  for length-varied rollouts, but heuristic, with diminishing returns.
- **Rolling out at prescribed target lengths** is close to **L1 / LCPO**
  (Aggarwal & Welleck 2025, cited by DAST), which trains a model by RL to obey a
  target length given in the prompt. **Han et al. 2024** instead searches the
  budget in the prompt iteratively — the very cost DAST advertises avoiding.

### The strongest version — an online, group-relative "live TLB"

Move DAST's TLB online and recompute it inside each rollout group (GRPO-style):

1. Sample a group of G rollouts per prompt.
2. From the group's *current* accuracy and correct-lengths, compute a live budget
   — an online TLB that adapts as the policy improves, with no fixed 4096 cap.
3. Advantage = correctness (kept strictly dominant) plus length shaping toward the
   live budget (shorter-if-correct, longer-if-wrong up to a cap), normalized
   group-relative.
4. Optionally inject length-diverse samples (via budget forcing) to trace a
   per-prompt length-vs-accuracy curve.

Why this beats offline DAST: the target tracks the policy; there is no
sampling-window cap; and crucially it **dissolves the $p = 0$ dead-end we found
earlier** — on-policy exploration can *discover* a correct long trajectory for a
never-solved problem and reinforce it, which an offline re-ranking method never
can.

### Simplest concrete port — DAST's reward inside GRPO *(my idea)*

The most natural on-policy version is *simpler* than DAST, not merely equivalent.
GRPO already samples a group of G responses per prompt from the *current* policy,
and its group-relative advantage $A_i = (r_i - \text{mean}(r)) / \text{std}(r)$
manufactures the DCP/DICP contrast **for free**:

- an all-correct group gives the shorter answers a positive advantage (the DCP
  signal: when right, be short);
- an all-wrong group gives the longer answers a positive advantage (the DICP
  signal: when stuck, reason more).

So the explicit pair construction *and* the δ filter can be **dropped entirely** —
group normalization does that job, and low-variance groups self-downweight. All
that ports over is DAST's reward-calibration formula, used as the GRPO reward.

**A self-regulating property.** Because a correct-short answer scores above a
correct-long one, yet shortening too far flips the answer to *wrong* (a big
negative), the policy settles near the *minimal length that stays correct* — which
is exactly the objective we wanted. The reward is its own length controller
(modulo retuning the constants 0.5 / 0.9 / 0.1 for RL).

**Stage it:**

- **v1 (safest, isolates the on-policy effect).** Compute the TLB *once* from a
  frozen reference model (DAST's TLB, but sampled at the full 32768 so the 4096
  cap disappears), then run GRPO with DAST's reward against that fixed budget, KL
  to the reference. A clean apples-to-apples test of "same reward, offline SimPO
  vs online GRPO."
- **v2 (fuller).** Make the budget a *live* TLB — an EMA over recent groups — so it
  adapts as the policy improves. More powerful, but watch the moving-target
  feedback loop (policy shortens, $L_r$ drops, budget drops, …); the EMA and the
  KL anchor damp it.

**The money experiment.** Does on-policy exploration recover accuracy on the
hardest / previously-unsolved $p = 0$ problems that offline DAST structurally
cannot? Report accuracy on the hardest bucket specifically — that is the result
that would justify the successor.

**Costs and guards.** On-policy GRPO over 32768-token rollouts erases DAST's
cheapness (its main selling point), and length rewards hack aggressively
on-policy — keep the correctness sign-gap, KL, and an entropy bonus.

### Two things that must be pinned down

- **Define "optimal length" as an explicit objective.** "Dynamically decide the
  optimal length" is under-specified until scalarized: either *minimal length
  subject to preserving accuracy* (constrained), or a Lagrangian
  *accuracy-per-token* exchange rate. DAST silently takes "the length correct
  answers happen to run" as optimal — a heuristic worth replacing.
- **Guard against length reward-hacking, which is worse on-policy.** Keep DAST's
  *correctness-dominates-length* sign gap as an invariant, add KL / entropy
  control, and beware the **forced-length confound**: a truncated 500-token
  rollout may fail because it was cut, not because 500 was too short — so training
  a model to *natively* produce a target length (L1-style) is cleaner than hard
  truncation for measuring the length-accuracy curve.

### The white space

None of DAST (offline hard rule), L1 (needs a target length supplied), or s1
(test-time heuristic) *learns, on-policy, the per-prompt optimal length as a
function of difficulty, with the target recomputed as the policy improves*. That
gap — an "online difficulty-adaptive RL" with a self-derived budget — is a clean,
novel direction.

## Net read

DAST is a well-framed, honest engineering contribution: one clean idea — a Token
Length Budget that doubles as difficulty measure and target length — turned into
a cheap, stable, offline SimPO recipe that compresses reasoning *adaptively*
rather than uniformly, preserving or improving accuracy across model scales. It
stands or falls on the TLB being a good proxy for "how much reasoning a problem
deserves," and the in-domain evidence (compression tracking difficulty, AIME kept
long while accuracy rises) is convincing. Its ceiling is exactly its cheapness: an
offline, hard-ruled, sampling-capped budget that cannot explore, transfers only
softly out-of-domain, and leans on a hand-tuned δ. The obvious sequel is
on-policy.

<!-- Reading complete: motivation, full method §3.1–3.4, experiments §4 (including the finer analyses), reader critiques, on-policy follow-up ideas, and a net read are all recorded. -->



---

## Application project — Difficulty-Adaptive Reasoning for LLM-based Recommendation *(spun off from this reading)*

*Working title / name options: **AdaReason-Rec**, **Rec-DAST**, "Think as Hard as
the Query Deserves."*

**Status:** v0 proposal (draft for iteration). Ported from the reading of DAST
(Shen et al., EMNLP 2025 Industry; arXiv 2503.04472) — see
`paper_reading_notes/DAST - Difficulty-Adaptive Slow-Thinking for Large Reasoning Models.md`.

> ⚠️ Citations below are from memory and **must be verified** in a dedicated
> related-work pass before submission (titles, authors, venues).

---

### 1. Thesis and motivation

Reasoning-augmented LLM recommenders (models that emit a natural-language
`<think>` trace before recommending) plausibly **overthink**: they spend long
reasoning on easy queries (an active user with an obvious next item) and need
extended reasoning only on hard ones (cold-start, intent shift, long-tail).

Why this matters *more* in recommendation than in math:

- **Latency and cost are first-class.** Recommendation serves enormous request
  volumes under tight latency budgets; reasoning tokens are pure serving cost.
  Overthinking is far more expensive here than in offline math evaluation.
- **Difficulty is heavily long-tailed.** Most queries are easy; a minority are
  hard. So the headroom for adaptive savings is large.

**Claim.** Spend reasoning tokens *in proportion to query difficulty*: keep the
accuracy gains of reasoning at a fraction of the tokens, and do it **on-policy**
so the model can *explore* longer reasoning for the hard queries an offline method
can never solve.

---

### 2. What we port from DAST (and what we drop)

DAST's core is a **Token Length Budget (TLB)** that is simultaneously a difficulty
score and a target length, used to shape a reward and build offline preference
pairs for SimPO.

Key insight from the reading: moving this **on-policy with GRPO** makes it
*simpler*, not just better. GRPO's group-relative advantage **auto-generates**
DAST's DCP/DICP contrast (all-correct group → shorter wins; all-wrong group →
longer wins), so we **drop the explicit pair construction and the δ filter
entirely** and port only the reward-calibration formula.

---

### 3. Method

#### 3.1 Backbone — a reason-then-rerank recommender

Chosen backbone: an LLM recommender that emits a **natural-language reasoning
trace** (largest overthinking headroom), instantiated as **reason-then-rerank**
for a clean, matchable reward:

1. A cheap first-stage retriever returns top-$M$ candidate items for the user.
2. The LLM sees the user history and the $M$ candidates, emits a `<think>` trace,
   then outputs a **reranked top-$K$** list (or picks the next item).
3. Correctness is measured on the held-out next item (leave-one-out).

Rationale: reranking over a candidate set avoids fuzzy open-vocabulary
title-to-catalog matching (a major noise source) and mirrors real retrieve→rerank
pipelines. *(More ambitious alternative: generate a Semantic ID directly — more
"generative recommendation," but harder to match; defer to a later version.)*

#### 3.2 Step 0 — obtain a base reasoning recommender (SFT warm-start)

No off-the-shelf reasoning recommender exists, so we must build one before
adapting it. Default: **distill** reasoning-plus-recommendation demonstrations
from a strong teacher LLM over (history, candidates), SFT them into the target
model, then apply the adaptive-length training below.

**Positioning note.** The paper's novelty is **difficulty-adaptive length
efficiency**, *not* "reasoning helps recommendation." Keep the base recommender as
simple and as borrowed-from-prior-work as possible; concentrate the contribution
on adaptive length.

#### 3.3 Recommendation TLB (Rec-TLB)

Sample $N$ reasoning traces for a query from a reference policy; let $c$ be the
number whose reranked list contains the held-out item in the top-$K$, and $L_r$
the mean reasoning length of those hitting traces:

$$L_{budget} = p \cdot L_r + (1 - p) \cdot L_{max}, \qquad p = \frac{c}{N}$$

Easy query (active user, obvious item): $p$ high, budget small. Hard query
(cold-start, tail): $p \to 0$, budget approaches $L_{max}$. Unlike DAST, sample at
the **full inference length** so there is no artificial cap.

#### 3.4 Reward — recommendation correctness shaped by length

With relative length deviation $\lambda_i = (L_i - L_{budget}) / L_{budget}$:

$$
r_i =
\begin{cases}
\max(-0.5\lambda_i + 0.5,\, 0.1), & \text{hit@}K \\
\min(0.9\lambda_i - 0.1,\, -0.1), & \text{miss}
\end{cases}
$$

We keep DAST's **sign gap** (a hit always scores above a miss), so the reward can
never trade recommendation quality for brevity. Two variants of "hit":

- **Binary** (faithful port): hit@$K$ on the held-out item.
- **Graded** (denser, less sparse gradient): use NDCG@$K$ as the base term before
  length shaping — likely needed to tame GRPO variance from sparse implicit
  feedback.

```python
def dast_rec_reward(trace, L_budget, L_max, K):
    hit = held_out_item_in_topK(trace.reranked_list, K)   # or graded NDCG@K
    lam = (len(trace.reasoning_tokens) - L_budget) / L_budget
    if hit:
        return max(-0.5 * lam + 0.5, 0.1)   # correct: reward shorter-than-budget, decay if longer
    else:
        return min(0.9 * lam - 0.1, -0.1)   # miss: penalty shrinks toward budget, saturates at it
```

#### 3.5 On-policy training with GRPO

```python
# Rec-TLB from a reference policy (v1: precomputed & fixed; v2: EMA over recent groups)
def rec_tlb(prompt, ref_policy, N, K, L_max):
    traces = [sample(ref_policy, prompt) for _ in range(N)]
    hits   = [held_out_item_in_topK(t.reranked_list, K) for t in traces]
    p = sum(hits) / N
    correct_lens = [len(t.reasoning_tokens) for t, h in zip(traces, hits) if h]
    L_r = mean(correct_lens) if correct_lens else L_max
    return p * L_r + (1 - p) * L_max

for step in training:
    prompt = sample_query()
    group  = [sample(policy, prompt) for _ in range(G)]                  # on-policy rollouts
    rew    = [dast_rec_reward(t, L_budget[prompt], L_max, K) for t in group]
    adv    = (rew - mean(rew)) / (std(rew) + eps)                        # group-relative advantage
    loss   = grpo_clip_objective(policy, group, adv) + beta_kl * KL(policy, ref)
    update(policy, loss)
```

Group-relative advantage:

$$A_i = \frac{r_i - \text{mean}(r)}{\text{std}(r) + \epsilon}$$

- **v1 (safest, isolates the on-policy effect).** Fixed Rec-TLB from the frozen
  reference; a clean "same reward, offline SimPO vs online GRPO" comparison.
- **v2 (fuller).** Live Rec-TLB via EMA over recent groups, so the budget adapts
  as the policy improves; watch the moving-target feedback loop, where the policy
  shortens, so $L_r$ drops, so the budget drops with it. An EMA and the KL anchor
  damp it.
- **Guards.** Keep the sign gap, KL to reference, and an entropy bonus — length
  rewards hack aggressively on-policy.

---

### 4. Experiments

#### 4.1 Data and metrics

- **Amazon Reviews 2023** (existing `amazon_2023/` pipeline): several categories
  spanning different sparsity → natural difficulty variation. Sequential splits
  (maxlen 20 / 50), leave-one-out. Optionally a second corpus for generality.
- **Quality:** Recall@$K$, NDCG@$K$. **Efficiency:** avg reasoning tokens,
  compression ratio vs full-reasoning, wall-clock latency.

#### 4.2 Baselines

| Baseline | Reasoning | Length control | Role (DAST analog) |
|---|---|---|---|
| No-reasoning rerank | none | — | fast/cheap (DeepSeek-V3) |
| Full-reasoning | always long | none | overthinking (R1) |
| Uniform-short | short | length-penalty GRPO | one-size-fits-all (SimPO-shortest) |
| DAST-offline (ported) | adaptive | offline SimPO on DCP/DICP | the paper we build on |
| L1-rec | targeted | fixed target length in prompt | length-controlled RL |
| **Ours v1 / v2** | **adaptive** | **GRPO + Rec-TLB reward** | on-policy successor |

#### 4.3 Ablation matrix

- reward: binary hit vs graded NDCG; with/without the sign gap.
- budget: fixed (v1) vs live EMA (v2); full-length vs capped sampling.
- pairing: confirm GRPO-group replaces DCP/DICP + δ (drop them, expect no loss).
- guards: KL / entropy on-off; group size $G$; candidate count $M$.

#### 4.4 Headline analyses

- **Adaptivity curves:** reasoning length vs difficulty, bucketed by history
  length (cold-start), item popularity (tail), and sampled $p$. Expect long
  reasoning on hard buckets, short on easy.
- **Difficulty-metric validity:** show sampled $p$ correlates with cold-start /
  tail / retriever margin (justify Rec-TLB as a real difficulty signal).
- **The money experiment — the cold-start / $p = 0$ queries.** Does on-policy
  exploration recover quality on the hardest / never-hit queries that offline DAST
  *structurally* cannot? Report metrics on the hardest bucket specifically — this
  is the result that justifies the successor.

---

### 5. Risks and mitigations

1. **Backbone must have substantial, variable reasoning** or there is no
   overthinking to cut. Mitigate via the SFT warm-start producing genuinely
   contentful traces; verify length actually varies with difficulty pre-training.
2. **Noisy recommendation correctness** (implicit feedback, several plausible
   items, exposure bias) → sparse/high-variance reward. Mitigate with graded
   NDCG reward, larger $K$, larger groups, KL control.
3. **Difficulty may not equal uncertainty.** Validate the $p$ metric against
   intuitive difficulty axes; consider complementary signals (retriever margin,
   distribution entropy).
4. **Compute.** On-policy GRPO over long rollouts erases DAST's cheapness; report
   training cost honestly and lean on v1 for controlled comparison.

---

### 6. Related work skeleton *(verify all citations)*

- **Efficient / adaptive reasoning:** DAST (Shen et al. 2025); budget forcing —
  s1 (Muennighoff et al. 2025); length-controlled RL — L1 / LCPO (Aggarwal &
  Welleck 2025); token-budget-aware (Han et al. 2024); length-penalty RL — Kimi
  k1.5 (Team et al. 2025); cosine length reward (Yeo et al. 2025); latent
  reasoning — Coconut (Hao et al. 2024).
- **Reasoning / generative recommendation:** "Reasoning over Semantic IDs …"
  (in `paper_reading_notes/`); Semantic-ID generative retrieval — TIGER (Rajput et
  al. 2023) and successors; LLM-as-recommender.
- **RL for recommendation:** RLHF-style reward optimization for rankers/LLM
  recommenders.
- **Gap (to defend):** no method makes reasoning *length* difficulty-adaptive for
  recommendation, nor learns it on-policy with a self-derived budget.

---

### 7. Open decisions / TODO

- [ ] Related-work scan to lock novelty and exact citations.
- [ ] Pick teacher LLM and SFT recipe for the base reasoning recommender.
- [ ] Decide binary-hit vs graded-NDCG reward for v1.
- [ ] Choose categories, $K$, $M$, $N$, $G$, $L_{max}$.
- [ ] Implement Rec-TLB + GRPO on top of the existing `amazon_2023` pipeline.
