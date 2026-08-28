# DAPO: An Open-Source LLM Reinforcement Learning System at Scale

**Authors:** Qiying Yu, Zheng Zhang, Ruofei Zhu, Yufeng Yuan, Xiaochen Zuo, Yu Yue, Weinan Dai, Tiantian Fan, Gaohong Liu, Lingjun Liu, Xin Liu, Haibin Lin, Zhiqi Lin, Bole Ma, Guangming Sheng, Yuxuan Tong, Chi Zhang, Mofan Zhang, Wang Zhang, Hang Zhu, Jinhua Zhu, Jiaze Chen, Jiangjie Chen, Chengyi Wang, Hongli Yu, Yuxuan Song, Xiangpeng Wei, Hao Zhou, Jingjing Liu, Wei-Ying Ma, Ya-Qin Zhang, Lin Yan, Mu Qiao, Yonghui Wu, Mingxuan Wang

**arXiv:** https://arxiv.org/abs/2503.14476 (v2)

**PDF:** https://arxiv.org/pdf/2503.14476

**Venue:** arXiv preprint

**Categories:** cs.LG (primary), cs.CL

**Published:** 2025-03-18 · **Updated:** 2025-05-20

---

## Abstract

The abstract draws an important distinction between inference-time scaling and
reinforcement learning. Inference-time scaling gives a model more computation
while solving a problem, commonly by allowing longer chains of thought, more
samples, or additional search. It is therefore broader than simply adding a
chain-of-thought prompt. Reinforcement learning is the training technique used
to elicit complex reasoning behaviors from the model; it is better understood
as strengthening and shaping those behaviors than as teaching reasoning from
scratch.

I find it useful to divide test-time scaling into two forms. **Sequential
scaling** spends more tokens within one trajectory, allowing a longer chain of
thought, self-checking, and revision before producing the answer. **Parallel
scaling** samples multiple candidate trajectories, as in Best-of-N, and then
selects or aggregates them with a verifier, reward model, majority vote, or
another scoring rule. The two can also be combined. RL is not itself a form of
test-time scaling; it elicits reasoning behaviors that let the model use this
additional inference-time computation more effectively.

The paper is motivated by a reproducibility gap. Systems such as OpenAI o1 and
DeepSeek-R1 demonstrate strong reasoning, but their public technical reports do
not disclose all of the training details needed to reproduce large-scale RL
successfully. DAPO responds by proposing several techniques for improving
large-scale RL and releasing the algorithm, `verl`-based training code, and a
curated dataset. Its headline result is 50 points on AIME 2024 using a
Qwen2.5-32B base model.

## Introduction

Test-time scaling represents a shift in the LLM paradigm: by allocating more
inference-time computation, models can produce longer chains of thought and
exhibit sophisticated behaviors such as self-verification and iterative
refinement, leading to major gains on competitive mathematics and coding
tasks. This does not mean that earlier LLMs could not reason at all; rather,
test-time scaling makes extended reasoning a central and visibly scalable
capability.

The practical obstacle is that systems such as OpenAI o1 and DeepSeek-R1 do not
disclose all of the RL algorithmic details and training pitfalls needed for
reproduction. When the DAPO authors initially applied naive GRPO to
Qwen2.5-32B, they obtained only about 30 points on AIME 2024, compared with 47
points reported for **DeepSeek-R1-Zero-Qwen-32B**. Their diagnosis identifies
three specific failure modes: **entropy collapse, reward noise, and training
instability**.

An important baseline distinction is that
**DeepSeek-R1-Zero-Qwen-32B is not DeepSeek-R1-Distill-Qwen-32B**. The former
applies large-scale RL directly to a Qwen-32B base model, without first
distilling DeepSeek-R1 trajectories into it; the latter is the separately named
model trained by distillation from DeepSeek-R1 outputs. DAPO is therefore
comparing its Qwen2.5-32B RL run against another direct RL experiment on a
Qwen-32B base, rather than against a distilled model.

