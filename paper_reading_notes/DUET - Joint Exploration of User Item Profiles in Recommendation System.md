# DUET: Joint Exploration of User Item Profiles in Recommendation System

**Authors:** Yue Chen, Yifei Sun, Lu Wang, Fangkai Yang, Pu Zhao, Minjie Hong, Yifei Dong, Minghua He, Nan Hu, Jianjin Zhang, Zhiwei Dai, Yuefeng Zhan, Weihao Han, Hao Sun, Qingwei Lin, Weiwei Deng, Feng Sun, Qi Zhang, Saravan Rajmohan, Dongmei Zhang

**arXiv:** https://arxiv.org/abs/2604.13801 (v1)

**PDF:** https://arxiv.org/pdf/2604.13801

**Venue:** 15 pages, 2 figures

**Categories:** cs.IR (primary)

**Published:** 2026-04-15

---

<!-- Reading progress: complete. The abstract, introduction, full method, main ablations, ranking setup, semantic analysis, appendix details, and released training and ranking code were examined. The remaining experimental tables were read selectively rather than line by line. Statements are the paper's unless marked *(inference)*. -->

## Initial read — Abstract

### From latent alignment to textual alignment

Traditional recommenders represent users and items as dense vectors and optimize their compatibility in a shared latent space. The vectors are useful for relevance estimation, but their dimensions are difficult to inspect or explain.

LLM-based systems introduce a different representation layer: natural-language profiles for users and items. These profiles are human-readable and can be consumed directly by later LLM reasoning modules.

| Representation | Alignment space | Main strength | Main weakness |
| --- | --- | --- | --- |
| Dense user and item vectors | A learned latent space | Efficient scoring and end-to-end optimization | Opaque and difficult to inspect |
| Independent textual profiles | Natural language | Interpretable and easy to reuse in LLM pipelines | Two plausible descriptions may emphasize incompatible facets |
| DUET's paired textual profiles | A jointly generated, interaction-conditioned language space | Both descriptions can emphasize the facets relevant to the current pair | The profiles may become pair-specific rationalizations rather than stable descriptions |

### The two problems identified by the abstract

The first problem is the same one raised by LettinGo: there is no unique ground-truth profile or obviously optimal template. A manually prescribed list of attributes can be brittle and may not preserve the information that matters for the downstream task.

The second problem is specific to jointly using user and item profiles. If they are generated independently, each profile can be reasonable on its own while the two descriptions focus on different semantic axes. For example, a user profile may emphasize heavy metal while an album profile emphasizes polished pop production, even though the pair is actually compatible through a shared funk-rock interest.

This means that the desired alignment is not merely factual correctness on each side. The profiles should expose **compatible evidence for this particular user–item decision**.

### What DUET claims to do

DUET is an interaction-aware profile generator. It conditions on both user history and item evidence, then jointly produces a paired user profile and item profile.

The abstract describes three stages:

1. Raw histories and metadata are compressed into compact cues.
2. The cues are expanded into paired profile prompts and then into textual profiles.
3. Reinforcement learning uses downstream recommendation performance to optimize the profile-generation policy.

The shared natural-language space provides the representation, joint conditioning provides pairwise semantic coordination, and downstream feedback supplies task alignment. The abstract does not describe a separate contrastive alignment loss. *(inference)*

### The most important precision: these may not be stable profiles

The reader's initial interpretation is correct, but "joint generation" has a stronger meaning than simply training one model to output two independent descriptions. Both outputs are conditioned on evidence from both sides.

Therefore, the generated user profile may change when the candidate item changes, and the generated item profile may change for different users. *(inference, to verify in the method)* This makes DUET closer to a pair-conditioned textual representation or explanation than to a reusable, user-only or item-only profile.

This is potentially powerful because it can surface the relevant facet of a multi-interest user and a multi-faceted item. It is also risky because the generator may overstate compatibility after seeing both sides, producing a persuasive post-hoc rationale rather than a faithful profile.

### Lineage from LettinGo

DUET appears to extend the central LettinGo idea. LettinGo learns a user-profile generator from downstream weak supervision; DUET adds the item side and makes profile generation interaction-aware. *(inference based on the shared authors and method framing)*

The conceptual progression is:

