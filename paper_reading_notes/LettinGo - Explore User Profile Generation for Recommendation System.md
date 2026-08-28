# LettinGo: Explore User Profile Generation for Recommendation System

**Authors:** Lu Wang, Di Zhang, Fangkai Yang, Pu Zhao, Jianfeng Liu, Yuefeng Zhan, Hao Sun, Qingwei Lin, Weiwei Deng, Dongmei Zhang, Feng Sun, Qi Zhang

**arXiv:** https://arxiv.org/abs/2506.18309 (v1)

**PDF:** https://arxiv.org/pdf/2506.18309

**Venue:** 11 pages, 3 figures

**Categories:** cs.IR (primary), cs.AI

**Published:** 2025-06-23

---

<!-- Reading progress: complete for the abstract, §1, §3–§5, verified against the PDF. §2 related work was intentionally skipped in the discussion. Statements are the paper's unless marked *(inference)*. -->

## TL;DR

LettinGo treats a textual user profile as compact long-term memory while preserving the ten most recent interactions as high-resolution short-term evidence. Because no gold profile exists, it samples diverse candidates, labels them through a downstream sentiment-classification task, and uses the resulting positive-negative pairs to train the profile generator with preference optimization.

The core idea is genuinely useful: evaluate a representation by whether it helps the task it is built for. The paper stands or falls on whether this weak supervision learns a faithful, reusable user profile or merely a textual prompt optimized for one particular LLM evaluator.

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

First, §3.2.1 and Algorithm 1 say that **each** profiling model generates $N=10$ profiles per user. With four profilers, the natural reading is 40 candidate profiles per user. However, §4.1.1 says, "For each user, we generate 10 profiles," which implies ten in total. Table 1 later reports only about four to five DPO pairs per sampled training user on average, which is much more consistent with ten total candidates than with forty. The actual experiment therefore most likely used ten profiles in total, but the method description remains contradictory. *(inference)*

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
\mathcal{L}_{\mathrm{paper}} = -\mathbb{E}_{(H_u,p_u^+,p_u^-)} [\log \sigma(f_{\mathrm{LLM}}(p_u^+ \mid H_u) - f_{\mathrm{LLM}}(p_u^- \mid H_u))].
$$

Read literally, this is a pairwise logistic or Bradley-Terry ranking loss over two model scores. It only asks the preferred profile to score above the dispreferred profile.

Standard DPO instead compares how much the trainable policy's relative preference differs from that of a frozen reference policy:

$$
\mathcal{L}_{\mathrm{DPO}} = -\mathbb{E}[\log \sigma(\beta[\log \frac{\pi_\theta(p_u^+ \mid H_u)}{\pi_{\mathrm{ref}}(p_u^+ \mid H_u)} - \log \frac{\pi_\theta(p_u^- \mid H_u)}{\pi_{\mathrm{ref}}(p_u^- \mid H_u)}])].
$$

The paper's equation omits both the frozen reference model and the scaling coefficient $\beta$. It also never defines whether $f_{\mathrm{LLM}}(p \mid H_u)$ means a probability, a sequence log-probability, a length-normalized score, or something else.

This matters because the preferred and dispreferred profiles are free-text sequences with potentially different lengths. Comparing raw sequence probabilities would introduce a strong length effect, usually favoring shorter completions. The paper states that training uses LLaMA-Factory, so the actual code may use a standard DPO implementation and Equation 3 may only be an incorrect simplification. Without the configuration or released implementation, this cannot be resolved. *(open)*

The clean conceptual summary remains the reader's version: use downstream weak supervision to construct positive and negative profiles, then train the generator to assign greater relative probability to the positive one. The mathematical and implementation details are much less solid than that high-level idea.

## Method §3.3 — the Cartesian product written as an algorithm

Section 3.3 adds almost no conceptual information. For each user, the pipeline repeatedly samples profiles from every profiler, evaluates each profile with the downstream predictor, and partitions the candidates into a positive set and a negative set. If both sets are non-empty, it retains every possible positive-negative combination:

$$
\mathcal{D}_u = \{(H_u, p_u^+, p_u^-, y_u) \mid p_u^+ \in \mathcal{P}_u^+, \; p_u^- \in \mathcal{P}_u^-\}.
$$

