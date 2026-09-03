# Self-supervised User Profile Generation for Personalization

**Authors:** Clark Mingxuan Ju, Yuwei Qiu, Tong Zhao, Neil Shah

**arXiv:** https://arxiv.org/abs/2606.05336 (v1)

**PDF:** https://arxiv.org/pdf/2606.05336

**Venue:** —

**Categories:** cs.CL (primary)

**Published:** 2026-06-03 · **Updated:** 2026-06-03

---

<!-- Reading progress: complete for the chosen scope. Read the abstract, §1, and §3.1 to §3.7, with a targeted check of §4.1; experimental results were intentionally not reviewed in detail. Verified against the PDF. Statements below are the paper's unless marked as an inference or an open question. -->

## TL;DR

BUMP learns a free-form natural-language user profile without labels from any downstream personalization task. Its central bet is that a good profile should be bidirectionally consistent with the user's held-out behavior: the profile should retrieve that user's interactions, and those interactions should retrieve that user's profile. The method stands or falls on whether this user-discriminative retrieval objective learns broadly useful preferences rather than superficial identity cues.

## Where it sits

Personalized LLM applications include recommendation, search, dialogue, and content generation. The same query may require a different answer for each user, yet a frozen or private LLM often exposes only its prompt as the personalization interface. A straightforward solution is therefore to summarize a user's interaction history into a natural-language profile and prepend it to future prompts.

Existing learned profile generators commonly use explicit rewards from labeled downstream tasks. This makes profile learning task-dependent: every target task needs its own labels, reward definition, or downstream evaluator. BUMP instead asks whether raw interaction logs can supervise a task-agnostic profile generator.

## Introduction: why a profile instead of raw history?

Traditional collaborative-filtering embeddings capture statistical user patterns, but they do not naturally interface with an instruction-tuned LLM, especially when the model is closed-weight and can only be personalized through its input. A natural-language profile uses the prompt as this personalization surface without retraining the downstream backbone.

The most direct alternative is to place the full interaction history in every prompt. The introduction identifies several deployment problems with this approach:

- Real users may have hundreds or thousands of interactions, eventually exceeding the context window.
- Repeating the history on every request incurs large prefill latency, KV-cache memory, and inference cost.
- Even when the sequence fits, relevant signals can be lost in the middle or diluted by irrelevant events.

A compact profile can be precomputed offline, cached, and reused for many queries. It is therefore not only a semantic user representation but also a systems optimization that amortizes context construction and prefill cost.

### The paper overstates the labeling problem

The introduction claims that task-supervised profile learning requires an annotated corpus and fresh label collection for every target task. I do not find this universally convincing. Recommendation systems already receive clicks, watches, ratings, and other interaction logs as naturally occurring implicit labels. In that setting, downstream supervision is not necessarily expensive human annotation.

A more defensible criticism of task-supervised profile learning is that every downstream task still needs its own reward or oracle, and the profile generator may need to be retrained for each objective. A click-optimized profile can also overemphasize features useful for recommendation while omitting preferences relevant to search, writing, or dialogue. BUMP may therefore reduce task-specific engineering and task bias even when labels themselves are cheap. This is a narrower and stronger motivation than the paper's blanket claim about annotation cost.

### The self-supervised premise

The introduction derives BUMP from two desired properties. A profile should predict the user's held-out or future behavior, and the same behavior should identify the corresponding profile among profiles from other users. This turns within-user consistency into supervision without invoking a labeled downstream task.

Calling the signal "self-supervised" is reasonable under the paper's terminology because the target is constructed from raw logs rather than external annotations. However, the held-out interactions still function as implicit behavioral targets. The real distinction is not the complete absence of supervision; it is that the supervision is task-agnostic and constructed from the same user history corpus.

## What the abstract actually proposes

Given an observed interaction history, an LLM generates a free-form textual user profile. The paper trains this generator with GRPO, using a bidirectional in-batch ranking objective evaluated by a small LLM judge.