1. Do not rely only on a fixed profile prompt.
2. Use downstream outcomes to train profile generation.
3. Do not optimize user and item text independently.
4. Generate both sides together so that they expose mutually relevant semantics.

### Questions the method must resolve

- The Introduction says both histories are joint inputs, but exactly where cross-conditioning enters the cue, self-prompt, and profile-generation sequence still needs to be verified. *(open)*
- Is one pair of profiles generated for every candidate during scoring, and if so, what is the inference cost? *(open)*
- What constitutes "item history": metadata, reviews from other users, interaction logs, or all of them? *(open)*
- How does the data construction guarantee that the target user's own label or review is excluded from the item evidence? Otherwise the joint generator could leak the answer. *(open)*
- Does the reinforcement-learning reward encourage factual grounding, or only downstream correctness? *(open)*
- How does DUET prevent joint alignment from becoming post-hoc rationalization that makes every candidate sound compatible? *(open)*
- Are the generated profiles reusable representations, or are they temporary pair-specific reasoning artifacts? *(open)*

## Introduction — alignment means coordinating semantic facets

The reader's summary of the motivation is accurate. The Introduction makes three complaints about existing LLM-based recommendation pipelines:

1. Directly inserting long, sparse, or heterogeneous raw histories into an LLM can produce noisy and incomplete signals.
2. Handwritten profile templates require human engineering and restrict what the profile can express.
3. Independently generated user and item profiles do not model their interaction before each side has already been compressed.

The third point is the least intuitive and the most important. It is not primarily a claim that an external embedding model will assign a low cosine similarity to two otherwise relevant pieces of text. The problem occurs earlier, during **facet selection**.

A user and an item are both multi-faceted. In Figure 1:

- The user's history contains punk, metal, and funk.
- The candidate album contains pop, rock, funk-bass, and 1980s signals.
- An independent user summary chooses heavy metal and punk.
- An independent item summary chooses polished pop-rock.

Both summaries are individually defensible, but they discard the shared funk-related evidence. DUET lets both sides see the pair before completing the compression. It can therefore describe the user through a funk and soul affinity and the item through its funk-rock character.

The desired alignment is thus **conditional semantic emphasis**: select the user facet and item facet that jointly explain the current interaction.

### What the paper means by an item profile

An item profile is not the item's raw metadata. Metadata and item-side behavioral evidence are inputs from which DUET generates a higher-level natural-language representation.

The item side has several layers:

| Layer | Example |
| --- | --- |
| Raw item evidence | Category, title, reviews, interaction history, and aggregate signals such as average rating |
| Item cue | "Retro-style indie puzzle game with high difficulty" |
| Constructed item-profile prompt | "Describe pixel-art graphics and intellectual difficulty to match logic preference" |
| Final item profile | "A 2D experience featuring pixelated nostalgia and challenging mechanics that demand logical deduction" |

The final profile is meant to explain the item's characteristic and, more specifically, what kind of user it may appeal to. It abstracts and selects from the raw evidence rather than copying the title or metadata.

The unusual part is that DUET generates this item profile jointly with the user side. The constructed item prompt explicitly says what to emphasize "to match logic preference." Therefore, the same item can receive different textual profiles for different users. *(inference, strongly supported by the joint input and example)*

This makes "item profile" a somewhat misleading name. It is closer to a **user-conditioned view of the item** or a pair-specific item explanation than to a stable catalog representation.

### Deployment consequence — DUET is not a recall model

The reader's concern is exactly right. If the item representation depends on the current user, it cannot be precomputed once for the catalog and indexed with approximate nearest-neighbor search.

DUET defines one state for every user-item pair and jointly generates the user and item profiles for that pair. A full-catalog recall stage would therefore require pair-conditioned LLM generation for every candidate item, with complexity proportional to the catalog size. This is incompatible with large-scale retrieval.

The current paper's ranking experiment confirms the intended scale. For each positive user-item interaction, it samples only nine unseen items, generates predicted rating scores for a candidate set of ten, and reports NDCG. This is a small reranking experiment, not full-catalog recall.

A realistic deployment would need two stages:

1. A conventional embedding, collaborative-filtering, or generative retriever first produces a small candidate set.
2. DUET generates pair-conditioned profiles and scores only those candidates as an expensive reranker.