The ground-truth sentiment label $y_u$ is needed to decide whether the evaluator was correct, but it is not used directly in the DPO objective once the preferred and dispreferred profiles have been assigned.

### The all-pairs construction creates an implicit weighting scheme

If a user has $a$ positive profiles and $b$ negative profiles, that user contributes $ab$ training pairs. With $n=a+b$ candidates, the count is largest when the evaluator splits the candidates almost evenly:

$$
\max ab = \lfloor \frac{n^2}{4} \rfloor.
$$

This gives at most 400 pairs if the method's implied candidate count is 40, but only 25 if the experimental count is ten. Table 1 strongly suggests that the latter was used, although the paper never explicitly reconciles the two descriptions.

More importantly, users for whom the evaluator is most inconsistent across candidate profiles receive the largest training weight. Users with all-correct or all-incorrect outcomes contribute nothing. This may deliberately focus learning on cases where the profile affects the answer, but the paper neither discusses nor controls this weighting.

All pairs from one user are also highly correlated because they come from the same history, target, label, and evaluator call structure. Counting them as separate rows enlarges the dataset without creating equally many independent supervision signals.

A cleaner construction could cap or sample a balanced number of pairs per user, include a confidence or margin from the evaluator, and evaluate profiles across several target items before assigning preference labels. *(my idea)*

One notation inconsistency remains: Algorithm 1 writes the predictor as $f_{\mathrm{Rec}}(p,H_u)$, while §3.1 defines it using the profile, recent history, and target item as $f_{\mathrm{Rec}}(p_u,h_u,t)$. The algorithm appears to suppress important inputs rather than introduce a genuinely different evaluator. *(inference)*

## Experiments §4.1.1 — how the train and test users are constructed

The experiment uses MovieLens-10M, Amazon Books, and Yelp. Each dataset is first restricted to users with more than 70 historical interactions, ensuring that every selected user has enough behavior to support the recent-history window, the profile-history window, and a held-out target.

The split is user-level and computationally small:

1. **Test users.** The authors sample 2,000 eligible users. For each user, the last interacted item is held out as the target item, giving one temporally held-out test instance per user.
2. **Training users.** From the remaining eligible users, the authors sample only 3,000 users per dataset for profile-generation and DPO data collection.
3. **History-length groups.** The 3,000 training users are divided into three disjoint groups of 1,000. Their profile-generation inputs contain 30, 50, or 70 historical interactions, respectively.

The purpose of the three groups is to expose the profile generator to different input lengths. A training user belongs to one length group rather than contributing examples at all three lengths.

The notation in the results, such as `10H+30P`, means that the downstream predictor receives ten recent raw interactions plus a profile generated from 30 older interactions. The formulation in §3.1 implies that these two windows should be non-overlapping. However, §4.3.2 later calls the profile inputs the "most recent" 30, 50, or 70 interactions, so the experimental description is less precise than the method about the exact window boundary. *(open)*

### Table 1's `#train` column is not a user count

The reported training counts are:

| Dataset | Sampled training users | DPO training rows in Table 1 | Average rows per sampled user | Test users |
| --- | ---: | ---: | ---: | ---: |
| MovieLens-10M | 3,000 | 15,637 | 5.21 | 2,000 |
| Amazon Books | 3,000 | 13,212 | 4.40 | 2,000 |
| Yelp | 3,000 | 14,427 | 4.81 | 2,000 |

The `#train` values must refer to constructed positive-negative preference rows rather than distinct users. They are produced by expanding the 3,000 sampled users through the all-pairs procedure in Algorithm 1. This makes the nominal training set appear larger, but the number of independent user histories remains only 3,000 per dataset.

These counts also provide indirect evidence about the earlier sampling ambiguity. If every user really had 40 candidate profiles, the all-pairs procedure could generate as many as 400 rows per user. An observed average of roughly five rows is much more plausible when only ten candidate profiles are generated in total, whose per-user maximum is 25. *(inference)*

### What the temporal test target does and does not establish

Holding out the final interaction is a sensible temporal evaluation choice. The model predicts a future observation from earlier behavior rather than reconstructing an item already included in the input.

However, each test user contributes only one target item. The evaluation therefore has 2,000 user-target decisions per dataset, and profile quality is measured against one future outcome per user. This is a narrow estimate of whether a profile captures the user's broader preferences. The paper also does not clearly document how raw ratings are mapped into the three sentiment labels `like`, `neutral`, and `dislike`. *(open)*

