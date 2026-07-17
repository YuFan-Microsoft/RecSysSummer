# LLM-Based User Personas for Recommendations at Scale

**Authors:** Haoting Wang, Haokai Lu, Zheyun Feng, Jenny Huang, Yifat Amir, Gregory Hinkson, Ben Most, Zelong Zhao, Yixin Kelly Cui, Rein Zhang, Fabio Soldo, Yu Xia, Nihar Bhupalam, Minmin Chen, Konstantina Christakopoulou, Lichan Hong, Ed H. Chi

**arXiv:** https://arxiv.org/abs/2606.12198 (v2)

**PDF:** https://arxiv.org/pdf/2606.12198

**Venue:** Accepted by 2026 RecSys Industry Track

**Categories:** cs.IR (primary)

**Published:** 2026-06-10 · **Updated:** 2026-07-15

---

<!-- Reading progress: complete for our purposes. Read with the user through abstract, §1, §3, all of §4, and all of §5 (§5.4 live A/B skimmed). §2 Related Work was skimmed for lineage only. Verified against the PDF (arXiv:2606.12198v1). Statements are the paper's own unless marked *(inference)* or *(open)*. -->

## TL;DR

The paper builds a real-time service that, during serving, uses an LLM to turn a user's noisy interaction history into a concise **natural-language interest persona**. The persona is dual-objective on purpose: it *summarizes* existing interests (exploitation) and *infers novel-but-related topics* the user has not engaged with (exploration), which is meant to break the recommender's feedback loop. The second half of the paper is the systems work that makes this affordable at a billion-user scale: knowledge distillation from a teacher LLM into a small student, asynchronous inference decoupled from live traffic, quantization, and input compression via semantically clustered video representations. The paper names the platform only as a large-scale commercial video recommendation service; given the Google DeepMind authorship, YouTube is the obvious but unstated guess. *(inference)*

Two things make it distinct from the generative-recommendation line: the output is **human-readable language** rather than a structured ID, and the inference runs **online** rather than fully precomputed. The open question is how that persona is actually consumed by the downstream recommender, which the intro does not spell out.

## Where it sits (abstract, §1, and a bit of §2)

**The contrast the paper draws.** The intro sorts existing LLM-for-rec work into buckets: LLMs to build richer *item* content embeddings from text or thumbnails; LLMs fine-tuned to emit *structured outputs* — "content or cluster ids" — for use in traditional retrieval; and, from §2, traditional ID-based sequential models (RNN, graph, Transformer) that treat items as opaque identifiers. The paper's complaint about the structured-output bucket is that emitting IDs "bypasses the generation of natural language," which sacrifices semantic nuance and, importantly, precludes *user-facing* features like a human-readable interest summary. It also notes those systems run offline or near-offline for cost reasons, so they cannot react to immediate intent.

**On the reader's "structured id = semantic id?" question.** Reasonable, but broader than that. The paper says "content or cluster ids," and semantic IDs (RQ-VAE codes in the TIGER / OneRec line) are one prominent instance of that bucket, not the whole of it. The real axis the paper cares about is *structured-ID output* versus *natural-language output*. Worth noting the direct contrast with the paper we read just before this one: OneRec-Think is exactly one of these structured-ID generative recommenders, and even though it adds a text reasoning trace, its recommendation is still an itemic ID. This paper takes the opposite bet, where the deliverable itself is language. *(This bridge is mine; the paper does not cite OneRec-Think.)*

**The exploration angle.** The novel-topic half is not decoration. The intro frames it as "directly mitigating the feedback loop," meaning the echo chamber that pure exploitation creates, and it is *knowledge-grounded*: the LLM's world knowledge infers novel-but-related topics rather than sampling randomly. That is the genuinely LLM-specific move, exploration beyond collaborative-filtering co-occurrence.

## The two pillars (both are load-bearing)

The abstract and the contributions list make this a two-pillar paper. The reader's summary captured the first pillar well; the second is easy to under-weight but is the "at Scale" in the title.

