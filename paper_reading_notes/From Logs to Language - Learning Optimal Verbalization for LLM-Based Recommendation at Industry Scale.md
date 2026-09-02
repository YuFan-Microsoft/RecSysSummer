# From Logs to Language: Learning Optimal Verbalization for LLM-Based Recommendation at Industry Scale

**Authors:** Yucheng Shi, Ying Li, Yu Wang, Yesu Feng, Arjun Rao, Rein Houthooft, Shradha Sehgal, Jin Wang, Hao Zhen, Ninghao Liu, Linas Baltrunas

**arXiv:** https://arxiv.org/abs/2602.20558 (v2)

**PDF:** https://arxiv.org/pdf/2602.20558

**Venue:** Work in progress

**Categories:** cs.AI (primary), cs.IR

**Published:** 2026-02-24 · **Updated:** 2026-03-19

---

<!-- Reading progress: complete. Read the abstract, introduction, problem formulation, method, experiments, and results; skimmed the analysis, discussion, and conclusion. Verified against the PDF. Statements below are the paper's unless marked as an inference or an open question. -->

## TL;DR

The paper treats the conversion of structured interaction logs into natural language as a learnable part of the recommendation pipeline rather than a fixed preprocessing rule. A verbalization agent is trained with downstream recommendation accuracy as its reward, so it can learn which information to preserve, remove, enrich, or reorganize. The central bet is that better language input representations can materially improve an LLM recommender even without explicit labels describing what an ideal verbalization should look like.

## Where it sits

Template-based approaches concatenate selected fields from a user's interaction history into a predetermined textual format. This is simple, but it assumes that every retained field deserves a fixed position and that the downstream LLM can identify the useful preference signals despite noise and awkward organization.

This paper takes a data-centric approach instead. It optimizes the textual context presented to the recommender, using actual recommendation performance to judge whether a verbalization is useful. I currently see this as a user-representation problem expressed through natural language, rather than only as a prompt-writing problem.

## Introduction: why verbalization matters

A raw interaction log may contain timestamps, devices, item IDs, engagement types, and viewing durations. Putting these fields into a textual template makes them technically consumable by an LLM, but it does not necessarily turn them into an effective language representation.

| Problem with raw or templated logs | Why it hurts the LLM recommender | What learned verbalization could do |
|---|---|---|
| The input contains heterogeneous, low-level fields. | The LLM must spend capacity parsing the schema before it can reason about preference. | Normalize and reorganize the information into a semantically clearer form. |
| Interactions do not all have equal predictive value. | Weak or irrelevant actions can obscure the preference signals that matter for the next prediction. | Filter noise and summarize repeated or related evidence. |
| Bare behavioral records lack item semantics. | The LLM must infer from behavioral patterns without enough content understanding, which is especially limiting for cold-start items. | Incorporate relevant metadata that explains what the interacted items are. |

My analogy is that this avoidable parsing burden resembles converting text into an image and then asking an LLM to perform OCR before understanding the content *(my analogy)*. The comparison is not literal because interaction logs are already symbolic rather than visual. What it captures is the representational tax: the model must first reconstruct useful meaning from an inconvenient encoding before doing the recommendation task.

## The two-component decomposition

The paper separates context construction from preference prediction:

- The **Verbalizer** converts the raw user interaction history into a useful natural-language representation.
- The **Reasoner** consumes that representation and performs the actual recommendation.

This separation makes the input representation itself optimizable. The important refinement is that the Verbalizer does not receive arbitrary internal feedback from the Reasoner. It receives a reward derived from whether the Reasoner's final recommendation is correct. In the subsequent training stage, the Reasoner is optimized using ground-truth engagement labels. A targeted check of §4.3 further shows that Verbalizer training uses a fixed oracle Reasoner rather than simultaneously co-training the target Reasoner.

### The Reasoner is a generative reranker

The downstream candidate-selection model is the Reasoner, which §4.2 defines as a causal language model. It receives the verbalized user context together with the candidate set. Rather than assigning an explicit scalar score to every candidate and sorting those scores, it generates an answer through standard autoregressive decoding, after which the predicted item is extracted from the generated text.