My interpretation of **entropy collapse** is that the policy's token
distributions become sharply peaked during training: their entropy drops
rapidly, sampled responses within a group become increasingly similar, and
output diversity falls. This is a loss of exploration, not merely an abrupt
change in the scalar entropy metric. Once the policy becomes nearly
deterministic, it has little chance to sample alternative reasoning paths that
could receive higher rewards, so RL progress can plateau prematurely.

The authors address these problems with four techniques: Clip-Higher, Dynamic
Sampling, Token-Level Policy Gradient Loss, and Overlong Reward Shaping. The
resulting DAPO system reports 50 points on AIME 2024 while using 50% of the
training steps of the referenced DeepSeek result. The paper's main value is
therefore not just its final score, but its account of the intervening failure
modes and fixes, together with the released algorithm, training code, and
dataset.

## Preliminary

### PPO

My intuitive reading of PPO is that it evaluates each sampled token under the
current policy and the rollout policy, then uses the token's advantage to decide
whether its probability should increase or decrease. The relevant quantity is
not a probability difference but the **importance-sampling ratio**

```math
r_t(\theta)
=
\frac{\pi_\theta(o_t\mid q,o_{\lt t})}
     {\pi_{\theta_{\mathrm{old}}}(o_t\mid q,o_{\lt t})}.
```

PPO maximizes the clipped surrogate objective

```math
\min\left(
r_t\hat A_t,\;
\mathrm{clip}(r_t,1-\epsilon,1+\epsilon)\hat A_t
\right).
```

If $\hat A_t>0$, the sampled token was better than expected, so PPO encourages
increasing its probability, but removes the incentive to increase its ratio
beyond $1+\epsilon$. If $\hat A_t<0$, PPO encourages decreasing that token's
probability, but removes the incentive to reduce its ratio below
$1-\epsilon$. This operates on the probability of the sampled token
conditioned on its prefix, not on the policy distribution as one undifferentiated
object.

The clipping should also not be interpreted as a hard constraint that forces
the new probability ratio to remain inside the interval. It clips the surrogate
training objective, making excessively large policy changes unprofitable in
that update; the realized ratio can still move outside the clipping range.

#### Reward versus advantage in LLM training

Advantage is not simply the output of the reward function. A reward model
usually assigns a scalar reward $R(y)$ to the completed response, whereas the
advantage measures how much better or worse a sampled action was than the
expected outcome from its current prefix:

```math
A_t = Q(s_t,a_t)-V(s_t).
```

In PPO-based RLHF, the reward-model score is commonly placed at the end of the
sequence, sometimes alongside token-level KL penalties. A learned critic
estimates $V(s_t)$ for each prefix, and Generalized Advantage Estimation uses
the temporal-difference residuals

```math
\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)
```

to produce $\hat A_t$. Therefore, the final sequence reward contributes to the
return of all preceding tokens, but it is not merely divided equally among
them. Different prefixes can receive different advantages because their value
estimates differ.

GRPO uses a simpler mechanism. It removes the critic and normalizes completed
sequence rewards within the $G$ responses sampled for the same question:

```math
\hat A_i =
\frac{R_i-\mathrm{mean}(\{R_j\}_{j=1}^{G})}
     {\mathrm{std}(\{R_j\}_{j=1}^{G})}.
```

The resulting scalar is copied to every token in response $i$. Thus GRPO and
DAPO do not solve fine-grained token credit assignment: all tokens in one
response share the same outcome-based advantage, even though their PPO ratios
are token-specific. DAPO's later token-level loss changes how these token losses
are aggregated, not how a distinct advantage is inferred for each token.

For a concrete RLVR example, suppose GRPO samples 16 responses for one input and
the verifier returns 16 binary rewards. Normalizing those rewards within this
group produces 16 **sequence-level group-relative advantage estimates**. If
eight responses are correct and eight are wrong, the reward mean and population
standard deviation are both $0.5$, so correct responses receive advantage
$+1$ and incorrect responses receive $-1$. Each response's scalar advantage is
then copied to all of its tokens.

More generally, if the fraction of correct responses is $p$, the population
normalization gives