Even this design may be costly because the supposedly reusable user profile also changes with each candidate. Ten candidates can require ten joint generations, unless the implementation batches them or shares intermediate computation. The paper provides no such systems design.

The statement that DUET uses a "single pass" and introduces "no additional latency" only means that cue extraction, self-prompt construction, and profile generation occur in one autoregressive sequence for one pair. It does not remove the cost of running that sequence separately across candidates.

#### Exact ranking loop confirmed by the released code

The public `ranking_eval/duet_score_ranking.py` implementation confirms the candidate-wise execution:

1. Each test row contains one observed positive item and nine pre-sampled negative item IDs.
2. The code extracts the same ten prior user interactions for the row.
3. For each of the ten candidates, it separately retrieves up to ten item reviews written before the target timestamp.
4. It creates one DUET generation prompt from that fixed user history and the current candidate's item history.
5. DUET jointly generates a new user cue, user self-prompt, user profile, item cue, item self-prompt, and item profile for that candidate.
6. A second downstream LLM receives the generated user and item profiles and predicts a numeric rating from 1.00 to 5.00.
7. The ten candidates are sorted by these predicted ratings to compute Hit Rate, NDCG, and MRR.

Therefore, the answer to the reader's question is unambiguously yes: **the same user's textual user profile is regenerated ten times, once for each candidate item**. The code batches these generations for GPU throughput, but batching does not change the amount of pair-specific generation or make the representations cacheable.

The ranking label is also assigned solely by whether a candidate ID equals the observed target item ID. The script does not inspect the target interaction's rating when marking it as the one positive candidate. Unless the unpublished data-preparation step filters test targets to positively rated interactions, a disliked but observed item could still be treated as the item that should rank first. *(open)*

#### The paper mixes two different prediction targets

For **rating prediction**, one observed user-item pair has a true numerical rating. DUET jointly generates the two pair-conditioned profiles, and the frozen downstream LLM predicts that rating. MAE, RMSE, Accuracy, and F1 compare the predicted rating with the observed rating.

For **candidate ranking**, the system repeats the same rating-prediction procedure for the observed target item and nine unobserved items. It then treats each predicted rating as a ranking score. The identity of the observed item, rather than its rating value, defines the one positive candidate.

DUET therefore never generates the next item directly. It is a pairwise feature generator placed in front of an LLM rating scorer, and the ranking experiment reuses that scorer as a reranker.

The code also exposes a discrepancy with the paper's inference description. The paper says the learned prompt is greedily executed at inference time, while the released ranking code samples profile generations with temperature 0.7. The reported candidate scores may therefore depend on stochastic profile sampling unless an unreported evaluation configuration overrides this behavior.

Three alternatives could preserve more of the idea while making recall feasible:

- Generate several stable user-interest facets and item facets offline, then retrieve by matching the best facet pair. *(my idea)*
- Use DUET only as a teacher and distill its pairwise score into a cacheable dual-encoder retriever. *(my idea)*
- Keep global user and item profiles for recall, then allow candidate-conditioned profile refinement only during reranking. *(my idea)*

### A dual-encoder versus cross-encoder analogy

Independent textual profiling resembles a dual encoder. Each side is compressed without seeing the other, and compatibility is computed only after the representations are fixed.

DUET is closer to a cross encoder. User and item evidence interact before the final textual representations are produced. The resulting profiles can encode pair-specific interaction features rather than only global user and item attributes. *(inference)*

This explains both the attraction and the danger:

| Property | Independent profiles | DUET joint profiles |
| --- | --- | --- |
| Reusability | One user profile and one item profile can be cached and reused. | Profiles may need to be regenerated for each pair. |
| Semantic coverage | Each summary may choose a globally salient but incompatible facet. | The pair can expose a shared, decision-relevant facet. |
| Faithfulness risk | Compression can omit relevant information. | Joint generation can cherry-pick overlap or rationalize a weak match. |
| Computational shape | Similar to two-tower precomputation. | Similar to candidate-time cross interaction. |

Calling these outputs "profiles" is therefore potentially misleading. A stable user profile should describe the user independently of the current candidate, whereas DUET appears to generate a candidate-conditioned view of the user. The same concern applies to the item profile.

### What the proposed method adds

At the highest level, the reader's summary is right: DUET uses downstream recommendation feedback and reinforcement learning to let a model generate free-text user and item representations jointly.

