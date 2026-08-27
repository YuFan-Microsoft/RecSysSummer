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