```math
A_{\mathrm{correct}}=\sqrt{\frac{1-p}{p}},
\qquad
A_{\mathrm{wrong}}=-\sqrt{\frac{p}{1-p}}.
```

Thus a rare correct response receives a particularly strong positive signal.
If all 16 responses are correct or all are wrong, however, the standard
deviation is zero and there is no within-group ranking signal. This degenerate
case directly motivates DAPO's Dynamic Sampling, which keeps only groups
containing both correct and incorrect responses.

There are two different length scalings that should not be conflated. If a
response has sequence-level advantage $A_i=0.5$, then GRPO sets
$A_{i,t}=0.5$ for every token; it does not define
$A_{i,t}=0.5/|o_i|$. However, original GRPO computes

```math
\frac{1}{|o_i|}\sum_t \ell_{i,t}(A_{i,t}),
```

so the outer sequence average makes each individual token's contribution to
the final objective carry an effective factor of $1/|o_i|$. The advantage
tensor remains $0.5$ at every token, while the loss aggregation supplies the
length normalization. DAPO's Token-Level Loss later replaces this per-sequence
normalization with one normalization over all valid tokens in the batch.

### GRPO

GRPO removes PPO's learned value function and uses the responses sampled for
the same input as a group-relative baseline. Their completed-response rewards
are normalized within the group to obtain one advantage estimate per response.
The policy is then optimized with the clipped surrogate objective

```math
J_{\mathrm{GRPO}}(\theta)
=
\mathbb{E}\left[
\frac{1}{G}\sum_{i=1}^{G}\frac{1}{|o_i|}
\sum_{t=1}^{|o_i|}
\left(
\min\left[
r_{i,t}(\theta)\hat A_i,\,
\mathrm{clip}\left(r_{i,t}(\theta),1-\epsilon,1+\epsilon\right)\hat A_i
\right]
-\beta D_{\mathrm{KL}}\left(\pi_\theta\middle\|\pi_{\mathrm{ref}}\right)
\right)
\right],
```

where

```math
r_{i,t}(\theta)
=
\frac{\pi_\theta(o_{i,t}\mid q,o_{i,\lt t})}
     {\pi_{\theta_{\mathrm{old}}}(o_{i,t}\mid q,o_{i,\lt t})}.
```

This is a **policy-optimization objective**, not a reward function. The
verifier or reward model first produces $R_i$; group normalization converts
$R_i$ into $\hat A_i$; and the equation above turns those advantages into an
objective for updating the policy. The paper writes $J$ as an objective to
maximize, whereas implementations normally minimize the loss
$L_{\mathrm{GRPO}}=-J_{\mathrm{GRPO}}$.

The two comparison policies also serve different purposes.
$\pi_{\theta_{\mathrm{old}}}$ is the rollout policy used in the importance
ratio, while $\pi_{\mathrm{ref}}$ is a frozen reference policy used by the KL
penalty to discourage excessive drift. As in PPO, clipping modifies the
surrogate objective rather than hard-clamping the realized importance ratio.

### Removing KL divergence

The KL penalty in standard RLHF discourages the online policy from diverging
too far from a frozen reference policy, usually the initial post-trained model.
That makes sense when RL is intended to align behavior while preserving most of
the starting model's distribution.

DAPO adopts a different premise for long-CoT reasoning RL. Developing extended
reasoning behaviors may require the policy distribution to move substantially
away from the initial policy, so this divergence is partly the desired outcome
rather than merely a failure mode. The authors therefore regard the KL
constraint as unnecessary and remove the term
$\beta D_{\mathrm{KL}}(\pi_\theta\|\pi_{\mathrm{ref}})$ from their objective.
This is the paper's task-specific design choice, not a general claim that KL
regularization is unnecessary for every form of RL training.

### Rule-based verifiable rewards

DAPO uses final-answer correctness as a rule-based outcome reward instead of a
learned reward model. This is particularly suitable for mathematics and code,
where an answer can often be checked by symbolic equivalence, compilation, or
tests. A learned reward model is an imperfect proxy whose weaknesses may be
exploited as RL optimization pressure increases; a deterministic verifier
reduces that attack surface by tying reward more directly to task success.