The paper claims two additional mechanisms beyond that sentence:

- **Cue-based initialization** first compresses raw histories and metadata into minimal evidence.
- **Self-prompt exploration** expands each cue into a richer profile-generation instruction before producing the final paired profiles.

The intended causal chain is:

1. Cues remove noise from raw histories.
2. Self-prompts avoid one human-designed profile template.
3. Joint conditioning preserves the semantic intersection between user and item.
4. Reinforcement learning selects generations that improve the downstream task.

The reviewers' attribution concern now becomes precise. If most of the final gain comes from RL, the experiments must still show that cue initialization, self-prompting, and joint conditioning each add value beyond simply RL-training an ordinary fixed-prompt generator.

### Reader's interpretation of "shared semantic space"

The Introduction borrows the language of latent vector alignment and says that user and item text are aligned in a shared semantic space. At this point, there is no explicit geometric space, contrastive objective, or textual similarity constraint.

The phrase should therefore be read operationally: both profiles are natural language, they are generated jointly, and downstream reward favors paired descriptions that help the recommender. Whether this deserves to be called alignment rather than pair-conditioned generation remains an open conceptual question.

### The motivation is mismatched with retrieval

The reader identified a more fundamental problem with the paper's motivation. If the intended application is recall, it is not enough for the user and item profiles to sound semantically compatible in natural language. They must be compatible under the **actual embedding model and similarity function used by the retrieval system**.

A recall-oriented formulation should preserve independent, reusable representations:

1. A user profile should be generated from the user's history without seeing a candidate item.
2. An item profile should be generated from the item's evidence without seeing the current user.
3. Both profiles should be encoded by the retrieval model that will be used at serving time.
4. The generator, encoder, or both should be optimized with a retrieval objective that brings positive pairs closer than sampled negatives.

This would make item embeddings globally precomputable and allow approximate nearest-neighbor search. It would also define "alignment" concretely in the geometry that determines retrieval, rather than assuming that two natural-language descriptions occupy a useful shared space.

DUET instead solves independent-profile misalignment by allowing the two sides to see each other before generating either representation. In effect, it removes the separability required by recall. This can improve a pairwise prediction because the generator can choose mutually compatible facets, but it does not solve the retrieval problem that motivates user-item representation learning.

Moreover, the released system never embeds the two generated profiles independently and compares their similarity. A second LLM reads both profiles jointly and predicts a rating. The evidence therefore supports a much narrower claim: pair-conditioned textual rationales can help an LLM judge a supplied pair. It does not establish that DUET learns user and item representations aligned for retrieval.

The natural-language motivation remains more plausible for an agentic or conversational recommender, where an LLM directly consumes the profiles for reasoning. Even in that setting, however, the outputs are pair-specific intermediate reasoning artifacts rather than reusable user and item profiles.

## Method — overall mechanism

The reader's reconstruction is substantially correct. DUET treats one user–item example as a reinforcement-learning state and the complete generated text as one action:

$$
s = \{H_u, H_i\}, \qquad a = \{C_u, S_u, P_u, C_i, S_i, P_i\}.
$$

Here, $H_u$ and $H_i$ are the user and item histories; $C_u$ and $C_i$ are concise cues; $S_u$ and $S_i$ are generated profile-construction instructions; and $P_u$ and $P_i$ are the final profiles. A single policy model $\pi_\theta$ generates all six components.

### The three stages are one autoregressive completion

The paper presents cue extraction, adaptive prompt discovery, and profile generation as three conceptual stages. They are not three separate LLM calls. The released prompt asks one causal language model to emit a tagged completion containing the cue, constructed prompt, and final profile.

The constructed prompt can influence the profile because its tokens appear earlier in the autoregressive sequence. However, it is never separately submitted to the model as a new instruction. Therefore, "executing a discovered profile prompt" is a stronger description than what the implementation literally does. The constructed prompt is an intermediate span inside the same trajectory.

The released output format is also ordered asymmetrically:

1. user cue;
2. user constructed prompt;
3. user profile;
4. item cue;
5. item constructed prompt;
6. item profile.

Both sides can inspect both raw histories because the combined pair is in the input. At the generated-token level, however, the item side can additionally condition on the completed user side, while the generated user side cannot condition on the later item outputs. Thus, "joint generation" means one joint conditional sequence rather than a symmetric exchange between two profile generators.

