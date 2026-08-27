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

$$
r_t(\theta)
=
\frac{\pi_\theta(o_t\mid q,o_{<t})}
     {\pi_{\theta_{\mathrm{old}}}(o_t\mid q,o_{<t})}.
$$

PPO maximizes the clipped surrogate objective

$$
\min\left(
r_t\hat A_t,\;
\operatorname{clip}(r_t,1-\epsilon,1+\epsilon)\hat A_t
\right).
$$

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

$$
A_t = Q(s_t,a_t)-V(s_t).
$$

In PPO-based RLHF, the reward-model score is commonly placed at the end of the
sequence, sometimes alongside token-level KL penalties. A learned critic
estimates $V(s_t)$ for each prefix, and Generalized Advantage Estimation uses
the temporal-difference residuals

$$
\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)
$$

to produce $\hat A_t$. Therefore, the final sequence reward contributes to the
return of all preceding tokens, but it is not merely divided equally among
them. Different prefixes can receive different advantages because their value
estimates differ.

GRPO uses a simpler mechanism. It removes the critic and normalizes completed
sequence rewards within the $G$ responses sampled for the same question:

$$
\hat A_i =
\frac{R_i-\operatorname{mean}(\{R_j\}_{j=1}^{G})}
     {\operatorname{std}(\{R_j\}_{j=1}^{G})}.
$$

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

$$
A_{\mathrm{correct}}=\sqrt{\frac{1-p}{p}},
\qquad
A_{\mathrm{wrong}}=-\sqrt{\frac{p}{1-p}}.
$$

Thus a rare correct response receives a particularly strong positive signal.
If all 16 responses are correct or all are wrong, however, the standard
deviation is zero and there is no within-group ranking signal. This degenerate
case directly motivates DAPO's Dynamic Sampling, which keeps only groups
containing both correct and incorrect responses.

There are two different length scalings that should not be conflated. If a
response has sequence-level advantage $A_i=0.5$, then GRPO sets
$A_{i,t}=0.5$ for every token; it does not define
$A_{i,t}=0.5/|o_i|$. However, original GRPO computes

$$
\frac{1}{|o_i|}\sum_t \ell_{i,t}(A_{i,t}),
$$

so the outer sequence average makes each individual token's contribution to
the final objective carry an effective factor of $1/|o_i|$. The advantage
tensor remains $0.5$ at every token, while the loss aggregation supplies the
length normalization. DAPO's Token-Level Loss later replaces this per-sequence
normalization with one normalization over all valid tokens in the batch.