## Experiments §4.1.2 — sentiment classification, not item ranking

The reader's reconstruction is correct. The downstream evaluator is an instruction-tuned LLM, specifically LLaMA3 8B Instruct in the main experiments. For each test user, the prompt contains:

1. The ten recent interactions, including item attributes and the user's sentiment toward each item.
2. A generated long-term user profile.
3. The metadata of one candidate item, which is the user's held-out final interaction.

The model must output exactly one class: `like`, `neutral`, or `dislike`. That prediction is compared with the held-out interaction's ground-truth sentiment label. Accuracy and an F1 score are then aggregated across the 2,000 test users in each dataset.

### The missing rating-to-sentiment mapping

MovieLens, Amazon Books, and Yelp provide numerical ratings, so those ratings must be discretized before they can become the three textual classes. LettinGo never states the thresholds.

A natural guess would map low ratings to `dislike`, the middle rating to `neutral`, and high ratings to `like`, but this is not verified. MovieLens also contains half-star ratings, making the omitted boundary choices consequential. *(inference)*

The cited Kang et al. rating-prediction paper does not resolve the issue. It treats ratings from one to five as five separate classes rather than defining LettinGo's three-way sentiment mapping. This is therefore a genuine reproducibility omission.

### This is not conventional recommendation evaluation

Although the paper repeatedly calls the reported number recommendation accuracy, the experiment does not rank items or predict which item the user will select next.

- Each user has only one provided target item.
- The target is an item the user actually interacted with, not one item among a candidate set.
- There are no sampled or full-catalog negative items.
- The paper reports no Recall, NDCG, Hit Rate, or ranking AUC.
- The prediction target is the user's sentiment toward the given item, not the identity of the next item.

The task is therefore more precisely described as **zero-shot user rating or sentiment classification conditioned on a profile**. It tests whether the profile helps an LLM infer preference for a known candidate. It does not establish that the profile improves retrieval or ranking in a deployed recommendation pipeline.

This distinction also changes how to interpret the long-term profile. The profile may help predict whether the user likes a supplied book, movie, or business, but that is weaker than demonstrating that it can find the right item from a large catalog.

### The F1 definition is internally inconsistent

The evaluation paragraph says it reports **weighted F1**, which weights each class by its frequency. The next sentence says it uses **macro averaging so that each class contributes equally**. These are different metrics, and Table 2 labels the column only as `F1`.

The reported values therefore cannot be identified as weighted or macro F1 from the paper. This is another implementation detail that would need code or author clarification. *(open)*

## Experiments §4.1.3 — what each baseline is meant to isolate

The reader's three-level organization captures the intended comparison:

| Baseline family | Information given to the predictor | Intended control |
| --- | --- | --- |
| **10H** | Only the ten recent raw interactions and the target item | Whether any long-term information is useful |
| **KAR** | The same amount of long-history information is used without LettinGo's learned profile generator | Whether compression into a learned profile is better than directly exposing longer history |
| **RLMRec / PALR** | A prompted profile generated from older behavior, combined with the same recent raw history and target | Whether DPO-aligned profile generation improves over fixed prompt-based profile generation |
| **LettinGo** | A DPO-trained profile, recent raw history, and target | The full proposed method |

RLMRec and PALR are the cleanest prompt baselines. The paper says that all other components are held constant and only their profile-generation prompts differ:

- **PALR** requests a rigid, importance-ordered keyword list that links each keyword to supporting historical businesses.
- **RLMRec** requests a JSON object with a preference summary and a separate reasoning field, with the summary limited to 100 words.

Their comparison with LettinGo is therefore intended to isolate **fixed prompted format versus task-aligned preference training**, while preserving the downstream evaluator and the recent-history interface.

### The KAR baseline is described inconsistently

The main text says KAR "directly utilizes the same number of interaction records for prediction," which suggests a raw long-history control rather than profile generation. Under that reading, KAR is approximately a recent-history-plus-long-raw-history baseline.

However, Appendix A provides a `KAR Prompt` that asks the LLM to analyze the user's preferences and provide explanations from the reviewing history. That output is itself profile-like. The paper does not show the complete final prediction prompt or explain how this intermediate analysis is inserted into the evaluator.