The experimental task in §5.1 makes this concrete: the input contains up to 100 recent user interactions and 10 candidate items, and the Reasoner must predict which candidate the user actually engaged with next. The reported metric is Recall@1 on previously unwatched discovery items. I therefore think of the Reasoner as a generative LLM reranker or candidate classifier, not as a conventional embedding-based ranker *(inference)*.

There are also two distinct Reasoner roles:

- A fixed, capable closed-source **oracle Reasoner** evaluates candidate verbalizations during the first training stage.
- A trainable **target Reasoner** learns from the frozen Verbalizer's outputs during the second stage.

The paper identifies the Verbalizer models as Qwen-3 8B and 32B, but it does not clearly name the exact oracle or target Reasoner models in the PDF. This leaves an important reproducibility detail unresolved.

### The chicken-and-egg question

The training dataset supplies three concrete objects for each example: a raw history, a candidate set, and the ground-truth item that the user engaged with next. It does not supply a separately defined or labeled user context. At any point in training, the "user context" is simply the current Verbalizer output for that raw history.

The apparent circle is broken by renting a recommendation capability from outside the two trainable stages. During Stage 1, a fixed, already capable closed-source LLM acts as the oracle Reasoner. The Verbalizer generates several candidate contexts from the same raw history. The oracle reads each context together with the candidate set and chooses an item. Comparing that choice with the observed next item gives the Verbalizer its reward.

After this process has trained the Verbalizer, Stage 2 freezes it and trains the target Reasoner directly against the observed next-item labels. The target Reasoner therefore does not need to provide a useful learning signal before it has itself been trained.

This makes the pipeline non-circular mathematically, but it introduces a strong bootstrap assumption. The oracle must already have nontrivial zero-shot or prompted ability to infer preference from an imperfect textual context, and the initial Verbalizer must produce candidates that lead to different accuracy rewards. If every sampled context produces the same accuracy outcome, the length component may still create some reward variation, but there is no group-relative signal about which context is semantically better for recommendation. The paper motivates the use of a strong oracle, but it does not disclose the oracle identity, its prompt, or enough initialization detail to show exactly how reliable this bootstrap is.

## Method

### §4.1 Two Verbalizer variants

The paper explores two ways to define the Verbalizer's output space:

| Variant | Model output | Post-processing before the Reasoner |
|---|---|---|
| **Action-based** | For every interaction, the model emits a binary keep decision and a binary metadata-enrichment decision. | A deterministic executor removes discarded events and augments selected events with metadata. The resulting representation becomes the Reasoner context. |
| **Rewrite-based** | The model generates a complete natural-language rewrite of the interaction history. | The generated text itself becomes the Reasoner context. It can aggregate events, summarize patterns, and reorganize information without being limited to the two discrete actions. |

Calling rewrite-based "unrestricted" is directionally right when comparing its action space with the action-based variant, but it is not literally unconstrained. Its prompt asks it to preserve important signals and remove noise, while the RL objective also imposes recommendation, length, and KL constraints. The paper reports that this rewrite-based variant performs better and adopts it for the primary experiments.

Both variants are evaluated through the same downstream interface. During Verbalizer training, the realized context is passed to the oracle Reasoner for reward. During the second stage and inference, it is passed to the target Reasoner for recommendation. The action-based model's raw keep/add bits are therefore not themselves the final natural-language input; the deterministic execution step comes first.

### Metadata provenance is unclear

The paper does not describe an external tool call, retrieval API, or agent loop for obtaining metadata. For the action-based variant, it merely says that selected interactions are deterministically "augmented with additional metadata," without identifying the metadata store, fields, or retrieval procedure.

The rewrite-based story is even less explicit. §5.1 says each dataset record contains timestamp, item ID, title, engagement type, and duration, while the illustrative raw input in Table 3 already contains year and plot tags. This suggests that at least some metadata is made available before the rewrite *(inference)*, but the paper never documents that preprocessing step. There is no basis for claiming that the Verbalizer autonomously fetches metadata. If it instead relies on the language model's parametric knowledge, factual errors and hallucinated attributes would become a serious concern *(open)*.

### §4.3 Stage 1: training the Verbalizer

For each training example, the method starts with a user history $H_u$ , candidate set $\mathcal{C}$ , and ground-truth next item $y^*$ . It samples a group of $G$ natural-language representations from the current Verbalizer:

$$
\{x_1, x_2, \ldots, x_G\}
\sim
\pi_\theta^V(\cdot \mid H_u).
$$

Each rollout is passed to the fixed oracle Reasoner together with the candidates. The accuracy reward is binary:

$$
r_i^{\text{acc}}
=
\begin{cases}
1, & \pi_{\text{oracle}}^R(x_i,\mathcal{C}) = y^*, \\
0, & \text{otherwise}.
\end{cases}
$$

The paper adds a length reward because accuracy-only optimization could produce an over-compressed text that loses information or an unnecessarily verbose text that raises training and inference cost. The total reward is

$$
r_i^{\text{total}}
=
\alpha r_i^{\text{acc}}
+
(1-\alpha)r_i^{\text{len}},
\qquad
\alpha = 0.9.
$$

The length term is a plateau reward whose preferred compression-ratio range is approximately 0.3 to 0.7. It penalizes both over-compression and under-compression, so it encourages rather than guarantees an acceptable length.

The total rewards are normalized within the sampled group to produce relative advantages, after which the Verbalizer is updated with the standard clipped GRPO objective and a KL penalty to a reference policy. The method is conceptually simple: sample several candidate contexts, let downstream recommendation correctness rank their utility, add a modest length preference, and reinforce the relatively better rollouts.

### §4.4 Stage 2: training the Reasoner

After the Verbalizer converges, the paper freezes it. For each user history, the frozen Verbalizer generates one textual context:

$$
x = \phi_\theta(H_u).
$$

The target Reasoner receives that context and candidate set, then samples a group of $G$ predictions:

$$
\{\hat{y}_1, \hat{y}_2, \ldots, \hat{y}_G\}
\sim
\pi_\psi^R(\cdot \mid x,\mathcal{C}).
$$

The Stage 2 reward differs slightly from the Stage 1 accuracy reward:

$$
r_j
=
\begin{cases}
+1, & \hat{y}_j = y^*, \\
-1, & \text{otherwise}.
\end{cases}
$$

The rewards are again normalized within the group, and the Reasoner is updated with a clipped GRPO objective and KL regularization.

#### Why GRPO rather than supervised learning?

At the task level, this is a 10-way candidate-selection problem with a known ground-truth item. That makes Stage 2 fundamentally different from Stage 1. Stage 1 has no gold verbalization, so sequence-level RL provides supervision that is otherwise unavailable. Stage 2 already has a direct target, $y^*$ , so standard supervised fine-tuning could train the model to output the correct candidate.

One possible defense of GRPO is that the Reasoner may generate a free-form reasoning trajectory before its final answer. Outcome-based RL can reward a correct sequence without requiring a labeled rationale and directly optimizes exact-match success. However, the paper does not describe or analyze such reasoning trajectories. §4.2 only says that the predicted item is extracted from generated text.

For the stated task, several simpler alternatives appear natural *(my idea)*:

- Represent the 10 candidates as fixed labels and use cross-entropy SFT on the correct label.
- Score the candidate strings with the causal language model and optimize a listwise softmax loss.
- Constrain decoding so the output must be one of the provided candidates, eliminating malformed or out-of-set generations.

These alternatives would also provide a useful gradient on every labeled example. In contrast, if all $G$ GRPO samples are wrong, they all receive $-1$ and group normalization yields no relative task signal. The same issue occurs when every sample is correct. The paper does not compare Stage 2 GRPO with SFT, constrained decoding, or a conventional candidate-classification objective, so it does not establish that RL is necessary or even preferable here.

## Problem formulation

The end task resembles a ranking problem because the model receives a user history and a candidate set, then must identify the item with which the user will engage next. More precisely, the paper formulates it as top-1 next-item selection rather than learning an explicit pairwise or listwise ranking function.

For user $u$ , the interaction history is

$$
H_u = \{h_1, h_2, \ldots, h_T\},
$$

where each $h_t$ is a structured record containing a timestamp, content identifier, engagement type, and viewing duration. Given candidate set

$$
\mathcal{C} = \{y_1, y_2, \ldots, y_N\},
$$

the task is to select the ground-truth next item $y^*$ .

A template is a deterministic mapping from the structured history to the space of natural-language strings:

$$
\phi_{\text{template}}: H_u \rightarrow \mathcal{X}.
$$

The paper replaces it with a parameterized mapping:

$$
\phi_\theta: H_u \rightarrow \mathcal{X}.
$$

The objective in §3 optimizes the Verbalizer parameters rather than the ranking model parameters:

$$
\max_\theta
\mathbb{E}_{u,\mathcal{C},y^*}
\left[
\mathbf{1}
\left\{
\operatorname{Reasoner}\left(\phi_\theta(H_u), \mathcal{C}\right) = y^*
\right\}
\right].
$$

My initial description of this as a ranker problem is therefore right at the task level but incomplete at the optimization level. The Reasoner performs candidate selection, while the object being learned in this formulation is the textual representation that makes the correct top-1 selection more likely.

## What clicked so far

The most appealing part is that the method does not need a human-written target for the "best" textual representation. The downstream recommendation task supplies the supervision. If removing noise, adding metadata, or restructuring the history helps the recommender predict correctly, that transformation receives a better reward.

My initial guess was that the generated text would simply be a natural-language user profile or an interest summary. The abstract partly supports this intuition because it reports user-interest summarization as an emergent strategy. However, that interpretation is probably too narrow *(inference)*. The paper calls the output an optimized textual context and separately mentions noise removal, metadata incorporation, and information reorganization. The verbalization may therefore preserve parts of the event history, summarize other parts, and rewrite the structure rather than reducing everything to a single profile.

### No direct verbalization labels, but indirect supervision

There is no ground-truth text showing the Verbalizer what an optimal representation should say. In that sense, the content and organization of the generated representation are not directly supervised. Interest summarization, denoising, metadata enrichment, and information reorganization are not mutually exclusive predefined targets. They can all emerge in the same output when they improve the downstream prediction.

However, saying that the model can generate anything without constraint would be too strong. During Verbalizer training, multiple candidate verbalizations are passed to a fixed oracle Reasoner. The oracle's predicted item is compared with the ground-truth item, and correct recommendation provides the task reward. The method also adds a length reward and KL regularization. Therefore, the wording is open-ended, but selection pressure comes from recommendation utility, output length, and proximity to the reference policy.

## Experiments

### §5.1 Task

The experiment is a 10-way reranking task on three months of proprietary Netflix viewing interactions. Each example contains up to 100 recent interactions and 10 candidate items. The model must select the item with which the user actually engaged next. Evaluation uses Recall@1 for discovery items, defined as items the user has not watched before.

### §5.2 Baselines and configurations

The comparison is mainly among different ways to construct the Reasoner's textual input:

| Configuration | How the user context is constructed | Task-specific training |
|---|---|---|
| **Template Baseline** | A fixed template directly concatenates interaction fields. | No learned Verbalizer. |
| **Zero-Shot Verbalizer** | A prompted LLM rewrites interactions using hand-specified heuristics. | No task-specific Verbalizer training. |
| **Action-Based Verbalizer** | The model chooses whether to retain each event and whether to enrich it with metadata. | The restricted-action Verbalizer is trained with GRPO. |
| **Rewrite Verbalizer** | The model produces a complete textual rewrite with room for aggregation and summarization. | The open-ended Verbalizer is trained with GRPO. |
| **Rewrite + Trained Reasoner** | The trained rewrite Verbalizer supplies the context. | Both sequential stages are used: first train the Verbalizer, then train the target Reasoner. |

The first four rows are intended to compare verbalization strategies, while the final row changes an additional variable by training the Reasoner. This makes the headline table easy to read but not fully apples-to-apples. The separate raw-interaction versus verbalized-interaction ablation partly addresses attribution, but the paper still does not include an SFT Reasoner, constrained candidate classifier, or conventional recommender baseline.

## Credibility assessment

The mechanism is plausible. Optimizing an input representation against downstream task performance is a legitimate learning problem, and using a fixed teacher avoids the instability of training the representation generator and its evaluator simultaneously. The second stage also reduces distribution mismatch by adapting the target Reasoner to the learned verbalization style.

The reported ablations provide some encouraging evidence. Training only the rewrite-based Verbalizer improves Recall@1 by 12.5% relative to the template baseline. Training the Reasoner on raw interactions yields a 42.8% relative improvement, while training it on verbalized interactions yields 92.9%. This comparison suggests that the learned representation contributes value beyond Reasoner training alone.