| Direction | Query | Items being ranked | Desired result |
|---|---|---|---|
| **Profile to interaction** | The generated profile for user $u$ | Held-out interactions from users in the batch | Rank user $u$'s own held-out interactions above other users' interactions. |
| **Interaction to profile** | A held-out interaction from user $u$ | Generated profiles from users in the batch | Rank user $u$'s own profile above other users' profiles. |

The profile is therefore the query, not the key, in the first direction. The roles reverse in the second direction. Other users in the batch provide negatives without additional annotation. Both directions use multi-positive NDCG, and their scores are combined into a dense reward for each profile rollout.

## Method

### §3.1 Problem setup

The method starts with a set of users $\mathcal{U}$ . Each user $u$ has a chronologically ordered interaction history:

$$
H_u
=
\left(
h_{u,1},
h_{u,2},
\ldots,
h_{u,T_u}
\right).
$$

An interaction is represented as a textual record. Depending on the application, it may be a dialogue turn, an item interaction with metadata, a written post, or a paper.

The goal is to train a profile-generation LLM that maps the visible part of this history to a free-form textual profile:

$$
s_u
\sim
\pi_\theta
\left(
\cdot \mid H_u^{\text{vis}}
\right).
$$

There is no gold profile showing what $s_u$ should say, and no labeled downstream task is available during profile-generator training. The only permitted source of supervision is the user's own interaction stream. This does not mean that training has no signal; later sections construct that signal by withholding part of the same stream.

### §3.2 From history splitting to profile rollouts

Each chronologically ordered history is partitioned into a visible prefix and a held-out portion:

$$
H_u
=
\left(
H_u^{\text{vis}},
H_u^{\text{ho}}
\right),
\qquad
H_u^{\text{ho}}
=
\left(
h_u^{(1)},
\ldots,
h_u^{(P)}
\right).
$$

The profile policy sees only $H_u^{\text{vis}}$ and emits one or more candidate profiles. For a training batch of $B$ users, all generated profiles and held-out items form the positives and in-batch negatives used by the two ranking directions.

### §3.3 Forward reward: profile to future interactions

For user $u$ , the candidate pool contains all $P$ of that user's held-out interactions as positives and $K$ held-out interactions sampled from other users as negatives. The frozen LLM judge receives $s_u$ as its query and returns a complete ranking of the $P+K$ candidates.

If $r_{p,\text{fwd}}^u$ is the rank of the $p$-th positive, the forward multi-positive NDCG is

$$
R_{\text{fwd}}^u
=
\frac{1}{Z_P}
\sum_{p=1}^{P}
\frac{1}
{\log_2\left(r_{p,\text{fwd}}^u+1\right)},
$$

with ideal-ranking normalizer

$$
Z_P
=
\sum_{j=1}^{P}
\frac{1}
{\log_2(j+1)}.
$$

This is a soft ranking objective, not a hard all-or-nothing requirement. The reward reaches 1 exactly when every positive occupies one of the top $P$ positions. Imperfect rankings still receive partial credit according to where the positives appear.

### §3.3 Backward reward: future interaction to profile

For each held-out interaction $h_u^{(p)}$ , the candidate pool contains user $u$'s generated profile as the sole positive and $K$ profiles from other users as negatives. The held-out interaction becomes the query, and the judge ranks the $1+K$ profiles.

If $r_{p,\text{bwd}}^u$ is the rank of the correct profile for the $p$-th held-out interaction, the method averages the single-positive NDCG over all $P$ held-out interactions:

$$
R_{\text{bwd}}^u
=
\frac{1}{P}
\sum_{p=1}^{P}
\frac{1}
{\log_2\left(r_{p,\text{bwd}}^u+1\right)}.
$$

The forward reward asks whether the profile predicts the user's held-out behavior, while the backward reward asks whether each held-out behavior identifies the profile. Their sum supplies the bidirectional rollout reward used to optimize the profile policy with GRPO. The following section adds regularization before defining the final reward.

### What actually performs the ranking?

Both directions use a frozen LLM judge. The judge receives a query and a candidate list in its prompt, then emits a ranked permutation. In the experiments, both the profile policy and judge are initialized from Qwen3-4B-Instruct-2507. The judge is served separately with vLLM and guided-regex decoding so that its output is always a parseable ranking.

The notation has three different counts that should not be conflated:

- $G$ is the number of profile rollouts generated for GRPO.
- $P$ is the number of held-out positives for each user.
- $K$ is the number of in-batch negatives placed in a judge ranking.

The actual experiment uses $G=8$ profile rollouts, $P=1$ subsequent held-out interaction, and $K=8$ negatives. It also averages each reward over $M=2$ random candidate presentation orders to reduce the LLM judge's position bias. Although the general forward equation is multi-positive, the reported experiment has only one positive per user.

The paper does not report an experiment or ablation with $P>1$ . The general formulation and the illustrative forward-ranking example allow multiple positives, but every reported training configuration uses a single subsequent held-out item. The practical benefit of multi-positive NDCG, including whether multiple future interactions reduce backward-reward noise, is therefore not empirically tested.

### Challenge 1: could an embedding model replace the LLM judge?

Yes, an embedding model could score profile-interaction compatibility much more cheaply. This would reduce the method to a more conventional contrastive or retrieval objective and provide a natural baseline. It could also support a hybrid system in which embeddings retrieve difficult candidates and the LLM only reranks a small subset *(my idea)*.

The likely argument for an LLM judge is that a cross-encoder-style prompt can reason over free-form profiles and heterogeneous textual interactions more richly than a fixed dot product. However, this advantage needs empirical evidence because the judge is expensive and introduces position bias, prompt sensitivity, and its own semantic preferences. The paper already uses frozen BGE embeddings for BUMP+ hard-negative mining, but not as a replacement reward model. An embedding-judge baseline would directly test whether the costly LLM ranking is necessary.

### Challenge 2: backward retrieval can contain false negatives

The backward objective assumes that every held-out interaction identifies one unique correct user profile. That assumption can fail when multiple users click the same item or exhibit nearly identical interests. Their profiles may all be genuinely compatible with the query interaction, yet the single-positive NDCG labels only the originating user's profile as correct and treats the rest as negatives. The resulting reward can be noisy or can encourage the profile to encode arbitrary user-specific fingerprints rather than useful preferences.

Averaging backward rewards over multiple held-out interactions could reduce variance when those interactions provide independent evidence. However, the actual experiments use $P=1$ , so this protection is absent. BUMP+ selects topically similar users as harder backward negatives, which may force finer distinctions but may also increase the false-negative problem when similar profiles are legitimately relevant *(inference)*.

### §3.4 Position debiasing is shuffled-order averaging

The LLM list judge can favor candidates that appear earlier in its input. The paper addresses this by independently shuffling the candidate list $M$ times, running the judge on every shuffled presentation, computing NDCG for each result, and averaging:

$$
\bar{R}_{\text{dir}}^u
=
\frac{1}{M}
\sum_{m=1}^{M}
\operatorname{NDCG}(\sigma_m).
$$

Calling this an unbiased Monte Carlo estimator is mathematically correct: uniformly sampled permutations estimate the expected judge NDCG under a uniformly random input order. Operationally, however, it is simply randomized-order ensembling. It averages NDCG rather than the raw predicted ranks.

The word "unbiased" also needs care. The estimator is unbiased for the judge's order-averaged reward, not for an objective ground-truth notion of profile-interaction relevance. Shuffling can reduce variance caused by presentation position, but it cannot remove semantic errors, prompt bias, or systematic preferences of the judge. The experiment uses only $M=2$ permutations, so the technique is lightweight rather than a substantial methodological contribution.

### §3.4 Length penalty and reward hacking

The paper reports that optimizing NDCG alone encourages the policy to pad profiles with broadly relevant boilerplate. A longer profile can mention many generic interests, making almost any held-out interaction appear superficially plausible to the judge without producing a more specific user representation.

To suppress this behavior, BUMP applies no penalty below a per-task token threshold $T$ and an increasingly strong penalty above it. The final rollout reward is

$$
R(s_u)
=
\bar{R}_{\text{fwd}}^u
+
\bar{R}_{\text{bwd}}^u
-
R_{\text{len}}(s_u).
$$

