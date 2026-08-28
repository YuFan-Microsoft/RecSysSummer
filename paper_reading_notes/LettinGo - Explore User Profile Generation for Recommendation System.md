# LettinGo: Explore User Profile Generation for Recommendation System

**Authors:** Lu Wang, Di Zhang, Fangkai Yang, Pu Zhao, Jianfeng Liu, Yuefeng Zhan, Hao Sun, Qingwei Lin, Weiwei Deng, Dongmei Zhang, Feng Sun, Qi Zhang

**arXiv:** https://arxiv.org/abs/2506.18309 (v1)

**PDF:** https://arxiv.org/pdf/2506.18309

**Venue:** 11 pages, 3 figures

**Categories:** cs.IR (primary), cs.AI

**Published:** 2025-06-23

---

<!-- Reading progress: the abstract, §1 introduction, and §3.1–§3.3 have been discussed and verified against the PDF. §2 has not been discussed, and §4 onward remains to read. Statements are the paper's unless marked *(inference)*. -->

## Initial read — Abstract

### Why a textual user profile matters

The paper starts from the idea that a user profile is an intermediate representation between raw interaction logs and a downstream recommender. It compresses noisy behavioral data into a concise and structured description of the user's preferences.

The important contrast is between dense user embeddings and natural-language profiles.

| Representation | Main strength | Main limitation |
| --- | --- | --- |
| **Dense user embedding** | It is compact and works naturally with conventional recommendation models. | Its dimensions are difficult for a human to interpret, and the representation is not easy to inspect or edit. |
| **Textual user profile** | It is semantically richer and transparent enough for a person or another model to understand. It can also be adapted to different contexts and downstream requirements. | Its usefulness depends heavily on how the profile is generated and evaluated. A plausible-sounding profile is not necessarily useful for recommendation. |

My initial intuition was to call the second advantage **generalizability**, because a textual profile can potentially be reused across scenarios. The abstract's more precise term, however, is **adaptability**. Cross-scenario generalization is a plausible benefit, but the paper still needs to demonstrate it rather than assume it. *(inference)*

### The key shift: from prompt-only generation to data-driven profile learning

The central motivation is not merely to ask an LLM to summarize a user's history with a better prompt. Existing prompt-based methods usually prescribe a fixed profile format, which may prevent the model from capturing the diversity of real user behavior.

LettinGo instead combines two sources of intelligence:

- LLMs provide an expressive space for exploring diverse textual profiles. The idea that common-sense reasoning and world knowledge help this exploration is plausible, although the abstract itself only refers to the expressive power of LLMs. *(inference)*
- The downstream recommendation task provides a data-driven signal for deciding which candidate profiles are actually useful.

This makes the method better described as **LLM-based profile exploration plus task-driven preference alignment**, rather than simply prompt engineering.

### The three-stage loop

1. **Profile exploration.** Multiple LLMs generate diverse candidate profiles for the same user.
2. **Task-driven evaluation.** Each candidate is evaluated by its effect on downstream recommendation performance.
3. **Preference alignment.** Better and worse candidates are converted into pairwise preference data, and the profile generator is trained with Direct Preference Optimization.

One precision matters here: the paper does not yet claim that the profile generator and recommender are jointly optimized end to end. From the abstract, the downstream system acts as the evaluator that supplies preference labels, and DPO then aligns the profile generator with those labels. Whether any downstream model parameters are updated remains to be checked in the method section. *(open)*

### Reader's insight: richer behavioral context could produce finer profiles

A promising extension would be to move beyond a sequence of interacted items and expose the profile generator to more fine-grained behavioral context. For example, the input could include when an action happened, what the user was doing at that time, the interval between actions, the interaction type, and other contextual or engagement signals. *(my idea)*