I would nevertheless treat this as a promising prototype rather than a convincingly established result. The paper leaves several pieces needed to judge reliability or reproduce the result unclear:

- It does not identify the oracle or target Reasoner models or disclose their prompts and decoding configurations.
- It reports only relative Recall@1 improvements, not the absolute scores. A 92.9% relative gain can look dramatic when the baseline is small.
- The experiments use one proprietary Netflix dataset. The paper claims broader generalization but provides no public or cross-domain evaluation.
- The PDF does not clearly describe the train, validation, and test split or how the 10-item candidate sets are constructed.
- The binary reward depends on variation within each sampled group, but the paper does not report reward sparsity, collapsed groups, variance across runs, or confidence intervals.
- The fixed oracle can imprint its own biases or reward exploitable wording. The paper asserts transfer to different Reasoner architectures without presenting enough detail to assess that claim.

My verdict is therefore that the central idea is credible, but the headline improvement and claimed generality are not supported transparently enough to be trusted. In particular, I would not use the reported 92.9% relative improvement as reliable evidence without the absolute Recall@1, candidate construction, data splits, and full model configuration.

### Why the paper feels confusing

The confusion does not come from an intrinsically complicated method. It comes from missing definitions at the boundaries between components. The paper introduces a clean two-module abstraction, but it does not clearly identify the oracle and target Reasoners, explain how metadata enters either Verbalizer, disclose the prompts, or fully specify the evaluation pipeline. The notation also presents a generic `Reasoner` before later revealing that the first and second training stages use different Reasoner roles.

At the same time, the paper emphasizes a large relative improvement without reporting absolute Recall@1, candidate construction, standard data splits, or uncertainty across runs. This makes the claims feel more polished than the underlying experimental description. Even the claim of broad generalization is based on a single proprietary streaming dataset.

The draft therefore reads more like an early internal technical report or an unfinished research prototype than a polished peer-reviewed paper. Its arXiv comment, "Work in progress," is consistent with that impression. This does not establish that the authors are inexperienced; proprietary-system constraints or an intentionally early release could produce the same omissions. The fair criticism is about the maturity and completeness of the current manuscript, not the authors' seniority.

## Reader's insights and open questions

- *(open)* What is the actual form of the verbalizer's output? Is it a compact interest profile, a rewritten interaction sequence, or a mixture of both?
- *(open)* The task reward is binary: a candidate receives credit when the oracle Reasoner predicts the correct item. How does learning remain stable when every sampled verbalization for a user receives the same reward?
- *(open)* Verbalizer training uses a fixed, capable closed-source LLM as the oracle Reasoner, after which the Verbalizer is frozen and the target Reasoner is trained. How well do representations rewarded by the oracle transfer to weaker or architecturally different target Reasoners?
- *(open)* What exact models and prompts instantiate the oracle and target Reasoners? The paper describes their roles but does not clearly disclose their identities.
- *(open)* How is the initial Verbalizer policy initialized and prompted, and how often do its first groups of samples produce enough reward variation for GRPO to learn?
- *(open)* Why does Stage 2 use GRPO despite having a gold candidate label? A comparison with SFT, listwise classification, and constrained decoding is needed to justify this choice.
- *(open)* How does the method prevent the verbalizer from inventing unsupported preferences when it adds semantic context or summarizes interests?
- *(open)* Where does item metadata come from, which fields are available to each Verbalizer variant, and how are they retrieved? The dataset description and Table 3 expose different metadata fields.
- *(open)* The reported gain is as high as 93% relative improvement for discovery-item recommendation. What are the absolute numbers, which template baseline is used, and how broadly does the gain hold?

## Net read

The paper asks a useful question and offers a plausible data-centric idea: the natural-language representation of interaction logs should be learned for downstream recommendation rather than fixed by a template. Stage 1 is conceptually defensible because no gold verbalization exists, but Stage 2 uses GRPO for a labeled 10-way selection problem without showing why SFT or constrained classification would not be simpler and stronger.

The work ultimately stands or falls on whether its gains survive a transparent evaluation with disclosed Reasoners, metadata provenance, absolute metrics, candidate construction, and reproducible splits. The current work-in-progress does not provide that evidence. My final take is that the idea is worth remembering, but the reported metrics are not trustworthy enough to support the paper's stronger claims.