### Cue generation

Cue extraction is initiated by a fixed human-written instruction. It asks the policy model to inspect user rating behavior, preferences, review sentiment, or item reception and to emit a concise phrase rather than a complete description. The paper defines a cue as a deliberately partial hypothesis, not as a comprehensive high-level summary.

During GRPO training, the parameters of the same policy model are updated, so the distribution of cues produced under this fixed instruction can change. A cue that appears in a higher-reward trajectory has its token probabilities reinforced together with the rest of that trajectory.

The important qualification is that the cue has no separate target or reward. It becomes "better" only in the operational sense that the complete sequence containing it leads the frozen recommender to predict a rating closer to the label. The objective does not establish that the cue is more faithful, complete, stable, or human-interpretable.

The cue is also pair-conditioned rather than independently extracted. The prompt contains both user and item histories from the beginning, and there is no attention mask preventing the user cue from using item evidence or the item cue from using user evidence. This permits coordinated facet selection, but it also permits the cue to encode information tailored to the current pair instead of summarizing its nominal side independently.

### What is actually explored

For each state, training samples multiple complete trajectories from the same policy. The released training configuration uses eight rollouts with sampling temperature 1.0. Each rollout independently changes the cue, constructed prompt, and profile; the system does not hold a cue fixed while comparing several prompts, nor hold a prompt fixed while comparing several profile executions.

Consequently, the method does not isolate exploration over profile-construction strategies. It performs ordinary sequence-level exploration over the entire structured completion. A high reward cannot establish whether the cue, the constructed prompt, the final wording, or their combination caused the improvement. *(inference)*

### Frozen recommender and reward

For every sampled trajectory, a separate frozen LLM recommender receives the final user and item profiles and predicts the rating:

$$
\hat{y}_{ui} = f(P_u, P_i).
$$

The term "frozen downstream recommender" sounds more specialized than the implementation is. In the experiments, $f$ is an ordinary Qwen3-8B or LLaMA3-8B instruction model prompted to output a rating from the two profiles. It is not a separately designed collaborative-filtering model or a recommender trained on user-item interactions. The profile policy uses the same backbone family, but its parameters are updated by GRPO while the rating-model instance remains frozen.

The performance reward is normalized absolute rating accuracy:

$$
R_{\mathrm{perf}}(u,i) = 1 - \frac{|y_{ui} - \hat{y}_{ui}|}{M},
$$

where $M=4$ for ratings between 1 and 5. Calling this reward "continuous" means that a prediction of 4.8 receives more credit than a prediction of 4.0 when the label is 5.0. It does not mean that gradients pass through the frozen recommender.

The released reward code adds no separate semantic-alignment, cue-quality, prompt-quality, faithfulness, or ranking reward. It gives a reward between zero and one when all required tags and the predicted rating are valid; malformed profile output or an invalid rating receives minus one. Thus, the only additional signal is effectively a format gate or penalty. The training script also applies a small KL loss to the policy, but explicitly does not include KL in the scalar reward.

The paper's Figure 2 labels the feedback as "ranking correctness & format Reward," whereas the released training function computes normalized rating error plus the format penalty. This distinction matters because the learned policy is directly optimized for rating prediction, not listwise or pairwise ranking.

### What GRPO improves

GRPO compares the eight rewards obtained for the same input and raises the probability of trajectories that score better relative to the group. Because the reward is assigned to the entire completion, the cue, constructed-prompt, and profile tokens all receive the same trajectory-level advantage.

It is therefore reasonable to say that the intermediate cue and prompt are optimized indirectly: better earlier tokens may lead to better final profiles and hence a better reward. It is not justified to conclude that they become intrinsically better summaries or better instructions. They receive no direct supervision, and the frozen recommender never evaluates them. "Better" means only that the whole sampled sequence eventually induced a rating closer to the label.

This also exposes the central methodological uncertainty. The policy may genuinely learn useful cue-to-strategy-to-profile reasoning, but it may instead learn to produce reward-effective final profiles while treating the visible cue and constructed prompt as decorative scaffolding. A causal intervention that swaps or removes constructed prompts while holding the remaining trajectory comparable would be needed to distinguish these explanations. *(open)*

### How one timestamped training example is constructed