This connects directly to the existing TokenMinds reading note. TokenMinds already consumes chronological behavior together with signals such as timestamps, search queries, and likes or dislikes, but it produces SID user tokens and dense embeddings rather than a human-readable profile. A natural follow-up would combine TokenMinds-style fine-grained event inputs with LettinGo-style task-aligned textual profile generation. *(my idea)*

This richer event stream could support a hierarchical profile:

- Stable, long-term preferences would describe what the user generally likes.
- Temporal routines would describe when and under what circumstances those preferences appear.
- Short-term intent would capture what the user is likely trying to do in the current session.

The important research question is whether LettinGo's downstream-feedback mechanism can discover such profile dimensions automatically, or whether the candidate-generation stage is still bounded by the information and profile concepts specified in its prompts. *(open)*

Another question is whether optimizing a profile for one recommendation metric makes it less reusable elsewhere. A profile can be highly effective for one fixed downstream model while failing to be a genuinely general representation of the user. *(open)*

## Introduction — what remains convincing

The most durable motivation is that a user profile performs **selection and compression**. Raw interaction logs are noisy, repetitive, and unevenly informative. A useful profile should extract the few high-value behavioral patterns that matter for understanding or predicting the user, rather than forwarding every event to the downstream model.

Text profiles offer two clear advantages over latent vectors. They expose the model's current interpretation of the user to inspection, and they can express semantic relationships in natural language. These advantages do not prove that text is always a better predictive representation, but they make the representation easier to audit, communicate, and potentially reuse.

The paper's strongest methodological idea follows naturally from this framing. Because it is difficult to define a universally correct profile format, it explores multiple candidate profiles and lets downstream recommendation performance provide the supervision:

1. Generate diverse candidates with multiple LLMs.
2. Combine each candidate with the user's recent history and measure its downstream utility.
3. Turn the resulting scores into preferred and rejected profile pairs.
4. Train the profile generator with DPO.

This is the real transition from a purely prompt-based profile generator to a **prompt-initialized but data-driven learning loop**.

## Introduction — claims that are too broad

### Longer histories do not universally make LLM recommendation worse

Figure 1 shows a non-monotonic curve for one specific setup: a LLaMA 8B model evaluated on Amazon Books, Yelp, and MovieLens. Accuracy initially improves as more textual history is added and then declines. This supports the narrow claim that naively appending more history can hurt in that experimental setup. It does not establish a general law that longer inputs reduce LLM recommendation quality.

The paper's explanation is also tied to an earlier generation of LLM systems. Longer-context models and better context-management methods can substantially reduce truncation and context-length limitations. *(reader's assessment)* The figure therefore ages quickly as evidence for a fundamental limitation.

There is still a valid problem underneath the dated framing. Even when a model can technically accept the full history, additional interactions may be irrelevant, repetitive, contradictory, or weakly connected to the current intent. A larger context window solves **capacity**, but it does not automatically solve **evidence selection**. The robust motivation for profiling is therefore denoising and prioritization, not merely shortening the prompt.

### Dynamic and sequential modeling are not inherent weaknesses of embeddings

The introduction bundles three criticisms together: embedding profiles are difficult to interpret, difficult to update dynamically, and weak at capturing sequential or temporal signals. Only the first is an intrinsic and broadly defensible limitation of a latent vector.