- **Pillar 1 — dual-objective persona generation.** Synthesize a concise natural-language persona from noisy interaction data that both summarizes known interests and infers novel topics. Scalability of the *generation* is handled by distilling the teacher LLM's reasoning into an efficient student model.
- **Pillar 2 — cost-efficient online inference at billion-user scale.** An asynchronous generation pipeline that decouples LLM inference from live traffic, plus quantization, efficient input structuring via semantically clustered video representations, and safety mechanisms. For an industry-track paper this infrastructure is co-equal with the modeling.

## Preliminaries — the two-level planning skeleton (§3.1)

Behind the "hierarchical planning paradigm" vocabulary is a fairly plain two-stage retrieval design, and the reader's instinct that the section is dressed up in buzzwords is fair. The recommendation is split into two policies.

- **High-level language policy.** An LLM predicts a *textual description of the user's next interest*. This is the persona in action, and it is forward-looking: a prediction of the next interest, not only a summary of the past.
- **Low-level item policy.** A classic recommendation model grounds that text interest into actual items.

The grounding is the technical crux, and it is deliberately built on top of existing production retrieval rather than replacing it. The paper starts from Covington et al. [4], the classic two-tower deep retrieval that fetches items by nearest-neighbor search in a shared user-item embedding space, and adds one thing: a **semantic constraint**. The nearest-neighbor search is *restricted* to items semantically related to the LLM-generated text interest, which "confines the generation space to the user's text interests." So the persona is consumed not as a free-text prompt to a generator but as a **restriction on the candidate space** of the already-optimized retrieval stack. The reader's "text turns into a semantic embedding, then find nearest items" is the right shape; the load-bearing word is *restricted*.

Two honesty notes. The word "policy" is borrowed reinforcement-learning vocabulary; there is no MDP or reward here, just a two-stage function, LLM text then constrained nearest-neighbor search. And reusing the production sequential retriever is a pragmatic choice: it lets them layer semantics onto a system already tuned for scale rather than build a new retrieval path.

## Preliminaries — structuring the history by clustering (§3.2)

Before the LLM ever sees a user, the noisy watch history is compressed into clusters, and §3.2 compares two ways to do it.

- **Embedding-based clusters.** A hierarchical, online, density-based method [17] over the videos' **audio and visual embeddings**. It is bottom-up: fine-grained base clusters (items within a fixed distance of one another) are merged over time into broader macro clusters, producing stable cluster identifiers. The reader read the bottom-up merging correctly; the one correction is the input, which is audio-visual, not metadata.
- **Semantic-based clusters.** The Infinite Concept Personalized Clustering algorithm [3] over **salient terms** — weighted unigrams and bigrams, each with a salience score between 0 and 1, trained from the title, uploader, description, and related-video titles. It walks the user's history chronologically and, for each item, compares its salient terms to the existing cluster centroids by cosine similarity, then either starts a new cluster or joins the nearest one according to a threshold, finally pruning tiny clusters. The "infinite" part is that the cluster count is not fixed in advance: the scheme is online and non-parametric, so the number of interest clusters grows with the diversity of the user's history.

**A structural difference the reader caught: global versus per-user.** The two methods do not even operate at the same level. The embedding-based method clusters the *video corpus*, streaming in new videos to produce stable, cross-user cluster identifiers, and a user's history is then represented as the set of global clusters it lands in. *(inference, strongly implied by "stream of new videos" and "stable cluster identifiers.")* The semantic method, as its name Personalized Clustering says, clusters *one user's own watched videos*. This is a second reason, on top of cleaner topical boundaries, that it suits persona generation: each cluster is a coherent interest theme in *this* user's history, and those per-user clusters are exactly what the LLM ingests in §4. It also further weakens the labeled-perceptual alternative from the previous point, since LLM-labeling global perceptual clusters would still yield shared, non-personalized labels.

The paper's argument is that embedding-based clusters "lack semantic meaning": organized by perceptual similarity, they group videos that look and sound alike rather than by a shared concept, which makes them poor raw material for human-readable interest labels. It picks semantic clustering and reports in Figure 3(a) that it yields higher-quality personas.