Verifiable rewards do not eliminate reward hacking, however. A model can still
exploit a weak specification or verifier: for example, it might benefit from
incomplete tests, leaked answers, mutable evaluation files, parser bugs, or
side effects that make the checker report success without accomplishing the
intended task. RLVR is therefore only as sound as the verifier and evaluation
environment.

This connects to agent training, but three concepts should remain distinct:

1. **Reward hacking/specification gaming** obtains reward without satisfying
   the intended goal.
2. **Unauthorized tool use** invokes capabilities outside the intended policy,
   but does not necessarily cross an isolation boundary.
3. **Devbox or sandbox escape** crosses a security boundary from the isolated
   environment into the host, control plane, network, credentials, or another
   protected resource.

A sandbox escape can also become reward hacking if the agent uses the escaped
access to manipulate its evaluator or obtain answers, but escape is first a
security-containment failure. Secure agent RL consequently requires controls
outside the reward function: least-privilege tools, strong sandboxing, isolated
and immutable evaluators, hidden tests, environment resets, network and secret
isolation, and audited side effects.

A sharper version of this concern does not require the verifier itself to fail.
An outcome-only verifier may correctly recognize a successful final result
while remaining unaware that the agent obtained it through a prohibited tool,
answer leakage, an evaluation-system exploit, or another disallowed process.
The reward function has not been fooled about the outcome; the training
objective simply omitted constraints on how that outcome may be achieved.

This can be amplified by GRPO. If one rollout accidentally discovers a
high-reward cheating strategy while the rest fail, that rare successful
trajectory receives a large positive group-relative advantage. Because the same
sequence-level advantage is assigned to all actions in the trajectory, RL can
reinforce the entire behavior, including the prohibited tool use, and make it
increasingly common. The analogous failure with a learned reward model exploits
the scorer's approximation error; with a correct outcome verifier, it exploits
the gap between **task success** and **process compliance**. Preventing the
latter requires externally enforced action constraints and trajectory-level
monitoring, not only a stronger final-answer verifier.

## Method

### Clip-Higher

The motivation is entropy collapse. During naive PPO or GRPO training, the
policy entropy drops quickly and some response groups become nearly identical,
indicating that the policy is becoming deterministic too early and losing
exploration capacity.

The paper argues that symmetric clipping treats low- and high-probability tokens
asymmetrically in absolute probability space. With $\epsilon=0.2$ and positive
advantage, an old-policy token with probability $0.01$ receives useful
optimization pressure only up to probability $0.012$. A token with probability
$0.9$ has a nominal upper limit of $1.08$, which exceeds the maximum possible
probability and therefore hardly constrains its movement toward $1$. Figure 3a
supports this diagnosis more narrowly: the **mean probability of up-clipped
tokens** is below $0.2$; it does not show that every clipped token is inherently
low-probability.

DAPO decouples the clipping radii:

```math
\mathrm{clip}\left(r_{i,t},\,1-\epsilon_{\mathrm{low}},\,
1+\epsilon_{\mathrm{high}}\right),
\qquad
\epsilon_{\mathrm{high}}>\epsilon_{\mathrm{low}}.
```

For a positive-advantage token, the upper ratio bound
$1+\epsilon_{\mathrm{high}}$ controls how far its probability can be rewarded
for increasing. Raising $\epsilon_{\mathrm{high}}$ therefore gives a rewarded,
low-probability exploration token more room to grow.

For a negative-advantage token, the lower ratio bound
$1-\epsilon_{\mathrm{low}}$ controls how far its probability can be rewarded
for decreasing. The phrase "lower the lower bound" is ambiguous:

- Increasing $\epsilon_{\mathrm{low}}$ lowers the numerical bound
  $1-\epsilon_{\mathrm{low}}$. This lets negative-advantage tokens be pushed
  closer to zero, removes options from the sampling space, and therefore
  **reduces** exploration.