An embedding reward would not eliminate reward hacking. It would remove list-position bias if candidates were scored independently and would be much cheaper, but a profile policy trained directly against a fixed encoder could still exploit that encoder's geometry. Possible shortcuts include keyword stuffing, repeating broad topic terms, emphasizing lexical overlap, or discovering token patterns that receive high similarity without faithfully representing the user *(inference)*.

In this particular setting, a normalized pairwise embedding reward may nevertheless be harder to hack than the prompted listwise LLM judge *(inference)*. It has a smaller behavioral attack surface: no candidate-order effect, no instruction-following vulnerability, no free-form ranking output to parse, and no obvious reason that simply increasing profile length should improve cosine similarity. Its low cost would also make it practical to ensemble several encoders or randomize representations during training. This is a comparative robustness argument, not a claim that embeddings are immune to optimization shortcuts.

This is a general Goodhart problem: once a fixed proxy becomes the optimization target, the policy can learn features that improve the proxy without improving the intended downstream property. Bidirectional negatives and a length penalty may reduce some generic-profile shortcuts, but neither guarantees faithfulness. A stronger test would train against one reward model and evaluate profile quality with a different judge, embedding model, and downstream tasks *(my idea)*.

### §3.5 BUMP+: harder comparisons

BUMP+ uses frozen BGE embeddings to make the ranking signal less trivial. The paper describes the whole extension as hard-negative mining, but the two directions do different things:

- In the forward direction, it selects the user's own items that are least similar to the visible-history centroid. These remain positives, so this is more precisely hard-positive selection: the profile must cover future behavior that is not an obvious topical continuation of the visible history.
- In the backward direction, it selects profiles from users whose visible histories are most similar to the target user's history. These are genuine hard negatives: the judge must distinguish among topically similar users rather than unrelated users.

The backward construction may provide a stronger signal, but it also increases the risk of false negatives when multiple similar profiles are legitimately compatible with the same interaction.

### §3.6 Downstream use

After GRPO training, the profile generator is frozen. It generates one profile per user offline, and that string is cached. At serving time, the cached profile is simply prepended to a downstream prompt and can be consumed by an arbitrary model for classification, ranking, dialogue, or generation. There is no additional BUMP optimization in this deployment step.

### §3.7 Why the paper calls this self-supervised learning

The paper maps its objective directly onto the standard contrastive SSL vocabulary. Each user is treated as an implicit class; the generated profile and held-out interaction are two views of that class; other users provide in-batch negatives; and the forward and backward rewards play the role of a symmetric contrastive loss.

This interpretation is coherent but adds no new mechanism beyond the bidirectional reward already described. From a recommender-systems perspective, the forward half remains familiar implicit-feedback learning. The distinctive choice is to lift the views and matching function into free-form language using a profile policy and LLM judge.

## What clicked from the abstract

This reframes profile quality as a form of predictive user consistency. A profile is good when it compresses the observed history into information that remains specific enough to identify the same user's unseen behavior. No downstream task has to define in advance what the profile should say.

The profile is not merely trained to reconstruct the interactions from which it was generated. It is evaluated against held-out interactions, which should force it to capture persistent preferences that extend beyond the observed history. The reverse retrieval direction discourages a profile from being so generic that many users' interactions match it equally well.

My current mental model is symmetric contrastive learning with in-batch negatives *(my analogy)*. The generator rolls out several profiles from a user's observed history. The user's held-out interactions are positives, while other users' interactions and profiles in the batch act as negatives in the two retrieval directions. This resembles bidirectional text-embedding or CLIP-style training at the level of supervision structure.

The important difference is that BUMP does not define similarity as a differentiable embedding dot product and does not directly optimize an InfoNCE loss. A frozen small LLM judge produces rankings, bidirectional multi-positive NDCG converts those rankings into a rollout-level reward, and GRPO updates the profile generator.

The deeper assumption is that a representation useful for distinguishing and predicting users' held-out interactions will transfer to personalized generation, recommendation, search, and other downstream tasks *(inference)*. This is plausible, but it is not guaranteed: user-identifying information and task-relevant preference information are not necessarily the same.

### Is this only a summarization model?

At the output level, it is indeed a model that summarizes interaction history into a user profile. The retrieval objective does not change that basic function; it supplies a way to decide which possible summary is better.