**Reader's pushback, and where it lands.** The reader's objection is that "perceptual" is only half the story: one could sample a few videos per perceptual cluster and let an LLM assign a semantic label after the fact. *(my idea)* This is a fair hit, because the paper never tests that middle option; it compares raw perceptual clusters against semantic clusters, not *LLM-labeled* perceptual clusters, so its dismissal is a bit of a strawman.

The sharpening is that the deeper problem is the cluster **boundaries**, not the labels. Perceptual grouping cuts the space by how videos look and sound, which need not align with topic: two cooking videos with different visual styles can fall into different clusters, while two visually similar but topically unrelated videos can be merged. So an after-the-fact LLM label would sometimes have to describe a semantically mixed cluster and come out forced. Semantic clustering instead fixes the boundaries to be topical from the start, and because the salient terms are cheap text it delivers coherent boundaries and cheap labels together, whereas LLM-labeling millions of streaming clusters is not free. The reader's fix patches the label; the boundary problem is the deeper reason semantic clustering wins, and the paper's comparison is genuinely incomplete for leaving the labeled-perceptual variant untested. *(open)*

**How the salient-term similarity is actually computed is left vague (the reader's question).** The paper says only "cosine similarity between the item's salient terms and the cluster centroids" and never defines the vector space. Read literally, each video is a sparse, salience-weighted bag of unigrams and bigrams, the centroid is the mean of its members, and cosine is the usual sparse cosine. Under that reading the reader's synonym worry is real and unaddressed: lexical cosine treats "car" and "automobile" as orthogonal, so semantically equal but differently worded videos could be split apart. Two mitigations are plausible but neither is stated: the salient-term annotator may already canonicalize synonyms to a shared term, or the terms could be embedded densely so cosine captures meaning. On the finite-vocabulary question, the salient terms form a large, open unigram/bigram lexicon rather than a fixed set; the paper's whole pitch against prior work (§2) is that it avoids constraining outputs to "a small, fixed vocabulary" of "a few hundred predefined clusters," using an unbounded per-user cluster set instead. Tellingly, §4 later reports that salient terms are "overly broad" and that video *titles* make the best persona-generation input, so the paper itself only trusts salient terms for the coarse clustering, not for the fine persona. *(open)*

## Method §4.1 — generating the persona (the dual-function call)

**The core move.** A single LLM inference call produces a persona with two parts, one for each side of the exploitation-exploration trade-off. The reader stated this correctly, including the important detail that exploration is *per interest*.

- **Summarized interests (exploitation).** Analyze the interaction history into concise, human-readable labels for existing preferences.
- **Exploration interests.** For *each* summarized interest, use the LLM's world knowledge and reasoning to generate a novel-but-semantically-related topic. Exploration is anchored to a known interest rather than sampled globally, which keeps it relevant while still breaking the feedback loop.

**A distinction the "single call" framing hides: serving versus training.** The single unified call is a property of the *deployed student*. The *training* ground truth is produced very differently: the paper decomposes the unified prompt into a **multi-step, multi-call Chain-of-Thought workflow** run by a **teacher (Gemini 1.5 Pro)**, separately generating and refining the summaries and the exploration topics with reasoning, then applying a quality-control filter. That high-quality but slow teacher output is **distilled** into the fast single-call student. So the elegance of "one call" is bought by distilling a slower multi-call teacher, not by the small model reasoning it all out in one shot. This is the recurring industrial pattern: an expensive teacher offline, a cheap student online.

**What the output actually is, and a caution about the figure.** The persona is a set of **{summarized interest, exploration interest} pairs**: each summarized interest is paired with one explored topic. The number of pairs is a **prompt-instructed count**, and a quality-control step keeps only teacher responses that return exactly that many interests in the right format. So the clusters structure the *input* and roughly correspond to interests, but the count is set by the prompt rather than strictly equal to the number of clusters, and at serving the whole persona is produced in one joint call over all clusters, which lets the model reason across them and deduplicate rather than summarize each cluster in isolation. The reader's per-cluster mental picture matches Figure 1, but that figure is the *teacher's* multi-step training-data pipeline, not the single-call student path.

### §4.1.1 User representation, and the reader's temporal question

The three insights the reader summarized are all correct.

- **Insight 1 — use titles.** Text beats item IDs, which are opaque to an LLM, and among text, video *titles* win over descriptions and salient terms. Titles have the best signal-to-noise; descriptions carry promotional and copyright noise; salient terms are "overly broad." This is the payoff to the earlier open question about salient terms: the paper trusts them only for coarse clustering, not as the LLM's input.
- **Insight 2 — structure the input as clusters.** A raw concatenation of titles yields overly broad, abstract summaries; grouping the history into semantically coherent clusters before building the prompt yields more specific interests. The §5.1 ablation makes the choice explicit: chronological-order input (Prompt A.1) versus clustered input (Prompt A.2), with clustered winning.
- **Insight 3 — model-size plateau.** Bigger is better only up to a point: Gemini Pro and Ultra both beat Flash, but Pro to Ultra plateaus, a saturation in the reasoning this task needs. That plateau is what makes distillation safe: a mid-size teacher is already near the ceiling, so a distilled student can approach it.

**The reader's question: if you cluster by semantics, where does the temporal signal go?** Mostly it is dropped, and that is partly by design. The clustering re-groups the history by topic, and the §5.1 ablation shows they *chose* clustered input over chronological order because it produces better interests. Temporal information survives only coarsely: the persona is built from a tunable **recency window** of recent watches at a tunable **update frequency**, over a long history meant to cover both long-term and recent interests. More importantly, the persona is deliberately a *stable* representation: elsewhere the paper says it is meant to "counterbalance the production system's severe recency bias" by surfacing dormant, long-term interests. So fine-grained order is not the persona's job; that is left to the downstream **sequential transformer retriever** (the §3.1 low-level item policy). The paper openly admits the cost: asynchronous, clustered personas trade away "transient, sudden interests," mitigated only by tuning the window and refresh rate. *(This resolves the reader's worry: the persona carries coarse, stable semantics; the sequential model carries fine temporal order.)*

### §4.1.2 Distillation and the teacher data pipeline

Off-the-shelf small models fail at the simultaneous summarize-and-explore task, so the design is teacher-generates, student-distills. The teacher is Gemini 1.5 Pro. Data collection has four steps, which the reader summarized accurately: (1) **user sampling** of tens of thousands of consented users with sufficient high-satisfaction history, with unsafe videos removed; (2) **input structuring** into salient-term semantic clusters, dropping tiny clusters; (3) a **multi-step CoT workflow** where the unified serving prompt is decomposed into multiple teacher calls that separately generate and refine the summaries and exploration topics with reasoning; and (4) **quality control** keeping only responses with the instructed number of interests and format, then split into train/test.

**Reader's question 1: how is the number of interests per cluster decided?** The correction is that the count is not set per cluster at all; it is a single, prompt-instructed count for the whole user, and QC checks that the output has "the same number of interests as the prompt instructed." Clusters only structure the input; the LLM allocates the requested interests across them. How that number is chosen, and whether it adapts to the user, is not stated. *(open)* So the intuition of one-interest-per-cluster does not hold; interest count and cluster count are decoupled.

**Reader's question 2: what about second-order, cross-cluster combined interests?** This is a genuine gap, and the reader is right that the paper does not consider it. Exploration is explicitly "for each summarized interest," a first-order extrapolation of *one* interest at a time; there is no mechanism to combine two clusters, for example hiking plus photography into landscape-trek photography. The omission is consistent with how the persona is consumed downstream: it becomes a list of independent {summary, exploration} pairs, each retrieved separately by restricted nearest-neighbor search (§4.2), with no path that merges two interests. The deeper tension worth recording is that cross-interest composition is exactly the kind of inference only an LLM's world knowledge can do and collaborative filtering cannot, yet the paper confines exploration to same-cluster first-order extrapolation, leaving the most LLM-specific capability on the table. A strong follow-up would let exploration operate over *pairs or subsets* of interest clusters. *(my idea)*

### §4.2 Serving architecture

The reader's read of the pipeline is accurate: a request tries to fetch the user's persona and serves immediately if one exists; if not, the request is never blocked. Three details sharpen it.

- **Async regeneration on staleness, not every request.** On a visit the system checks the cached persona, and only if it is missing or stale does it trigger an asynchronous background job that fetches history, queries the student LLM, and updates the database; the current request does not wait, and the fresh persona serves the user's next visits. Eligibility is gated to users with a sufficiently rich, high-satisfaction history, and the student is quantized to cut cost.
- **Safety with fallback.** A safety classifier screens the LLM output, and if the new persona is flagged the system falls back to the user's previous safe persona rather than serving nothing.
- **Two ways to consume the persona (one correction to the reader's read).** Both reuse the existing retrieval stack.
  - *Conventional two-tower:* the query tower encodes the **LLM persona text** and the item tower encodes candidate videos, retrieving by cosine similarity. Here the persona embedding *is* the query.
  - *Sequential transformer with constrained NN:* the query is still the existing **user/sequence embedding**, and the persona instead *restricts* the nearest-neighbor search space to items semantically related to the persona. Here the persona is a **filter**, not the query.
  - The reader had the two-tower side right but described the constrained-NN side as "user embedding calls a constrained table," which drops the persona's role; in that path the persona defines the candidate subset, while the old user embedding remains the query.

One line ties the whole design together: both retrieval options deliberately **reuse the already-optimized production retrieval stack** (the §3.1 low-level item policy), attaching the persona only as a query or a filter. That reuse, not a new retrieval model, is what makes the system deployable at scale, and it also lets them A/B the summarized versus exploration interests separately.

## Experiments

### §5.1 Offline study: user representation

The question is which input representation makes the LLM summarize interests best. Two corrections to the reader's read, both about what the evidence actually shows.

- **What the ground truth is.** It is not the topics of the user's *future* clicked videos. The ground truth is the set of **text topics the user clicked** (clicking a topic routes to a page of videos on that subject, so it is a high-confidence interest signal), and the summarized persona is scored against those clicked topics with the **BLEURT** semantic-similarity metric. So this measures whether the summary matches the user's real interest *topics*, not whether it predicts the next video, which is a weaker claim than "predicts future clicks."
- **The title > description > salient-terms ranking is only partly stated.** The paper says titles are best and gives reasons that descriptions are noisy and salient terms too broad, but it does not lay out a clean second-versus-third ordering in the figures. Reading it as a full "description second, salient terms last" ranking is a reasonable inference, not a paper-stated result. *(inference)*

What the paper does state: the best representation is a **combination of clustered, title-based input and few-shot prompting** (Fig 3a, b, d), adopted as the standard input for all later experiments. Few-shot prompting is part of the winning recipe, alongside titles and clustering. Larger models consistently do better (Fig 3c), which motivates distillation. And clustered input beats chronological input, illustrated in Table 1: the sequential prompt yields only "bengali tv shows," while the clustered prompt resolves specific series names. This is the concrete evidence behind the §4.1.1 insights.

### §5.2 Offline evaluation: distillation performance

The reader's read of the three metrics is exactly right: **IFR** (format correctness plus the exact requested number of interests), **BLEURT** against the teacher's summaries as reference (summarization only, exploitation), and a **Creativity** side-by-side LLM autorater comparing student vs teacher {summary, exploration} pairs for novelty (exploration). Two students are distilled, Gemini Flash and Gemini Nano.

**The trend across epochs (Table 2), and the asymmetry worth remembering.**

- *IFR* saturates near 99% early, but at epoch 0 the students are near 0%. The paper's point is that an off-the-shelf small model would be flatly non-compliant on live traffic, which is the hard evidence that distillation is necessary.
- *BLEURT (summary)* rises steadily; both students peak at epoch 26.20, and Nano's 0.328 roughly matches the larger models' initial performance.
- *Creativity (exploration)* splits by size: Flash keeps improving and strikes the best balance, while Nano struggles and even goes negative.

The reading that matters: the two tasks have unequal capacity demands. Everyone learns formatting; even the small model catches up on summarization; only exploration's creativity is where Nano's capacity runs out. This empirically backs the §4 claim that off-the-shelf small models fail the dual task, and it localizes the bottleneck to **exploration, not summarization**. Flash is the smallest model that suffices, which is exactly why deployment uses Flash rather than the smaller Nano.

**A methodological caveat to carry forward.** Both BLEURT and Creativity use the *teacher* as the reference or opponent, so §5.2 measures how closely the student *imitates the teacher*, not how good the persona is in any objective sense. The teacher's own exploration quality has no independent ground truth here; whether the explored topics are actually good is deferred to the §5.3 user study and the A/B. *(open)*

### §5.3 User-satisfaction study

A survey of thousands of active US users. The protocol, which the reader described correctly: cluster the user's recent history, generate an interest per cluster, then show three representative videos from one random cluster; only if the user *recalls* watching them are they shown the generated interest label and asked to rate it. The ratings are two 5-point Likert questions, sharper than a generic "most users liked it":

- *Accuracy* — how closely the label summarizes those videos: over **80%** answered "Very" or "Extremely Closely."
- *Preference* — interest in seeing more on that topic: **71%** expressed strong interest.

**The comparative survey the reader skipped, which is the stronger evidence.** A second survey pitted the LLM personas head-to-head against a conventional *extractive* baseline of knowledge-graph-entity topics: **57%** strictly preferred the LLM personas and another **20%** rated them equivalent. Beating the incumbent method in human preference is more convincing than the absolute satisfaction numbers.

**The four failure modes (the reader named two of four).** Dissatisfaction fell into: missing some of the user's main interests; **inferring interests from sporadic activity**; mentioning outdated interests; and generating repetitive labels. The reader had outdated and repetitive; the first two matter too, especially "inferring from sporadic activity," which is the survey-side echo of the earlier worry that a near-random click forces a spurious interest.

**A methodological caveat.** The protocol has survivorship bias: only users who *recall* the videos proceed to rate, which filters out exactly the most irrelevant or jarring recommendations. And the accuracy question tests whether the *summary* is faithful; it barely tests the *exploration* half, whose value rests on the §5.4 A/B rather than this survey. *(open)*

### §5.4 Live A/B (skimmed)

Setup: equal, non-overlapping control and treatment traffic on a billions-user platform for 30+ days; control is the production stack with no personas. Per request, one summarized and one exploration interest are **randomly sampled** (not score-ranked) and fed to a sequential transformer via restricted nearest-neighbor search. The random sampling is deliberate, to enforce uniform exploration and to counterbalance the production system's severe recency bias by resurfacing dormant long-term interests, which is the design motivation behind treating the persona as a stable representation.

**The headline result the reader zeroed in on: exploration is throttled by the ranker but wins once through.**

- *Exposure gap:* items retrieved via exploration interests get **40.91% fewer** impressions than those from summarized interests, because the downstream ranker struggles to surface novel content.
- *Recommendation efficiency:* conditional on being shown, exploration items are **13.6% more likely** to be watched than summarized-interest items.

Together this is exactly the reader's read: the ranker kills a chunk of exploration candidates, but the survivors engage better. The methodological lesson is that the persona injects novel candidates at *retrieval*, which are then suppressed by an incumbent *ranker* not optimized for novelty, so the bottleneck is the ranker, not the persona.

**Three things worth recording beyond the reader's summary.**

- *Overall lift is significant but small* (p < 0.05): +0.04% watch time, +0.03% active users, +0.04% engaged topics, +0.03% users with multiple lasting engaged topics. Meaningful in absolute terms at scale, but modest in magnitude.
- *Gains concentrate in casual users*, because the LLM persona infers preferences better from sparse data and casual users have more concentrated, easier-to-cover interests. Core users benefit little.
- *A tension with what was deployed:* the live model is **Gemini Nano**, whose creativity was the *worst* in §5.2 (negative Creativity). So the +13.6% exploration efficiency was achieved by the student weakest at exploration, chosen for latency and cost; it plausibly understates what Flash would deliver, a real cost-versus-quality trade the paper makes explicit.

## Open questions raised while reading (some resolved as we read)

- **How is the persona consumed? (resolved, §3.1 / §4.2.)** The persona is not a generator prompt; it either *is* the two-tower query embedding, or it *restricts* the sequential retriever's nearest-neighbor search to semantically related items.
- **Is the exploration actually novel, or feedback-looped?** The persona is generated from interaction data that is itself the product of the old recommender. How far can the "novel topics" escape that loop? The +13.6% exploration efficiency suggests they do capture missed high-affinity topics, but relevance control is not spelled out.
- **What does "real-time" really mean here? (resolved, §4.2.)** Not per-request inference. The persona is regenerated asynchronously only when missing or stale and served from cache, so freshness is a tunable refresh window, closer to "frequently refreshed cache" than live inference.
- **Salient-term similarity is underspecified.** The clustering cosine is over an unstated vector space; if lexical, synonymy is unhandled unless the annotator canonicalizes terms, which the paper does not state.
- **Interest count and cross-cluster composition.** The per-user interest count is prompt-set with no stated rule, and exploration is strictly first-order (one topic per existing interest), leaving second-order combined interests, the most LLM-specific capability, untouched.

## Net read

A clean, honest industry paper. The contribution is not a new model but a *deployable pattern*: use an LLM to produce a natural-language, dual-objective (exploit + explore) user persona, distill a large teacher into a cheap student, serve it asynchronously as a cache, and attach it to the existing retrieval stack as either a query or a candidate filter. The most interesting empirical finding is the exploration exposure-gap versus efficiency split, which localizes the real blocker to the downstream ranker rather than the persona. It stands or falls not on a single claim but on cost-effectiveness at scale; the honest weak spots are the small absolute lift, the reliance on teacher-referenced offline metrics, and the fact that exploration, its most distinctive capability, is both throttled by the ranker and served by the least-creative student. Two ideas it leaves open and that connect to the reader's own research: cross-cluster *combined* interests (second-order exploration), and a ranker made novelty-aware so exploration candidates are not suppressed.

---

## Appendix — Prompts from the paper (verbatim, lightly de-hyphenated)

Reproduced from the paper's appendices A and B (arXiv:2606.12198v1). PDF-extraction artifacts (broken hyphenation, spacing, subscripted `video_metadata`) are cleaned up; wording and structure are unchanged. Placeholders like `video_metadata_1 ... video_metadata_m` and `<Num_Groups>` are the paper's own.

### Prompt A.1 — Summarization, sequential (chronological) input

Two-shot prompt for the user-interest summarization task, with user activity represented in sequential, chronological order.

```
I'm a brilliant video topic summarization expert that speaks all languages.
Given a set of videos a person watched, I can describe the interests of that
person and explain why respectively. I can also wrap interests of that person
using **.

For example: A person watched videos with titles:
video_metadata_1, ... video_metadata_m
My output is:
[Group 0]: **<Summarized Interests 0>**: <Reasoning 0>
[Group 1]: **<Summarized Interests 1>**: <Reasoning 1>
[Group 2]: **<Summarized Interests 2>**: <Reasoning 2>
[Group 3]: **<Summarized Interests 3>**: <Reasoning 3>

As another example: A person watched videos with titles:
video_metadata_1, ... video_metadata_m
My output is:
[Group 0]: **<Summarized Interests 0>**: <Reasoning 0>
[Group 1]: **<Summarized Interests 1>**: <Reasoning 1>
[Group 2]: **<Summarized Interests 2>**: <Reasoning 2>
[Group 3]: **<Summarized Interests 3>**: <Reasoning 3>

Now, if a person watched videos with video_metadata_1, ... video_metadata_m,
My output is:
```

### Prompt A.2 — Summarization, clustered (grouped) input

Two-shot prompt for the same task, but the user activity is first grouped into clusters, then represented by group.

```
I'm a brilliant video topic summarization expert who speaks all languages.
Given a few groups of videos a person watched, I can describe the interests of
that person for each group and explain why, respectively. I can also wrap the
interests of that person using **.

For example: A person watched the following groups of videos:
[Group 0]: video_metadata_1, ... video_metadata_m0
[Group 1]: video_metadata_1, ... video_metadata_m1
[Group 2]: video_metadata_1, ... video_metadata_m2
[Group 3]: video_metadata_1, ... video_metadata_m3
My output is:
[Group 0]: **<Summarized Interests 0>**: <Reasoning 0>
[Group 1]: **<Summarized Interests 1>**: <Reasoning 1>
[Group 2]: **<Summarized Interests 2>**: <Reasoning 2>
[Group 3]: **<Summarized Interests 3>**: <Reasoning 3>

As another example:
A person watched the following groups of videos:
[Group 0]: video_metadata_01, ... video_metadata_0m0
[Group 1]: video_metadata_11, ... video_metadata_1m1
[Group 2]: video_metadata_21, ... video_metadata_2m2
My output is:
[Group 0]: **<Summarized Interests 0>**: <Reasoning 0>
[Group 1]: **<Summarized Interests 1>**: <Reasoning 1>
[Group 2]: **<Summarized Interests 2>**: <Reasoning 2>

Now, a person watched following <Num_Groups> groups of videos:
[Group 0]: video_metadata_01, ... video_metadata_0m0
[Group 1]: video_metadata_11, ... video_metadata_1m1
[Group 2]: video_metadata_21, ... video_metadata_2m2
[Group 3]: video_metadata_31, ... video_metadata_3m3
My output is:
```

### Prompt B.1 — Unified summarization + exploration (the serving prompt)

The dual-objective prompt: Task 1 summarizes each group's interest; Task 2 generates, for each summarized interest, three creative-but-relevant exploration interests. Summaries are wrapped in `**`, exploration interests in `&&`.

```
I'm a brilliant video topic summarization expert who speaks all languages.
Given a few groups of videos a person watched, I can complete the following
2 tasks:

Task 1: Describe the interests of that person for each group and explain why,
respectively. I can wrap the interests of that person using **.

Task 2: For each summarized interest in Task 1, think of 3 creative and
exploratory interests that are relevant to that summarized interest, but also
novel and provide new perspectives. I can wrap the exploration interests in
this task using &&.

For example: A person watched the following groups of videos:
[Group 0]: video_metadata_1, ... video_metadata_m0
[Group 1]: video_metadata_1, ... video_metadata_m1
[Group 2]: video_metadata_1, ... video_metadata_m2
[Group 3]: video_metadata_1, ... video_metadata_m3
My output is:
[Group 0]:
Task 1: **<Summarized Interests 0>**: <Reasoning 0>
Task 2: &&<Exploration interests 0_0>&&, &&<Exploration interests 0_1>&&, &&<Exploration interests 0_2>&&
[Group 1]:
Task 1: **<Summarized Interests 1>**: <Reasoning 1>
Task 2: &&<Exploration interests 1_0>&&, &&<Exploration interests 1_1>&&, &&<Exploration interests 1_2>&&
[Group 2]:
Task 1: **<Summarized Interests 2>**: <Reasoning 2>
Task 2: &&<Exploration interests 2_0>&&, &&<Exploration interests 2_1>&&, &&<Exploration interests 2_2>&&
[Group 3]:
Task 1: **<Summarized Interests 3>**: <Reasoning 3>
Task 2: &&<Exploration interests 3_0>&&, &&<Exploration interests 3_1>&&, &&<Exploration interests 3_2>&&

As another example ...
Now, a person watched following <Num_Groups> groups of videos: ...
My output is:
```