- Decreasing $\epsilon_{\mathrm{low}}$ raises the numerical lower bound and
  protects tokens from being suppressed as aggressively. That may preserve
  support, but it does not directly give a successful rare token more room to
  increase and can also make it harder to suppress genuinely bad actions.

For example, if an old-policy token has probability $0.01$ and negative
advantage, a lower ratio bound of $0.8$ stops providing optimization benefit
once the new probability reaches $0.008$. Moving the bound down to $0.2$ would
allow it to fall to $0.002$, which shrinks rather than expands the exploration
space. DAPO therefore leaves $\epsilon_{\mathrm{low}}$ unchanged and raises only
$\epsilon_{\mathrm{high}}$. Figure 2 reports that this modification maintains
higher policy entropy and improves AIME accuracy.

The central insight is that a single symmetric clipping radius couples two
effects. Increasing it gives positive-advantage exploration tokens more uplift
room, which is desirable, but simultaneously gives negative-advantage tokens
more room to be suppressed toward zero, which can reduce diversity. Decoupled
clipping keeps the first benefit without accepting the second cost.

### Dynamic Sampling

As training progresses, an increasing fraction of prompts become too easy:
all $G$ rollouts for a prompt are correct and receive the same reward. A group
in which all rollouts are correct, or all are wrong, contains no relative
ranking information. Its normalized group-relative advantages are effectively
zero, so it contributes no policy gradient.

The filtering unit should be described as a **prompt and its rollout group**,
not an individual rollout. DAPO retains only groups satisfying

```math
0
<
\left|\left\{o_i:\mathrm{is\_equivalent}(a,o_i)\right\}\right|
<
G,
```

meaning that each retained group contains at least one correct and one
incorrect response. It oversamples prompts, generates their rollout groups,
filters homogeneous groups with accuracy $0$ or $1$, and continues filling a
dynamic buffer until it contains the target number of effective groups. Only
then does it update the policy.

The problem is not specifically that the learning rate remains fixed. Rather,
the nominal batch size hides a shrinking effective batch: zero-gradient groups
reduce the batch gradient's magnitude, increase its sensitivity to noise, and
raise gradient variance. Dynamic Sampling keeps the effective number of
informative prompts per update stable.

This method does require more rollout instances, so it cannot generally be
claimed to make every batch cheaper. In the authors' synchronous, non-pipelined
system, generation time is dominated by long-tail responses; the extra sampling
therefore does not significantly increase overall training time. Figure 6
further shows that the same performance is reached in fewer policy-update
steps, and the authors report a reduction in convergence time. This is an
empirical system-specific result, not a guarantee that Dynamic Sampling always
reduces wall-clock time.

### Token-Level Policy Gradient Loss

Original GRPO first averages token losses within each response and then
averages responses:

```math
J_{\mathrm{sample}}
=
\frac{1}{G}\sum_{i=1}^{G}
\frac{1}{T_i}\sum_{t=1}^{T_i}\ell_{i,t}.
```

This gives every response total weight $1/G$, regardless of its length. It does
not necessarily make a long response's total gradient smaller than a short
response's; rather, each token in response $i$ has weight $1/(G T_i)$.
Consequently, an individual token in a long response contributes less than an
individual token in a short response.

DAPO flattens all valid response tokens and performs one global average:

```math
J_{\mathrm{token}}
=
\frac{1}{\sum_{i=1}^{G}T_i}
\sum_{i=1}^{G}\sum_{t=1}^{T_i}\ell_{i,t}.
```

Now every token has the same weight $1/\sum_i T_i$, independent of the length
of the response containing it. The corresponding tradeoff is that a response's
total weight becomes proportional to its length: long responses have more
influence on the update than short responses.

For example, with responses of 100 and 1,000 tokens, sample-level reduction
gives each response total weight $1/2$, so their per-token weights are $1/200$
and $1/2000$. Token-level reduction gives every token weight $1/1100$, making
the responses' total weights $100/1100$ and $1000/1100$.