Each raw row is an observed review-and-rating event for a tuple consisting of a user, an item, a timestamp, and a rating. The rating on that row is the prediction target. Therefore, this is not a click-only dataset: the event carries an explicit one-to-five rating and usually review text.

For a target event at time $t$, the released `DUETDataset` constructs:

- **User history:** the same user's ten most recent rows whose timestamps are strictly earlier than $t$.
- **Item history:** the target item's ten most recent rows whose timestamps are strictly earlier than $t$.
- **Current item metadata:** primarily the item title in the released prompt.
- **Aggregate features:** the mean user rating and mean item rating computed over the selected historical rows.

The user-history text contains each previous item's title, rating, and up to 200 characters of the user's review. The item-history text contains the earlier reviewer's name, rating, and up to 200 characters of review text. Thus, despite the paper's broader language about "metadata," the released training prompt does not provide a rich metadata record such as category, brand, or structured attributes.

The strict timestamp filter excludes the current target row from both histories. The code does not explicitly enforce `historical reviewer != target user` when building the item history, even though the paper describes these as reviews from other users. In datasets with at most one review per user-item pair, the timestamp filter makes this largely moot; the implementation itself does not guarantee it. *(open)*

The reported average ratings are also not averages over all previous interactions. They are calculated after applying `tail(10)`, so they summarize only the same ten recent rows, despite some downstream prompt wording referring to "all previous ratings."

### Is this a chronological sliding window?

Yes, in the practical sense. The dataset iterates over timestamped interaction rows and treats each eligible row as a target, with the immediately preceding history reconstructed using a strict earlier-than-time filter and then truncated to the latest ten events. It is better described as rolling-prefix prediction than as a set of explicitly materialized fixed windows.

During training, histories are drawn only from the training dataframe. Training rows with no prior user interaction are skipped, while an item is allowed to have no prior reviews because its title remains available.

The paper states that the complete data is globally divided into training, validation, and test partitions by timestamp, with every test event later than the training and validation events. It also applies 5-core filtering and removes validation or test users and items that do not occur in training.

During released test-time evaluation, the code concatenates the training dataframe with the test dataframe and selects every row earlier than the current test event. Consequently, a later test example can use ratings and reviews from earlier test examples as observed history. This is a valid prequential or simulated-online protocol if earlier feedback is assumed to become available, but it differs from a static evaluation in which all test interactions are hidden throughout evaluation.

The repository does not release the preprocessing program that creates the train, validation, and test pickle files. The exact timestamp cutoffs, split proportions, and negative-sampling preprocessing therefore cannot be reconstructed from the published code alone.

## Experiments — are the intermediate steps necessary?

The paper attempts to answer this question in Table 3, but the evidence is suggestive rather than conclusive.

Its closest comparison is between `Profile + Joint Opt.`, described as joint user-item profile optimization without the strategy layer, and the full `Profile + Cue&Strategy + Joint Opt.` model. Adding cue and strategy improves MAE, RMSE, and accuracy on all three datasets. It also improves F1 on Yelp and Amazon Music, but reduces F1 on Amazon Books from 60.57 to 59.27.

The comparison without joint optimization is substantially weaker. Adding `Cue&Strategy` to `Profile` produces only small accuracy improvements:

| Dataset | Profile accuracy | Profile + Cue&Strategy accuracy | F1 change |
| --- | ---: | ---: | ---: |
| Yelp | 55.48 | 55.83 | 48.09 to 48.54 |
| Amazon Music | 58.67 | 58.91 | 57.48 to 55.53 |
| Amazon Books | 57.14 | 58.43 | 57.68 to 56.88 |

Thus, the paper's claim of "modest but consistent gains" depends on which metric is selected. MAE and accuracy improve, but F1 becomes worse on two of the three datasets. No variance, multiple-seed result, or statistical significance test is reported, so small differences cannot establish necessity.

More fundamentally, the ablation removes cue and strategy as one bundled block. It does not separately test cue extraction, constructed-prompt generation, and the causal use of that prompt by the final profile. It also does not report interventions such as replacing the constructed prompt with a constant instruction, shuffling prompts across trajectories, or preserving the extra reasoning tokens while removing their claimed semantics.

The full structured trajectory may help because it gives the model extra scratchpad tokens, imposes an output scaffold, changes generation length, or regularizes the policy. Table 3 cannot distinguish these explanations from genuine adaptive prompt discovery.