The method avoids the most direct reconstruction shortcut by defining each user's history as a chronologically ordered sequence. It generates the profile using only a visible prefix and evaluates it against a held-out suffix. A profile cannot simply copy the positive interactions because those interactions were not in its input. To succeed, it must preserve something stable enough about the user for the judge to associate the profile with later behavior.

However, the objective does not directly predict the next interaction. It only asks the judge to rank the user's held-out records above records from other users. This is a weaker surrogate. A broad topical summary, persistent writing style, or distinctive user fingerprint may separate users without capturing the fine-grained preference needed to predict what the user will do next.

The backward direction can strengthen this concern because it explicitly rewards user identifiability. Random in-batch negatives may also make the task easy when users occupy different domains. The method therefore needs downstream experiments and hard-negative analysis to demonstrate that it learns predictive personalization rather than merely recognizable summaries.

### Forward-only BUMP resembles standard recommender training

If the backward direction is removed, the remaining objective has the same supervision structure as a conventional implicit-feedback recommender:

- A visible history is encoded into a user representation, which here happens to be a free-form natural-language profile.
- The user's held-out future interactions are positives.
- Other users' interactions provide sampled negatives.
- Training rewards the user representation when positives rank above negatives.

From a recommender-systems perspective, this is structurally similar to next-item prediction or contrastive user-item learning. The main implementation differences are that the user representation is generated language, a frozen LLM judge supplies the ranking, and multi-positive NDCG becomes the policy reward.

Calling this self-supervised is terminologically defensible because the targets are created automatically from the same raw sequence rather than supplied by human annotators. However, it should not be mistaken for a fundamentally new supervision principle in recommendation. Observed future clicks or interactions have long served as implicit labels in exactly this way.

The backward direction adds symmetric profile-behavior alignment and explicitly encourages the profile to be identifiable from behavior. It does not change the fact that the forward half is a familiar implicit-feedback objective. The paper's more specific novelty is applying this bidirectional objective to free-form, cross-task natural-language profile generation with an LLM judge and GRPO, not inventing self-supervision from held-out user behavior.

## Reader's insights and open questions

- *(open)* Do in-batch negatives create false negatives when different users have genuinely similar interests?
- *(open)* Can the generator exploit names, item IDs, stylistic artifacts, or other identity shortcuts instead of learning transferable preferences?
- *(open)* Does bidirectional retrieval quality actually correlate with downstream personalization performance across tasks?
- *(open)* How much of BUMP's benefit comes from avoiding task-specific reward engineering rather than avoiding labels, especially in recommendation settings where implicit feedback is already abundant?
- *(open)* How much reward can a generic topic or style summary obtain without representing the fine-grained preferences needed for future prediction?
- *(open)* Can a frozen embedding judge match the downstream quality of the Qwen3 judge at a fraction of the reward-computation cost?
- *(open)* Do profiles optimized against the Qwen3 judge retain their advantage when evaluated by an independent judge or embedding model that was not part of training?
- *(open)* How often do backward candidate pools contain duplicate items or multiple semantically valid profiles, especially with only one held-out interaction per user?

## Net read

The useful idea is to train a reusable natural-language profile without choosing a downstream task, using consistency between a profile generated from past behavior and the user's held-out future behavior. The forward half is structurally familiar implicit-feedback recommendation training, while the backward half adds user identifiability but also introduces false-negative and fingerprinting risks.

The paper's SSL framing is coherent, but it packages a standard contrastive recipe in free-form language rather than introducing a fundamentally new supervision principle. The frozen LLM judge is expensive, position-sensitive, and vulnerable to proxy optimization; a normalized embedding judge is an obvious cheaper and potentially more robust alternative that the paper should compare directly. The fact that the actual experiment uses only one held-out positive per user also weakens the multi-positive framing and leaves backward-reward noise unresolved.

My final methodological take is that BUMP is a clever task-agnostic profile-learning formulation, but its strongest motivation is avoiding per-task reward engineering, not eliminating labels. Its value ultimately depends on whether bidirectional retrieval reward predicts real downstream personalization better than simpler summary, embedding, and implicit-feedback baselines.