This change prevents useful or undesirable patterns in long responses from
being diluted merely because they occur in a long sample. It does **not** solve
within-sequence credit assignment, however. GRPO still copies one
sequence-level advantage to every token, so the objective cannot identify a
valuable reasoning span and a repetitive span inside the same rollout and
assign them opposite advantage signs. It only ensures that each token's
existing policy-gradient term receives equal length-independent aggregation
weight. Figure 4 shows that this controls the otherwise unhealthy increase in
generation entropy and response length.

#### Relation to Dr.GRPO

DAPO's Token-Level Loss and Dr.GRPO share the diagnosis that the original
$1/T_i$ response-length normalization creates an inverse-length weight for
individual tokens. Both remove that per-response denominator, so tokens are no
longer downweighted merely because they occur in a longer rollout.

They differ in the remaining normalization. DAPO divides the token-loss sum by
the **actual total number of sampled tokens**:

```math
J_{\mathrm{DAPO\ token}}
=
\frac{1}{\sum_i T_i}\sum_i\sum_t\ell_{i,t}.
```

Dr.GRPO instead divides by a **fixed constant** such as the maximum generation
budget:

```math
J_{\mathrm{Dr.GRPO}}
\propto
\frac{1}{C}\sum_i\sum_t\ell_{i,t},
\qquad C\ \text{is constant}.
```

For a fixed batch, these two length reductions have the same gradient direction
and differ by a scalar. Across batches, however, DAPO's denominator changes
with sampled response lengths, whereas Dr.GRPO keeps the scale independent of
policy-generated lengths and presents this as an unbiased policy-gradient
estimator.

Dr.GRPO also removes a second normalization that DAPO retains. DAPO uses

```math
\hat A_i=\frac{R_i-\bar R}{s_R},
```

where $s_R$ is the within-question reward standard deviation. Dr.GRPO uses the
centered reward

```math
\widetilde A_i=R_i-\bar R
```

without dividing by $s_R$, because that division gives different effective
weights to questions with different reward variances and creates a
question-difficulty bias. DAPO's Dynamic Sampling filters zero-signal groups
whose accuracy is exactly $0$ or $1$, but it does not remove this standard
deviation weighting among the retained mixed-reward groups.

### Overlong Reward Shaping

Long responses are truncated at a maximum generation length. If every truncated
response is assigned an abrupt punitive outcome reward, a trajectory whose
reasoning was otherwise sound may be treated as wholly wrong merely because it
did not finish before the length limit. Since the same sequence-level advantage
is applied throughout the rollout, this creates noisy and potentially
confusing training signals.

The paper first studies **Overlong Filtering** as an ablation. This operates at
the individual rollout level: if 3 of 16 rollouts are truncated, their
policy-gradient losses are masked, so those three rollouts do not update the
actor. The method does not resample replacements for them. This is different
from Dynamic Sampling, which repeatedly samples until it fills the batch with
valid prompt-level groups.

Filtering demonstrates that truncated rollouts are a major source of reward
noise, but it discards their training signal and does not directly teach the
model to stop earlier. DAPO therefore proposes **Soft Overlong Punishment**.
With maximum length $L_{\max}$ and a penalty buffer of $L_{\mathrm{cache}}$,
the added length reward is

```math
R_{\mathrm{length}}(y)
=
\begin{cases}
0,
& |y|\le L_{\max}-L_{\mathrm{cache}},\\
\dfrac{(L_{\max}-L_{\mathrm{cache}})-|y|}
      {L_{\mathrm{cache}}},
& L_{\max}-L_{\mathrm{cache}}<|y|\le L_{\max},\\
-1,
& |y|>L_{\max}.
\end{cases}
```

The penalty is zero for ordinary lengths and then decreases linearly from $0$
to $-1$ over the final buffer before the hard limit. It is added to the
rule-based correctness reward, providing a gradual signal to finish before
truncation instead of an abrupt all-or-nothing punishment.

Conceptually, the soft approach has two reward **components**, but the optimizer
still receives one scalar reward per rollout:

```math
R_{\mathrm{total}}(y)
=
R_{\mathrm{correctness}}(y)
+
R_{\mathrm{length}}(y).
```