- Dynamic updating depends on how the embedding is produced. [PinnerSage](https://arxiv.org/abs/2007.03634), for example, clusters a user's recent interactions into multiple interest representations and periodically refreshes them as behavior changes. A user embedding does not have to be a permanently stored vector.
- Sequential recommenders compute the current user state from an ordered history. Their hidden representation can encode order, recency, and temporal dependencies when those signals are present in the input and training objective.
- A textual profile is not automatically dynamic either. It must also be regenerated or incrementally updated after new behavior arrives.

The fair comparison is therefore not simply **embedding versus text**.

| Representation design | Interpretability | Dynamic update | Sequential signal |
| --- | --- | --- | --- |
| Static, single user embedding | Low | Usually weak | Usually weak |
| PinnerSage-style multi-interest embeddings | Low to medium, especially when represented by cluster medoids | Supported through refreshed interaction clusters | Captures changing interests, although fine-grained order may still be compressed |
| Sequential-model user state | Low | Naturally recomputed from the latest sequence | Explicitly modeled |
| Natural-language user profile | High | Possible, but requires regeneration or editing | Only preserved if generation receives and retains temporal information |

The paper is thus criticizing a narrow static-embedding baseline while writing as if the criticism applies to embedding-based user modeling in general. The more defensible advantage of textual profiles is **inspectability and semantic explicitness**, not a unique ability to change over time or represent sequences.

## Questions exposed by the Introduction

The paper defines a good profile primarily through downstream recommendation performance. This is operationally convenient, but it creates a potential conflict with the interpretability motivation. A profile could improve recommendation by encoding a task-specific shortcut while being incomplete, misleading, or unfaithful as a human-readable explanation. *(open)*

The claim that DPO "lets go" of rigid profile formats also needs scrutiny. Preference optimization can avoid cloning one supervised target, but its learned distribution is still bounded by the prompts, candidate-generating LLMs, and profile pool used to construct the preference pairs. The method section needs to show how much genuine format exploration remains after these choices. *(open)*

## Method §3.1 — separate long-term memory from recent intent

The design in §3.1 is more interesting than a simple summary-then-recommend pipeline. The authors split one chronological interaction history into two non-overlapping temporal segments. Smaller indices denote more recent actions.

The most recent $K$ interactions remain as raw recent history:

$$
h_u = [h_{u,1}, h_{u,2}, \ldots, h_{u,K}].
$$

The older $L-K$ interactions form the long history:

$$
H_u = [h_{u,K+1}, h_{u,K+2}, \ldots, h_{u,L}].
$$

Only the older segment is passed to the profile generator:

$$
p_u = f_{\mathrm{LLM}}(H_u).
$$

The resulting profile is then combined with the untouched recent history and a candidate item $t$. These components are serialized into a natural-language prompt for the downstream recommendation system:

$$
\hat{y}_u = f_{\mathrm{Rec}}(p_u, h_u, t).
$$

The output $\hat{y}_u$ is the predicted relevance score for that candidate item.

### A two-timescale user representation

The cleanest interpretation is that LettinGo assigns different jobs to the two temporal segments:

- The generated profile acts as **compressed long-term memory**, extracting relatively stable preferences from older behavior.
- The raw recent history preserves **short-term intent**, including preference shifts that may be lost in a summary.
- The candidate item makes the final scoring operation target-conditioned, while the profile itself remains target-independent and can therefore be reused across candidates.

The paper does not explicitly describe this as a long-term versus short-term decomposition, but the formulation strongly implies it. *(inference)*

This design also gives a better justification for profiling than the Introduction's outdated context-length argument. The framework does not discard the long history because it is too long. Instead, it compresses older evidence while keeping the most decision-relevant recent evidence at full resolution.

### What the downstream score actually evaluates

Every candidate profile for a user is evaluated while the recent history and target-item input are also present. The score therefore does not measure the profile's intrinsic quality in isolation. It measures the profile's **incremental utility beyond the same recent raw signals**.

This controlled interface is useful for comparing candidate profiles, because the profile is the component that changes. It also raises several questions:

- If recent behavior already predicts the target well, the downstream score may provide little signal for distinguishing profiles. *(open)*
- If the user's interests have recently shifted, an older-history profile may be stale or even conflict with the raw recent history. The paper still calls the profile dynamic, but it can only become dynamic through regeneration and movement of the temporal boundary. *(open)*
- A profile selected for improving one scorer's output may learn scorer-specific shortcuts rather than a generally faithful account of the user. *(open)*

The central architectural bet is therefore not simply that a textual profile is useful. It is that **compressed older behavior and uncompressed recent behavior are complementary**, and that downstream performance can identify which compression preserves the right information.

### Reader's connection — the same pattern as agent memory compaction

This architecture closely resembles the memory hierarchy used by many LLM agents. Recent interactions remain verbatim as high-resolution working memory, while older interactions are compressed into a smaller long-term representation. In both settings, the design accepts that recent events usually have the strongest immediate predictive value, whereas older events are more useful for supplying stable background knowledge.

A Bayesian interpretation makes the roles especially clear. The long-term profile behaves like a prior over the user's stable preferences, and the recent raw history provides fresh evidence that updates or overrides that prior for the current prediction. *(inference)*

The analogy is strong but not exact:

| Recommendation in LettinGo | Memory in an LLM agent |
| --- | --- |
| Older behavior is compressed into a user profile. | Older conversation or experience is summarized into long-term memory. |
| Recent behavior is kept at full resolution for next-item prediction. | Recent turns remain verbatim in the working context. |
| Profile quality is optimized through downstream recommendation outcomes. | Memory quality is usually judged by task completion, factual continuity, or instruction adherence. |
| One global profile summarizes the old history. | Stronger agent systems may retain episodic memories and retrieve only those relevant to the current task. |

The last difference suggests a stronger recommendation design. Instead of forcing all old behavior into one profile, the system could maintain a multi-resolution memory:

1. A stable long-term profile would store persistent preferences.
2. A medium-term memory would retain emerging interests and recent preference shifts.
3. A short verbatim window would preserve the latest actions and their exact order.
4. The current recent history or candidate item would retrieve relevant episodes from older history rather than relying only on a global summary. *(my idea)*

A learned gate could then decide how much to trust each level. This matters because the assumption that the next click is dominated by recent behavior is often reasonable, but it is domain- and user-dependent. A short-lived shopping mission may be highly session-driven, whereas music, books, or specialized hobbies may depend much more on stable long-term taste.

The shared failure mode with agent memory is **lossy compaction**. A summary can erase rare but important preferences, hide uncertainty, reinforce outdated beliefs, or gradually drift away from the underlying events. A useful profile should therefore preserve provenance, recency, and confidence, or retain access to the original episodes when the compressed memory is insufficient. *(my idea)*

## Method §3.2.1 — diversity through model and sampling exploration

The exploration stage uses a deliberately broad prompt. It provides a sequence of item attributes and observed sentiments, then asks the profiler to produce any information that could help predict the user's sentiment toward a new item. The intended diversity comes from two sources:

- **Model diversity.** The implementation names LLaMA3 8B Instruct, LLaMA2 Chat, GPT-4o-mini, and Claude as profile generators.
- **Sampling diversity.** Each profiler is sampled repeatedly with temperature set to 1.0, whereas the downstream recommendation model uses temperature 0 for deterministic evaluation.

The paper contains two reproducibility inconsistencies.

First, §3.2.1 and Algorithm 1 say that **each** profiling model generates $N=10$ profiles per user. With four profilers, the natural reading is 40 candidate profiles per user. However, §4.1.1 says, "For each user, we generate 10 profiles," which implies ten in total. The paper never resolves whether the experimental dataset contains ten or forty candidates per user. *(open)*

Second, §4.1.4 calls the second open-source profiler "LLaMA2 14B Chat," while Table 2 calls it "LLaMA2 13B." LLaMA2's standard released size is 13B, so "14B" is likely a paper typo, but the implementation is not documented precisely enough to prove this. *(inference)*

The temporal split also needs one refinement. The general formulation uses all interactions outside the recent window as long history, but the experiments explicitly control the profile-generation input to 30, 50, or 70 older interactions. The practical recipe is therefore **ten recent raw interactions plus a bounded older-history window for profile generation**, not necessarily every event preceding the latest ten.

### What kind of diversity is actually explored?

Using several model families and a high temperature should produce lexical, structural, and stylistic variation. It does not guarantee meaningful semantic diversity. Multiple candidates may express the same broad preferences with different wording, while rare interests or alternative interpretations remain unexplored. The case studies later in the paper need to show whether the candidate pool differs in information content rather than surface form. *(open)*

## Method §3.2.2 — downstream correctness as indirect supervision

There is no gold-standard textual profile for a user. LettinGo replaces unavailable profile labels with an outcome-based signal from a downstream task.

For each candidate profile, the downstream LLaMA3 8B Instruct model receives:

1. The user's ten most recent raw interactions.
2. One candidate profile generated from older history.
3. A target item.

It must output exactly one label: `like`, `neutral`, or `dislike`. A profile is placed in the positive set if the model predicts the ground-truth label correctly and in the negative set otherwise. Algorithm 1 then forms every possible positive-negative profile pair for that user.

The reader's summary captures the central move precisely: downstream behavior supplies an **indirect signal** for profile quality when direct supervision does not exist. The profile generator can therefore be trained from recommendation outcomes without requiring humans to write an ideal profile for every user.

### The signal is useful, but much coarser than the paper suggests

The evaluator does not assign a graded profile-quality score. It produces a three-way sentiment prediction, which is then reduced to a binary label:

- Every profile associated with a correct prediction is treated as preferred.
- Every profile associated with an incorrect prediction is treated as dispreferred.

This means that a profile's label contains noise from both the profile and the downstream predictor. A broadly faithful profile can be marked negative because the predictor fails on one target, while an incomplete or misleading profile can be marked positive because the predictor happens to guess correctly.

The learned notion of "good" is also evaluator-specific. A profile is good if it helps this particular downstream model, prompt, target distribution, and metric. It is not automatically a faithful or model-independent representation of the user.

Several design consequences follow:

- Users for whom all candidate profiles succeed or all fail produce no positive-negative pair and are omitted from DPO training. This concentrates training on cases where profile choice changes the evaluator's outcome, but it also creates selection bias.
- Forming every positive-negative combination can create many nominal pairs from one underlying user-target judgment. These pairs are correlated rather than independent pieces of evidence.
- Evaluating each profile on multiple target items, multiple downstream models, or several recommendation objectives would estimate its expected utility more reliably than one binary success event. *(my idea)*
- A separate faithfulness criterion could check whether the profile is supported by the user's history, preventing task-effective but ungrounded profiles from being rewarded. *(my idea)*

The attractive idea is therefore not that downstream correctness gives a perfect definition of profile quality. It is that it provides a cheap, scalable **weak supervision signal** that can bootstrap preference learning when no gold profile dataset exists.

## Method §3.2.3 — preference learning, with a questionable DPO equation

Most of §3.2.3 repeats the motivation already established in the Introduction and §3.2.2:

- There is no unique ground-truth profile.
- Downstream correctness supplies weak preference labels.
- Free-text generation is intended to avoid one manually prescribed profile format.
- The positive profile should receive a higher conditional score than the negative profile.

The training tuple contains the older interaction history and one preferred-dispreferred profile pair:

$$
(H_u, p_u^+, p_u^-).
$$

Conceptually, DPO is a natural choice for this setting because the supervision is relative. The data says which of two profiles is more useful, without pretending that either profile is the one uniquely correct textual answer.

However, the claim that DPO preserves an unconstrained profile format is overstated. The generator is still constrained by the initial prompt, the candidate models, their sampled outputs, the tokenizer, and the preference distribution. DPO removes the need to imitate one fixed target, but it cannot learn profile concepts or formats that never appear in the exploration pool.

### The equation shown in the paper is not standard DPO

Equation 3 is written as:

$$
\mathcal{L}_{\mathrm{paper}} = -\mathbb{E}_{(H_u,p_u^+,p_u^-)}\left[\log \sigma\left(f_{\mathrm{LLM}}(p_u^+ \mid H_u) - f_{\mathrm{LLM}}(p_u^- \mid H_u)\right)\right].
$$

Read literally, this is a pairwise logistic or Bradley-Terry ranking loss over two model scores. It only asks the preferred profile to score above the dispreferred profile.

Standard DPO instead compares how much the trainable policy's relative preference differs from that of a frozen reference policy:

$$
\mathcal{L}_{\mathrm{DPO}} = -\mathbb{E}\left[\log \sigma\left(\beta\left[\log \frac{\pi_\theta(p_u^+ \mid H_u)}{\pi_{\mathrm{ref}}(p_u^+ \mid H_u)} - \log \frac{\pi_\theta(p_u^- \mid H_u)}{\pi_{\mathrm{ref}}(p_u^- \mid H_u)}\right]\right)\right].
$$

The paper's equation omits both the frozen reference model and the scaling coefficient $\beta$. It also never defines whether $f_{\mathrm{LLM}}(p \mid H_u)$ means a probability, a sequence log-probability, a length-normalized score, or something else.

This matters because the preferred and dispreferred profiles are free-text sequences with potentially different lengths. Comparing raw sequence probabilities would introduce a strong length effect, usually favoring shorter completions. The paper states that training uses LLaMA-Factory, so the actual code may use a standard DPO implementation and Equation 3 may only be an incorrect simplification. Without the configuration or released implementation, this cannot be resolved. *(open)*

The clean conceptual summary remains the reader's version: use downstream weak supervision to construct positive and negative profiles, then train the generator to assign greater relative probability to the positive one. The mathematical and implementation details are much less solid than that high-level idea.

## Method §3.3 — the Cartesian product written as an algorithm

Section 3.3 adds almost no conceptual information. For each user, the pipeline repeatedly samples profiles from every profiler, evaluates each profile with the downstream predictor, and partitions the candidates into a positive set and a negative set. If both sets are non-empty, it retains every possible positive-negative combination:

$$
\mathcal{D}_u = \left\{(H_u, p_u^+, p_u^-, y_u) \mid p_u^+ \in \mathcal{P}_u^+, \; p_u^- \in \mathcal{P}_u^-\right\}.
$$

The ground-truth sentiment label $y_u$ is needed to decide whether the evaluator was correct, but it is not used directly in the DPO objective once the preferred and dispreferred profiles have been assigned.

### The all-pairs construction creates an implicit weighting scheme

If a user has $a$ positive profiles and $b$ negative profiles, that user contributes $ab$ training pairs. With $n=a+b$ candidates, the count is largest when the evaluator splits the candidates almost evenly:

$$
\max ab = \left\lfloor\frac{n^2}{4}\right\rfloor.
$$

This gives at most 400 pairs if the intended candidate count is 40, but only 25 if the actual count is ten. The unresolved ten-versus-forty inconsistency therefore changes not only sampling cost but also the possible DPO dataset size by a factor of sixteen.

More importantly, users for whom the evaluator is most inconsistent across candidate profiles receive the largest training weight. Users with all-correct or all-incorrect outcomes contribute nothing. This may deliberately focus learning on cases where the profile affects the answer, but the paper neither discusses nor controls this weighting.

All pairs from one user are also highly correlated because they come from the same history, target, label, and evaluator call structure. Counting them as separate rows enlarges the dataset without creating equally many independent supervision signals.

A cleaner construction could cap or sample a balanced number of pairs per user, include a confidence or margin from the evaluator, and evaluate profiles across several target items before assigning preference labels. *(my idea)*

One notation inconsistency remains: Algorithm 1 writes the predictor as $f_{\mathrm{Rec}}(p,H_u)$, while §3.1 defines it using the profile, recent history, and target item as $f_{\mathrm{Rec}}(p_u,h_u,t)$. The algorithm appears to suppress important inputs rather than introduce a genuinely different evaluator. *(inference)*

<!-- To be continued: continue with §4 after the reader shares their understanding. -->