Table 5 establishes that RL is important for the full system, but it does not validate the intermediate mechanism. There is also an unexplained discrepancy: `Profile + Cue&Strategy` in Table 3 appears to be the natural no-joint-optimization counterpart of the full model, yet its numbers differ substantially from `DUET w/o RL` in Table 5. For example, Yelp accuracy is 55.83 in Table 3 but 48.53 in Table 5. The paper does not explain what differs between these two seemingly similar configurations. *(open)*

The strongest justified conclusion is therefore that adding the bundled cue-and-strategy scaffold correlates with better performance when combined with joint optimization. The experiments do not demonstrate that the generated cue and constructed prompt are necessary, causally operative intermediate states.

### Semantic and grounding sanity checks

The paper's quantitative profile analysis is one of the more relevant experimental additions because it inspects the generated text rather than only downstream rating accuracy.

For semantic alignment, it embeds the generated user and item profiles with the external `all-mpnet-base-v2` sentence encoder and reports their cosine similarity. DUET obtains the highest average similarity on all three datasets.

This is useful as a coarse sanity check, but it is not strong evidence of recommendation alignment. The profiles are jointly generated for the same pair and can deliberately repeat compatible facets, so high within-pair similarity is partly built into the construction. The paper does not report whether an observed pair has higher similarity than mismatched or negative user-item pairs. Generic, mutually agreeable profiles could therefore score highly without being discriminative.

The chosen encoder is also unrelated to the frozen LLM that supplies the training reward. The metric shows that another sentence encoder perceives lexical-semantic similarity; it does not establish alignment under the actual downstream scorer or under a deployable retrieval embedding model.

For grounding, the paper defines coverage as the fraction of profile tokens that also occur in the corresponding raw history. This lexical-overlap precision is easy to interpret, but calling it "faithfulness" is too strong. Copying a short generic phrase can obtain high coverage, a correct paraphrase can obtain low coverage, and a contradiction can share many tokens with its source. The metric measures textual reuse rather than entailment or factual support.

DUET has the highest alignment scores but not uniformly the highest user or item coverage. The authors more cautiously describe its coverage as comparable or mid-to-high. Overall, these metrics provide a rough view of profile behavior, but they neither validate the intermediate constructed prompts nor show that the generated profiles preserve truthful, discriminative user and item information.

## External review context — ICLR 2026 withdrawn submission

An earlier version of DUET was submitted to ICLR 2026 on September 19, 2025 and withdrawn by the authors on January 6, 2026. The current arXiv paper was published on April 15, 2026, so the reviews apply to an earlier version rather than automatically describing the present PDF.

The score distribution was highly mixed:

| Reviewer | Soundness | Contribution | Overall rating |
| --- | ---: | ---: | ---: |
| vEKn | 1, poor | 2, fair | 2, reject |
| 3Gyu | 2, fair | 1, poor | 4, marginally below |
| sG5X | 2, fair | 2, fair | 2, reject |
| hRi7 | 2, fair | 3, good | 6, marginally above |

The positive consensus was that the paper is easy to follow and that two ideas are promising: replacing fixed profile templates with cue-driven exploration, and optimizing user and item profiles jointly with downstream feedback.

The negative consensus is more important for this reading:

1. **Attribution to RL.** The strongest reviewer concern is that Table 1 compares a fully RL-trained DUET against prompting-only baselines. According to one review, the non-RL `Profile + Self-Prompt` variants do not outperform all baselines, suggesting that RL may explain most of the gain rather than joint profile exploration.
2. **Rating prediction rather than ranking.** Multiple reviewers object that the experiments evaluate rating or sentiment prediction instead of item retrieval or ranking with Recall, NDCG, MAP, or Hit Rate.
3. **Insufficient quantitative support for the mechanism.** Case studies show selected successes but do not establish that semantic user-item alignment occurs more often than in baseline outputs or that it causes the aggregate improvement.
4. **Unclear exploration.** The cue-to-self-prompt-to-profile pipeline appears to be a single sequence-to-sequence pass. Reviewers question whether this constitutes meaningful exploration of alternative formats or merely one fixed refinement procedure.
5. **Fairness of the joint-profile comparison.** It is unclear whether baselines receive item profiles as well as user profiles. Without that control, the experiment may conflate adding item-side information, joint conditioning, self-prompting, and RL.
6. **Efficiency.** Joint profile generation plus an RL loop appears expensive, but the withdrawn version reported no training-time, inference-latency, or cost comparison.
7. **Reproducibility and RL stability.** Reviewers requested code, hyperparameters, learning curves, sensitivity analysis, and comparison with alternatives such as PPO.
8. **Cue faithfulness and robustness.** Short cues may collapse distinct users or discard important evidence. The reviews ask for perturbation studies, sparse-user analysis, conflicting-preference cases, and cold-start evaluation.