It is therefore unclear whether KAR truly represents **raw long history without a profile**, or merely a third zero-shot profile prompt. This ambiguity matters because Table 2 contains no separately named `10H+30H` row that would unambiguously test raw long history against `10H+30P`. *(open)*

### What the baseline comparison can attribute

The strongest comparison is not simply "profile versus no profile." It is:

1. Recent behavior alone.
2. Additional long-term information in an ambiguously documented KAR form.
3. Long-term information compressed by fixed, zero-shot profile prompts.
4. Long-term information compressed by a generator trained on downstream-derived preference pairs.

Consequently, LettinGo's gain over RLMRec and PALR mixes at least two effects: learning from 3,000 in-domain users and replacing their prescribed formats with preference alignment. The experiment does not compare DPO against an equally trained SFT profile generator under the same target format until the later ablation, so Table 2 alone cannot attribute the gain specifically to format freedom. *(open)*

## Experiments §4.1.4 — implementation details

There is little additional modeling content in this section. Profile exploration uses temperature 1.0 to increase sampling diversity, while recommendation prediction uses temperature 0 so that the evaluator produces a deterministic answer for a fixed prompt.

The main downstream predictor is LLaMA3 8B Instruct. Candidate profiles are generated with LLaMA3 8B Instruct, the inconsistently named LLaMA2 13B or 14B Chat model, GPT-4o-mini, and Claude. Fine-tuning is implemented with LLaMA-Factory.

The main reproducibility gap is that the authors say batch size, learning rate, and other key hyperparameters are selected by grid search but never report either the search space or the final values. The paper also omits the DPO reference model and preference coefficient. As a result, the profile-sampling temperatures are documented more clearly than the actual training configuration.

## Results §4.2.1 — the complete pipeline wins, but RQ1 does not isolate why

The main table shows that LettinGo produces the strongest sentiment-classification results across the three datasets. For the LLaMA3 8B profile-generator setting, the clearest comparison in accuracy is:

| Dataset | Recent-only `10H` | Strongest reported baseline | Best LettinGo result |
| --- | ---: | ---: | ---: |
| MovieLens-10M | 44.95 | 51.00 | 53.00 |
| Yelp | 37.45 | 67.90 | 70.70 |
| Amazon Books | 48.15 | 67.40 | 70.75 |

Relative to the weak recent-only baseline, the absolute gains are 8.05, 33.25, and 22.60 percentage points. Relative to the strongest reported baseline in each dataset, however, the gains are only 2.00, 2.80, and 3.35 points.

The headline claim of roughly 20 percentage points therefore mainly demonstrates that adding long-term information is valuable, especially on Yelp and Amazon. The incremental evidence that LettinGo's learned profile generator is better than the strongest competing treatment of long-term information is positive but much smaller.

### The author's explanation versus what the table establishes

The reader accurately reconstructed the causal story proposed by the authors:

- The profile can use flexible free text rather than one prescribed format.
- An LLM can express semantic knowledge that is difficult to encode in a latent vector.
- Downstream-derived weak supervision aligns profile generation with the evaluation task.
- The ten raw recent interactions preserve short-term intent, while the generated profile compresses long-term preference information.

This is a coherent explanation of why the method could work. RQ1 does not separately prove any of these mechanisms.

- All profile baselines use LLMs, so the gain cannot be attributed simply to LLM world knowledge.
- RLMRec and PALR also combine a long-term profile with recent interactions, so long-short-term balancing is not unique to LettinGo.
- Keeping the recent interactions verbatim avoids explicit compression loss at the input level, but it does not prove that the downstream LLM attends to them without dilution.
- Format freedom and in-domain preference training are changed together, so their effects remain confounded.
- Task alignment receives a more direct test only in the later DPO ablation.

The strongest conclusion from RQ1 is therefore narrow: **the complete LettinGo pipeline yields better held-out sentiment classification than the implemented baselines**. It does not yet explain which design choice deserves the credit, and it still does not evaluate item retrieval or ranking.

### Internal reporting inconsistencies

The prose says the Amazon result is 66.30 accuracy and 69.04 F1, but those values do not appear in Table 2. The best LLaMA3 Amazon entries in the table are 70.75 accuracy and 71.79 F1, attained by different profile-history lengths.