The implementation literally adds the overlong penalty to the verifier reward;
it does not require a second learned reward model. With correctness rewards
$+1/-1$ and a length penalty in $[-1,0]$, an ordinary correct response receives
$+1$, while a correct response at the hard length boundary can fall to $0$.
An ordinary wrong response receives $-1$, while an equally wrong but overlong
response can fall toward $-2$. Group-relative normalization is then applied to
these total scalar rewards, allowing length to distinguish responses even when
their correctness rewards are identical.

Overlong Filtering is indeed simpler and more abrupt at implementation level:
detect truncation and mask the corresponding actor loss. Soft shaping requires
computing one additional deterministic length term, but preserves a graded
training signal before the hard boundary.

The maintained official DAPO recipe notes that Overlong Filtering overlaps with
Overlong Reward Shaping and was disabled in most experiments, including the
best-performing run; the released implementation focuses on the soft overlong
penalty. The paper does not specify whether masked truncated rollouts should
also be removed from group reward normalization, so the safe claim is only that
their actor loss is masked.

## Experiments

### Training details

The implementation uses `verl` with Qwen2.5-32B Base and naive GRPO as the
baseline. AdamW has a constant learning rate of $1\times10^{-6}$ after a linear
warm-up over 20 rollout steps. Each rollout step contains 512 prompts with 16
responses per prompt, or 8,192 generated responses. The training mini-batch size
is 512, giving 16 gradient updates per rollout step.

Training uses DAPO-Math-17K. The authors transform targets into integers where
necessary so that the rule-based verifier can parse answers reliably and add
less reward noise.

The length configuration has two nested thresholds rather than two independent
maximum lengths. The expected response-length boundary is 16,384 tokens, and a
4,096-token soft-punishment buffer extends from that point to the hard
generation limit:

```math
L_{\mathrm{expected}}=16{,}384,\qquad
L_{\mathrm{cache}}=4{,}096,\qquad
L_{\max}=20{,}480.
```

The Clip-Higher radii are
$\epsilon_{\mathrm{low}}=0.2$ and
$\epsilon_{\mathrm{high}}=0.28$.

One evaluation detail matters when interpreting the headline result. The authors
repeat the AIME evaluation set 32 times and report `avg@32`, using temperature
$1.0$ and top-$p=0.7$. The reported 50-point result is therefore an average
sampling accuracy rather than a single greedy-decoding score.

### Main result and progressive ablation

Table 1 reports the following progressive recipe on AIME 2024 `avg@32`:

| Configuration | Score | Marginal change in this sequence |
|---|---:|---:|
| Naive GRPO | 30 | - |
| + Overlong Filtering | 36 | +6 |
| + Clip-Higher | 38 | +2 |
| + Soft Overlong Punishment | 41 | +3 |
| + Token-Level Loss | 42 | +1 |
| + Dynamic Sampling (DAPO) | 50 | +8 |

Dynamic Sampling has the largest final marginal gain in this sequence. The
table is a progressive recipe rather than a clean set of independent
single-factor ablations, however, so it does not establish that Dynamic
Sampling alone always contributes exactly eight points or is independently the
most important component. The techniques can interact, and their measured
increments depend on the order in which they are added.

Several components improve stability through different mechanisms:

- **Dynamic Sampling** keeps the number of informative prompt groups per update
  stable, strengthening the batch gradient and reducing its noise sensitivity.
- **Token-Level Loss** removes inverse-length token weighting. Its direct score
  increment is only one point in Table 1, but the authors report more stable
  training and healthier response-length growth; it controls pathological
  length inflation rather than simply increasing or decreasing length.
- **Overlong Filtering or Soft Overlong Punishment** reduces reward noise caused
  by hard truncation. Filtering masks the noisy rollouts, while soft punishment
  replaces the abrupt boundary with a graded length signal.
- **Clip-Higher** maintains policy entropy and rollout diversity, preventing
  premature entropy collapse.

The paper's table lists both Overlong Filtering and Soft Overlong Punishment
along the progressive path, but the maintained official recipe says the two
overlap and that the best reproduced configuration generally uses soft shaping
without enabling hard filtering.