### How the reviews change the reading plan

The current arXiv version should be checked against the following stronger attribution ladder:

| Question | Required comparison |
| --- | --- |
| Does adding an item profile help? | User-only profile versus user-plus-item profiles |
| Does joint conditioning help? | Independently generated user/item profiles versus jointly generated profiles |
| Does self-prompt exploration help? | Fixed profile prompt versus cue plus self-prompt under identical training |
| Does RL help? | Prompt-only, SFT, and RL variants with the same architecture and inputs |
| Does the representation help recommendation? | Full-catalog or candidate-set ranking, not only rating prediction |
| Is textual alignment genuine? | Large-scale groundedness and alignment measurements, not only selected examples |
| Is it deployable? | Generation latency, number of LLM passes, training cost, and candidate-time complexity |

The April 2026 arXiv version does address several surface-level review requests. It releases code, adds ten-candidate NDCG evaluation with both random and EASE-based hard negatives, reports an RL ablation, and introduces semantic alignment and lexical coverage analyses.

The central attribution problem remains unresolved. The revision still lacks isolated interventions on the cue and constructed prompt, an equal-budget RL-trained direct pair scorer, convincing full-catalog or realistic large-candidate evaluation, and latency or cost analysis. The added experiments make the paper more complete without establishing its main causal story.

## Final takeaways

The most charitable interpretation of DUET is a **task-optimized, pair-conditioned textual bottleneck**. Given one user-item pair, a policy model verbalizes selected evidence, and a frozen LLM predicts the rating from that text. Reinforcement learning adapts the communication between these two models when no gold profile text exists.

That narrower idea is coherent. Downstream feedback can be useful for learning what information to preserve during textual compression, and jointly examining both histories can expose interaction-specific evidence that an independent summary might omit.

However, the paper repeatedly describes the resulting text as aligned user and item representations. This framing is misleading. Both outputs depend on the current pair, the same user's profile changes across candidates, and a second LLM reads both outputs jointly. The system is much closer to an expensive cross-encoder with generated rationales than to reusable user-item representation learning.

The claimed cue-to-strategy-to-profile mechanism is also unproven. All fields are emitted in one autoregressive completion and receive only the final sequence-level reward. The constructed prompt is not separately executed, evaluated, or causally tested. It may be a useful plan, but it may equally be decorative scaffolding or extra scratchpad tokens.

The reward establishes only evaluator-specific utility. It encourages the generated profiles to make a frozen rating LLM output the known label, without directly rewarding factual grounding, stable preferences, discriminative retrieval, or honest explanation. This leaves substantial room for post-hoc rationalization and implicit communication of rating cues.

The experiments do not rescue these claims. Rating prediction is a narrow proxy for recommendation; ten-candidate ranking remains far from retrieval; the cue-and-strategy ablation bundles several changes; semantic cosine is partly tautological for jointly generated pairs; and token overlap is not a reliable measure of faithfulness. Several configurations and implementation details are also insufficiently explained.

For a recall system, a more principled design would generate candidate-independent user and item profiles and optimize them under the actual retrieval encoder and contrastive ranking objective. For a reranker, the honest comparison would be against an equally trained pair-conditioned LLM scorer or rationale generator without the profile theater.

## Net read

DUET contains a modest combination-level idea: use downstream RL to optimize pair-conditioned textual evidence for a frozen recommendation judge. The paper overstates that idea as adaptive prompt discovery and shared-space representation learning without providing the interventions needed to support either claim.

My present-day assessment is **3/10, Strong Reject**. The earlier ICLR 2026 submission was withdrawn, and the expanded arXiv version still would not meet the bar for a sound recommendation paper.