The authors also claim that the relative improvement is largest on MovieLens. This is not supported by the displayed accuracy gains: the improvement over `10H` is much larger on Yelp and Amazon, while the gain over the strongest baseline is also not uniquely largest on MovieLens.

Finally, the paper attributes the result partly to "carefully designed prompt templates," even though its main methodological claim is that LettinGo avoids fixed profile formats through a simple general-purpose prompt. This wording further blurs whether the proposed advantage comes from prompt design, diverse sampling, or DPO alignment.

## Ablation §4.3.1 — DPO versus SFT versus prompt-only generation

Table 3 reports a clean ordering on all three datasets:

| Dataset | Without DPO | SFT | With DPO |
| --- | ---: | ---: | ---: |
| MovieLens-10M | 50.9 | 51.1 | 53.0 |
| Yelp | 64.9 | 66.2 | 70.4 |
| Amazon Books | 59.1 | 63.7 | 70.4 |

The reader's interpretation is correct: prompt-only generation is weakest, SFT helps, and preference optimization gives the best downstream classification accuracy.

This is the most direct evidence in the paper that task-derived pairwise supervision improves the profile generator. It supports the claim that simply instructing an LLM to write a plausible profile is weaker than training the generator on which profiles actually help the downstream evaluator.

Several details remain unclear:

- The paper does not define precisely what `Without DPO` means. It is most naturally read as the original instruction-tuned generator used without profile-alignment training. *(inference)*
- It never explains which profiles serve as SFT targets. The likely construction is to imitate profiles labeled positive by the evaluator, but this is not stated. *(inference)*
- Consequently, the comparison does not reveal whether DPO wins because pairwise learning is intrinsically better or because the SFT data selection, target multiplicity, and training configuration are weaker.

There is also a numerical error in the prose. The paper says DPO improves MovieLens accuracy by 2.1 points over SFT, but Table 3 gives 53.0 versus 51.1, which is a 1.9-point gain. The 2.1-point number is the difference between DPO and `Without DPO`, which is 50.9.

The Yelp and Amazon statements do match the table: DPO improves over SFT by 4.2 and 6.7 points, respectively. The growing gain suggests that pairwise task alignment matters more in those datasets, but the paper does not investigate why.

## Ablation §4.3.2 — profile history length has no universal optimum

RQ3 compares profiles generated from 30, 50, and 70 historical interactions while retaining the same ten recent raw interactions for prediction.

For the LLaMA3 setting:

| Dataset | Best accuracy length | Best F1 length | Shape of the result |
| --- | ---: | ---: | --- |
| MovieLens-10M | 70 | 70 | Longer profiles help modestly. |
| Yelp | 30 | 50 | Results are nearly flat, with no consistent winner. |
| Amazon Books | 50 | 30 | Accuracy and F1 prefer different lengths. |

The LLaMA2-profile setting shows the same broad pattern: MovieLens favors 70, Yelp favors 30, and Amazon generally favors 50. There is no monotonic rule that more history creates a better profile.

The paper proposes three explanations: dataset sparsity, preference drift, and the model's ability to handle noise. These are plausible post-hoc explanations, not mechanisms isolated by the experiment.

The observed differences are also small for several dataset-metric combinations. For example, LLaMA3 Yelp accuracy changes only from 70.70 to 70.40 across the entire 30-to-70 range, and Amazon accuracy remains between 70.40 and 70.75. The evidence supports **robustness to several history lengths** more strongly than it supports a sharply defined dataset-specific optimum.

The authors conclude that history length should be adapted dynamically, but LettinGo does not learn such an adaptive policy. It evaluates three fixed global choices. A stronger design would select or retrieve older interactions per user and current context, rather than deciding profile length solely at the dataset level. *(my idea)*

This result reinforces the earlier memory interpretation. The useful question is not how many old events can fit into the profile prompt, but which old events provide complementary evidence beyond the recent raw window.

## Case study §4.4 — useful illustrations, not strong evidence

The case study makes three qualitative points.

First, the generated profile is shorter than directly including 30 historical interactions, supporting the compaction interpretation. This is a real systems benefit, although the paper does not connect token savings to measured latency or cost.

Second, Figure 5 shows one MovieLens user for whom the ten recent interactions lead to a wrong prediction, while adding the long-term profile produces the correct label for *Toy Story 2*. The profile recovers recurring preferences for adventure, fantasy, science fiction, and light comedy that are not fully visible in the short window.

Third, the generated formats differ across datasets. MovieLens profiles are narrative, Yelp profiles use structured headings and bullet points, and Amazon profiles mix narrative and categorical descriptions. The authors interpret this as automatic domain-specific format adaptation.

These examples are plausible demonstrations, but they do not establish interpretability or faithfulness. A single success case can be selected after observing the prediction, and no human study checks whether the profile is accurate, complete, understandable, or supported by the history. Differences in surface format could also arise from domain vocabulary and random sampling rather than a learned adaptation strategy.

The MovieLens example itself contains broad statements such as an appreciation for "memorable quotes" that are not clearly grounded in the displayed interactions. This illustrates the central unresolved tension: a profile can be useful for prediction while still containing unsupported narrative details.

## Transfer and GPT-4o comparison §4.5

On MovieLens, the paper compares a LettinGo profile generator trained with downstream-derived preferences against zero-shot profiles generated by GPT-4o. Both are evaluated by a LLaMA3 8B Instruct predictor:

| Profile generator | Accuracy | F1 |
| --- | ---: | ---: |
| GPT-4o | 52.80 | 51.30 |
| LettinGo DPO with `10H+70P` | 53.00 | 51.69 |

The reader's causal interpretation is reasonable. GPT-4o relies mainly on its pretrained world knowledge and common-sense reasoning, whereas LettinGo receives direct in-domain feedback about which profiles help the downstream task. This is a useful illustration that task alignment can compensate for a large difference in base-model capability.

The numerical evidence is weak, however. An accuracy difference of 0.20 percentage points over 2,000 test users corresponds to only four additional correct predictions. The paper reports no variance, repeated runs, confidence interval, or paired significance test. It therefore shows that LettinGo roughly matches GPT-4o, not that it meaningfully outperforms it.

There is also an evaluator-alignment advantage. LettinGo is optimized directly against the behavior of the LLaMA3 downstream predictor, while GPT-4o is not. A profile can therefore win by using language or structure that this evaluator handles well, even if it is not a better general-purpose description of the user.

The Qwen2.5 7B experiment provides a second backbone:

| Method | Accuracy | F1 |
| --- | ---: | ---: |
| `10H` | 52.50 | 50.23 |
| `10H+30P` | 58.30 | 56.87 |
| `10H+50P` | 56.64 | 55.16 |
| `10H+70P` | 57.10 | 56.58 |

This result shows that the overall recipe can be rerun with Qwen and that profile augmentation still helps on MovieLens. It is evidence for **method portability**, not direct transfer of one trained profile generator across backbones. The experiment covers only one dataset and provides no prompt-only or SFT Qwen controls, so it does not isolate DPO's contribution under the new backbone.

## Final takeaways

The first durable lesson is that user-profile generation should be treated as a **data-driven learning problem**, not only a prompting problem. A strong prompt, an LLM's world knowledge, and common-sense reasoning can produce plausible profiles, but they do not say which profile is actually useful. Even noisy downstream outcomes can provide weak supervision that moves the generator toward task-relevant representations.

The second durable lesson is the two-timescale memory design. Older interactions are compacted into a semantic long-term profile, while recent interactions remain verbatim so that short-term intent and exact order are not deliberately compressed. This is a clean and reusable architecture for both recommendation and LLM-agent memory.

## Net read

From a 2026 perspective, the empirical package feels substantially weaker than the core idea. The task is sentiment classification for one supplied item rather than recommendation ranking; only 3,000 users per dataset provide the independent training histories; weak labels are evaluator-specific and noisy; several formulas, sample counts, model sizes, metrics, and reported results are inconsistent; and the qualitative studies do not verify profile faithfulness.

The paper's acceptance is more understandable in the 2024–2025 research window, when LLM-generated profiles and direct preference alignment for recommendation were less explored. The field has moved quickly enough that its broad claims and lightweight evaluation now feel older than the paper's calendar age.

My final view is that LettinGo is a weak experimental paper built around two genuinely useful ideas: **task-trained profile generation** and **long-term compaction plus short-term raw memory**. I would not treat it as strong evidence that the generated text is a generally correct or interpretable user profile, but I would keep both design ideas for future work. The central open question is whether downstream-aligned profiles transfer across evaluators, tasks, and time without degenerating into evaluator-specific prompt artifacts.
