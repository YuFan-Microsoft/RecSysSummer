# TokenMinds: Pretrained User Tokens and Embeddings for User Understanding in Large Recommender Systems

**Authors:** Qingyun Liu, Bo Yan, Yang Liu, Yuji Roh, Ekansh Sharma, Likang Yin, Emma Olowo, Min-hsuan Tsai, Yuxuan Li, Diego Uribe, Saksham Aggarwal, Siqi Wu, Yuan Hao, Vikas Kedigehalli, Lukasz Heldt, Lichan Hong, Li Wei, Xinyang Yi

**arXiv:** https://arxiv.org/abs/2606.25147 (v1)

**PDF:** https://arxiv.org/pdf/2606.25147

**Venue:** —

**Categories:** cs.IR (primary), cs.AI, cs.LG

**Published:** 2026-06-23

---

<!-- Reading progress: abstract, §1–§3.5, and most of §4 (RQs, §4.1 setup, §4.2 token accuracy/ablations/diversity, §4.3 online A/B, §4.4 input-length & batch scaling). A few §4 sub-parts remain (see end). Verified against the PDF. Statements are the paper's unless marked (inference) or (open). -->

## TL;DR

TokenMinds (Google DeepMind / YouTube) represents each user with **discrete Semantic-ID (SID) tokens** *in addition to* the usual dense embedding. It extends the **PLUM** item-retrieval framework (a SID vocabulary aligned to a pre-trained LLM via CPT) from items to *users*: an encoder-decoder consumes a user's behavior and emits **both** a sequence of SID user tokens **and** a dense user embedding. The paper stands or falls on one claim — that SID-based *user* tokens are viable at industrial scale (billions of users) and add value *on top of* dense embeddings for downstream ranking.

## Where it sits — three prior directions

| Direction | What it does | Stated limitation |
| --- | --- | --- |
| Dense user embeddings (industrial default) | User as one (or a few) fixed-dim vector(s) | Even "a few" fixed-dim vectors lose fine-grained signal — bounded capacity |
| LLM **text** user profiles | Summarize history into natural-language tokens | Topical co-occurrence, not sequential dynamics; hard to **ground to item attributes**; modality gap in non-text downstream |
| SID **item** tokenization (PLUM / Semantic-ID) | Hierarchical discrete codewords from item content | Proven for items, but **discrete SID for *users* is unexplored** — the gap filled here |

**Lineage:** keep PLUM's recipe (SID vocabulary + CPT + task post-training), change the tokenized object from items to users.

## What a *user* SID represents — interest regions, not the next click

A natural first confusion: is the generated user-token sequence a **summary of the user's interests**, or a **prediction of the items the user will click next**? And if it is the latter, how is this any different from generative recommendation?

The paper answers this directly in Related Work (§2, "Generative Recommendations"). Generative *retrieval* models such as PLUM, GenRank, and GPR are "constrained to predict immediate next items." TokenMinds deliberately diverges on two axes:

- **Granularity and horizon.** User modeling here "captures a broader spectrum of intents over longer time windows" and "leverages coarser semantic granularity to identify distinct areas of interest, avoiding the strict need to map back to specific individual items." This is exactly why the decoder emits only the **coarse prefix-$L$ SID** (with $L < L_{full} = 8$, see §3.1): a coarse prefix names an *interest region* in content space, not one exact video. The output is therefore best read as a **predicted, multi-interest profile**, not a next-item guess.
- **Coupling to the downstream objective.** "Unlike GPR, which aligns user representation with downstream task metrics and policy optimization, we decouple the learning of user representations from specific downstream training objectives to provide a general purpose understanding of user interests." TokenMinds is a *general-purpose* representation, trained once and reused across many downstream models; GPR bakes the representation into one task's objective.

So it is neither a pure "interest summary" nor a "next-click predictor" in the retrieval sense: it is **generative in mechanism** (the decoder autoregressively produces the tokens) but **interest-level in semantics** (coarse regions over a long window, decoupled from any one task).

The "if it is a summary, how is it consumed?" half is answered in §3.4 (below): beam search produces $B$ SID sequences — $B$ distinct predicted interest areas — each is projected back to a dense vector (Prefix Embedding Mapping / N-gram / SPM), the $B$ vectors are pooled, and the result feeds the ranker as input features or cross-attention key-values.

*(my read)* This also settles a fair skepticism about the intro's "multi-stage → end-to-end" narrative: TokenMinds itself is **not** end-to-end. It generates the user representation **asynchronously** and feeds a **separate** ranker (§3.5), so it sits firmly in the decoupled, multi-stage camp — the decoupling is a feature, not an omission.

## Core design

- **Dual output is deliberate.** The dense embedding preserves **backward compatibility** with downstream models that already eat dense user vectors; the SID tokens add a discrete, grounded representation. This backward-compat story is the key deployment argument.
- **Inputs (§3.1).** The encoder consumes the user's chronological behavior across multiple surfaces: **watch history** interleaved with **textual search queries**, each watch carrying fine-grained **temporal and engagement signals** (interaction **timestamps**, **likes/dislikes**). On the item side, a video is represented not by a random VID but by its **content features → RQ-VAE → SID** (content features, not just title text). The stated payoffs are better **head/tail generalization** and **temporal stability**: new items quantize into the *same* fixed codebook, so there is no vocabulary churn as the corpus evolves — a problem that otherwise hurts most over long histories. See the SID-vs-VID insight below.
- **Encoder-decoder, not decoder-only** (§3.1). The **encoder** captures full-history sequential patterns and the dense embedding is pooled off its contextualized outputs (last-token / mean); the **decoder** autoregressively generates the SID user tokens. Bonus: encoder/decoder can be **decoupled at serving** — heavy low-frequency encoder for long history, light high-frequency decoder for recent behavior. Both are initialized from PLUM's CPT.
- **Shared SID vocabulary** unifies long-form and short-form video in one model, cutting cost.
- **Serving (§3.5).** Representations are generated **asynchronously** and cached in a KV store; real-time scoring just **reads the cache** — constant latency/cost, off the heavy TokenMinds critical path. On a hit, the cached representation is fed to the ranker; on **expiry or miss**, a background Refresh Service reads the user's *latest* history, runs the exported TokenMinds, and writes the result back. Two consequences worth noting: (a) validity is judged by **expiry (TTL) / presence** — the paper regenerates on "expired or missing," *not* on a new-watch event, so a just-added watch is reflected only after the next expiry/refresh *(inference)*; (b) because the refresh is **background**, generation never blocks the current scoring request — precisely what keeps latency constant.

## Insight — "grounding to item attributes" and the "modality gap"

My two reading questions were: (a) if I have a user representation, can't I just retrieve with embeddings? and (b) if user-interest text and item title/description share one text encoder, where is the gap?

- **Grounding.** A text profile ("likes jazz, cooking") lives in *language space* and is topic-level. Embedding it gives neighbors that are textually similar *texts*, not the actual catalog items — you retrieve by coarse topic similarity, misaligned with the recommendation objective. "Grounding to item attributes" means tying the representation to real items in a *specific target domain's catalog*, which free text has no stable mapping to.
- **Modality gap = text vs. the *non-textual production stack*, not text vs. text.** The intuition is right in a narrow content-based two-tower framing. But (1) items in production are ID embeddings + collaborative signals, not title strings — encoding by title throws away collaborative signal; (2) the primary downstream is **ranking**, which consumes dense ID/SID/numeric features with **no slot for a paragraph of text**; (3) the text profile itself already dropped fine-grained behavior. So both towers degrade to topic matching.
- **Why SID dissolves both.** SID is a *discrete, non-text token derived from item content semantics* (RQ-VAE), aligned into the LLM vocabulary via CPT. It is grounded like content yet compact like an ID, plugs into non-text downstream without a gap, and is *generated* by the decoder over the behavior sequence — recovering the sequential dynamics the text approach loses.

**Positioning (§2):** user modeling is deliberately *not* per-item retrieval — it "leverages coarser semantic granularity … avoiding the strict need to map back to specific individual items", over longer windows, and is decoupled from any specific downstream objective (unlike GPR).

## Insight — is a Semantic ID just a hierarchical topic model? (§3.1)

Mechanically the reading is right: item content embedding → RQ-VAE (with $L_{full} = 8$ codebook levels) → a hierarchical codeword sequence; TokenMinds keeps only the coarse prefix-$L$ codes, with $L < L_{full}$ — the example `A12 B278 C23 D77` is a length-4 prefix — to encourage diversity and reduce memorization.

**A "hierarchical semantic representation trained on the current item space" is a fair working mental model** — and RQ-VAE case studies genuinely *do* show coarse-to-fine semantic prefixes (instrument → guitar → electric guitar), because level-1 code $c_1$ is the nearest centroid to $z$ (a coarse Voronoi cell) and sharing $(c_1, c_2)$ means similar residuals. Two caveats keep it honest:

1. **RQ is residual/additive VQ with a *shared* per-level codebook, not a nested per-parent tree.** The reconstruction is a *sum* of code vectors approximating one content vector: $z_q = \sum_l e^{(l)}_{c_l}$. The level-$l$ codebook $e^{(l)}$ is indexed by level only, whereas a truly nested tree (recursive k-means) would index by parent path, $e^{(l \mid c_1 \dots c_{l-1})}$. Consequence: interpretability lives in the **prefix *path* (the combination)**, not in a bare non-first code — the same $c_2$ offset under a different $c_1$ refines a different attribute, so you cannot give $c_2$ a cross-parent label. A single top-down case study cannot tell RQ-VAE from recursive k-means. *(inference; this paper shows no SID case study.)*
2. **Hard path, not soft mixture.** Each level picks exactly one code, so an item is one path down a depth-$L$ tree — not an LDA-style distribution over topics. This gap from topic models is robust regardless of interpretability.

**Why SID (over random VIDs), per the paper:** (1) **generalization** across head/tail via meaningful collisions; (2) **temporal stability** — random VIDs suffer vocabulary churn as the corpus evolves (worst over long histories), while SID codebooks are trained once and new items quantize into the *same* vocabulary. *(the "trained once / reused" framing is my inference from the stability claim; no retraining cadence given.)*

**Aside — does RQ-VAE explicitly push same-level centroids apart?** No. The loss is the VQ-VAE objective per level on the residual (reconstruction + codebook + $\beta$·commitment), with **no pairwise repulsion term**. Separation is *implicit*: the codebook term is k-means-like (each code pulled to the mean of its assigned residuals), so competing codes drift to distinct centroids. Redundancy *can* still happen, especially with an oversized codebook; in practice it is fought with *utilization* tricks (dead-code reset, EMA updates, k-means init, cosine/normalized codes), which target under-use/collapse rather than forbidding overlap. *(general RQ-VAE knowledge; not in this paper.)*

## Clarifier — what the RQ-VAE tokenizes, and what it does *not*

A tempting misreading is that one unified RQ-VAE discretizes *everything* — short-video embeddings, long-video embeddings, and search-query embeddings alike. That is not the design. Three different objects are handled three different ways:

- **Videos → RQ-VAE → SID.** The RQ-VAE (inherited from PLUM) is an *item / content* tokenizer: it maps a video's content embedding to a hierarchical SID. Both LFV and SFV videos are represented in a **single shared SID vocabulary** — which is precisely what lets their code usage *overlap* (about 40% on the first two prefixes); disjoint vocabularies could not overlap. So the "unified tokenizer across LFV and SFV" intuition is right *for videos*.
- **Search queries → native text tokens, not RQ-VAE.** A query is text, so it enters through the LLM's *existing text vocabulary* (the "shared token space inherited from a pre-trained LLM"), marked with a `<Search>` token and interleaved into the input. There is no "query embedding → RQ-VAE → SID" path; being able to use text *as text* is the whole point of reusing the LLM vocabulary, and quantizing the query would throw that away.
- **The user is never RQ-VAE'd at all.** There is no user-side autoencoder. A "user SID token" is simply a **coarse video-SID prefix that the decoder *generates*** for a predicted future watch (the training loss is defined over the *target watch's* SID codes). The user is discretized *by generation over the video-SID vocabulary*, not by quantizing a user embedding.

So "shared" has two nested meanings: the **RQ-VAE SID vocabulary** (videos only) sits *inside* the broader **shared LLM token space**, which also holds text tokens (search), scenario condition tokens (`<LFV>`/`<SFV>`), and bucketed/soft feature tokens. Only the first is an RQ-VAE.

## Method — Training the model (§3.2)

**Input tokenization.** Each watch becomes a small typed token group: its **prefix-$L$ video SID** as *hard* tokens, followed by that watch's side features. The paper's worked example is `A12 B278 C23 D77` (the $L=4$ SID prefix) followed by feature tokens like `100.0s` (watch time), `20%` (watch-time ratio / completion), and `IOS` (device platform). Non-SID features become either **hard tokens** (bucketing a dense value, or mapping a categorical/text field to a vocabulary) or **soft tokens** (embed each feature, concatenate, then project to $M$ embeddings via an MLP). So "concatenation" is the right picture, but the pieces are *typed* (hard vs soft), not raw values.

**Coarse prefix, restated.** RQ-VAE yields $L_{full} = 8$ codebook levels per video (one codeword per level); training keeps only the prefix-$L$ codes $(L < L_{full})$. The reason stated *here* is to **encourage diversity and mitigate memorization** — not "generalization," which was the separate head/tail argument for SID-over-VID in §3.1. Keep the two motivations distinct.

**Look-ahead target sampling — not next-item.** A cutoff timestamp $T$ splits the user's watches into a history before $T$ and a future window covering the 24 hours after $T$. Instead of predicting the immediate next watch, the model **randomly samples up to $N$ targets from that future window** and predicts them. Two payoffs, both matching the reading above:

- *Avoids overfitting to the immediate watch.* The very next click is often trivially tied to the previous one; sampling farther-ahead targets pushes the model to approximate genuine *near-future interests* rather than memorize the local continuation.
- *Training efficiency.* Predicting several targets per example beats one-target-per-example training.

**Loss (Eq. 1) — reward-weighted, decoder-only.** The objective is a cross-entropy over *only* the prefix-$L$ SID tokens of the sampled targets, each target weighted by an **engagement reward** $r(W_i)$ so high-value, diverse consumption counts more:

$$\mathcal{L} = -\sum_{i=1}^{N} r(W_i) \sum_{j=1}^{L} \log P(SID_{i,j} \mid W_1, \dots, W_t, W_{<i}, SID_{i,<j})$$

For efficiency the paper samples training examples *proportionally* to their reward and then weights them equally, instead of carrying explicit per-example weights.

**Where the dense embedding's supervision comes from.** Eq. 1 applies to *decoder outputs only*. The encoder receives gradients **solely through the decoder's cross-attention**, so the dense user embedding is never directly supervised — it is *implicitly* (weakly) trained to be whatever best supports accurate SID generation. This is worth flagging as a potential soft spot: the dense embedding is the backward-compatible output many downstream models actually consume, yet it carries **no loss term of its own** *(the "soft spot" is my inference)*.

## Method — Cross-scenario modeling and search interleaving (§3.3)

The base model is trained and served **independently per content scenario**; §3.3 folds LFV and SFV into one model.

**Why unify LFV and SFV.** The formats genuinely differ — SFV is consumed in continuous browsing with **no explicit click initiation** and a **stronger feedback loop**, unlike LFV. But interests are not isolated by format: **nearly half** of all users engage with *both* (nearly half, i.e. slightly under 50% — not a majority), and their SIDs overlap heavily — about **40%, specifically on the first two prefixes**. That overlap is the justification for one model, which buys efficiency, transfer learning, and a fuller view of preferences. The contributions quantify the efficiency: roughly **−50% training compute and −31% serving compute** versus separate models.

**§3.3.1 Unified training — two different roles, do not conflate them.**

- **LFV / SFV are the decoding contexts.** A discrete condition token (`<LFV>`, `<SFV>`) is prepended before *each watch*, so one chronologically-interleaved cross-scenario sequence stays disambiguated. Look-ahead target sampling (§3.2) is extended to draw future targets uniformly from both SFV and LFV. Condition tokens are **excluded from the loss** — predicting them is trivially easy and *degrades* SID quality if included.
- **Search is an input signal, NOT a decode domain** *(correcting a recurring slip)*. A `<Search>` token marks each of the $S$ most recent search queries, which are interleaved into the **input** sequence. The decoder never emits a "search SID"; search only enriches the input context. So there are exactly **two** decode contexts (LFV and SFV), not three. See the RQ-VAE Clarifier above.

**§3.3.2 Multi-context decoding — the serving trick.** A unified model must still emit scenario-specific tokens per context. The naive way reruns inference once per context, re-encoding the whole history and erasing the efficiency win. Instead: **one shared encoder pass** over the history, then a *context stage* branches decoding into **parallel sub-batches, one per target context**, each initialized with its own condition token and beam-searched independently, while **all sub-batches reuse the same cached encoder hidden states** (Fig. 3). One prefill, concurrent LFV + SFV generation.

**What the decoder emits is still a coarse interest region, not a specific item.** As in §3.1–§3.2, each generated user token is a **prefix-$L$ SID** naming an interest area, not one exact video. Multi-context decoding therefore produces *scenario-specific coarse interest tokens*, not concrete recommendations.

## Method — how a user's SID tokens are consumed downstream (§3.4)

Core tension: downstream LEM rankers need *dense vectors*, but SID tokens are *discrete*, so tokens are projected back to a continuous space.

1. **Generate.** Beam search over the decoder yields $B$ SID sequences per user, each a predicted future interest (coarse $L$-prefix).
2. **Token → embedding**, three methods: **Prefix Embedding Mapping** (static — map each prefix back to the mean-pooled content embeddings of videos sharing it), **N-gram**, and **SPM** (both are **Learnable Embeddings (LE)**: randomly-init tables trained end-to-end with the ranker).
3. **Aggregate** the $B$ embeddings by pooling — attention, mean, max, or top-$k$ concatenation. All pooling choices perform comparably, which the paper reads as the gain coming from the *token information itself*, not the aggregation.
4. **Ingest.** Both encoder dense embeddings and token-derived SID embeddings serve either as **direct input features** or as **key-value pairs in cross-attention** where candidate items attend over the user.

**Two axes of multiplicity (easy to conflate).** Per user there are $B$ predicted SID *sequences* (the beams), and within each sequence there are $L$ *codewords* (the prefix, e.g. $L=4$: `A12 B278 C23 D77`). They feed different steps: **N-gram / SPM tokenize the $L$ codewords *inside* one sequence** into sub-words (which are embedded and summed), whereas **pooling aggregates *across* the $B$ sequences** into one user vector. Consequence: N-gram and SPM stay meaningful even with a single beam, because one SID is still an $L$-codeword sequence to segment — they would collapse only if $L=1$.

**Subtlety *(my idea)*.** To be usable, the discrete tokens are ultimately projected back into a *dense* vector, so the ranker still eats a dense embedding — just one carrying SID-grounded, generatively-predicted *future-interest* content (and, for LE, trained end-to-end). Discreteness lives in the intermediate representation and the generation process, not at the ranker interface. This reframes the contribution as the *grounded, generative, sequence-derived content* of the vector.

**How the token → embedding map is trained — and what stays frozen** *(the reader's question)*. Method (1) is **static**: the prefix's vector is *precomputed* by mean-pooling content embeddings, a fixed lookup with **no training**. Methods (2) N-gram and (3) SPM are **Learnable Embeddings** — their randomly-initialized tables are **trained end-to-end with the downstream ranker**, so the supervision is simply the **ranker's own task loss**, exactly the reader's guess. Crucially, TokenMinds itself is **not** trained jointly here: per §3.5 its SID tokens and dense embedding are generated *asynchronously and cached*, and the ranker reads them as **fixed inputs**. So the only things learned at the downstream stage are the LE lookup tables (methods 2/3) plus the ranker; the encoder-decoder stays **frozen**. (Detail: N-gram *sums* fixed-length sub-word embeddings; SPM learns *variable-length* sub-words — the static-vs-LE comparison is deferred to §4.3.)

## Experiments

### The three research questions (§4)

Reassuringly, the questions that came out of the first read map almost exactly
onto the three RQs the paper itself sets up, which is a good sign that the
earlier sections framed the right tensions.

- **RQ1 — Token Adaptation & Viability.** This is really two sub-questions in
  one. *Adaptation*: how should the discrete SID user tokens be turned into
  something a downstream **continuous** ranker can consume — evaluated offline
  across the three token-to-embedding methods from §3.4 (Prefix Embedding
  Mapping, N-gram, SPM). *Viability*: do they then produce **measurable gains on
  industrial-scale surfaces** — answered by the online A/B in §4.3. So "how to
  integrate" and "does it actually pay off in production" are deliberately kept
  as separate burdens of proof.
- **RQ2 — Complementary Values.** Does the **dual output** genuinely pull its
  weight — i.e. does emitting a dense embedding *and* discrete SID tokens beat
  either one alone, showing the two carry complementary signal rather than
  redundant copies of the same user summary.
- **RQ3 — Cross-Scenario Modeling Impact.** Jointly training LFV and SFV in one
  unified model. The bet here is **two-sided**, and it is worth stating
  precisely: the claim is not merely "joint training does not hurt", but
  "**joint training buys a computational-efficiency gain** (one shared model /
  shared SID vocabulary instead of one per scenario) **without compromising**
  downstream recommendation quality". The risk being tested is negative transfer
  between the two very different video formats.

### §4.1 Setup — the numbers that matter

The concrete configuration is worth pinning down, because several of these
choices are exactly what the ablations later justify.

- **Input per user.** The most recent **1,200 watches**, interleaved with
  **$S = 10$** textual search queries (§3.3). Maximum input sequence length is
  **1,024 tokens**.
- **Per-watch token layout.** Each watch is encoded as one **condition token**
  (the `<LFV>`/`<SFV>` scenario marker) + the **prefix-$L = 4$** SID tokens +
  **$M = 1$** soft token that packs all the non-SID features. Using a single
  soft token trades away roughly **5% offline recall** in exchange for a large
  cut in sequence length — a deliberate length-versus-fidelity bargain.
- **Target.** Up to **$N = 15$** target watches sampled from a **24-hour
  look-ahead window** (not next-watch prediction — this is the look-ahead design
  the ablation shows is critical for cold-start).
- **Model.** Encoder-decoder built on **Gemini V1.5**: a **370M-parameter MoE
  encoder** plus a **370M-parameter dense decoder**, both initialized from
  **CPT** checkpoints.
- **Training.** Continuous daily training on the freshest data, ~millions of
  examples per day, which the paper frames as far more sample-efficient than
  traditional LEMs that need billions of interactions. Learning rate is
  grid-searched over $[10^{-6}, 10^{-3}]$; warmup + cosine decay with cyclic
  restarts peaks on same-day metrics, but a **constant LR is more robust** to
  day-to-day distribution shift under continuous training.
- **Serving.** Per user, extract a **1,152-dimensional dense embedding** from the
  encoder, and decode **$B = 40$** SID sequences by beam search — importantly
  split **20 LFV + 20 SFV** — each at prefix length $L$, to form the discrete
  user-token representation. Refresh cadence is **24 hours** (§3.5 async infra).

### §4.2 Representation Quality (RQ1, offline)

**Two accuracy protocols.** Both score the top-10 beam-searched SID sequences at
prefix-$L$ granularity, i.e. **Recall@10**.

- **Session Recall** — feed the near-complete history $[W_1, \dots, W_{n-1}]$ and
  predict the final watch $W_n$. This tests "given almost everything, do you nail
  the very next thing".
- **Cold-Start Recall** — feed a **truncated** history $[W_1, \dots, W_t]$ and
  predict a *randomly sampled* watch from the future $\{W_{t+1}, \dots, W_n\}$.
  This tests generalization from little history to a longer-horizon interest.

**Training ablation (Table 1).** Each row removes one design and confirms it
helps, and the pattern is informative — the two horizon-related choices matter
most for cold-start:

- **Multiple targets — $N = 15$ vs $N = 1$.** Sampling 15 look-ahead targets beats a
  single target: −8.9% Session / −3.3% Cold-Start when reduced to one.
- **Look-ahead window vs plain next-watch.** Replacing look-ahead sampling with
  standard next-watch prediction costs −4.5% Session but **−10.0% Cold-Start** —
  predicting a *window* of the future, not just the immediate next item, is what
  generalizes.
- **SID truncation — prefix-$L$ vs full $L_{full}$.** Training on full-length
  SIDs instead of the coarse prefix is the *most* damaging: −15.1% Session /
  **−17.1% Cold-Start**. Coarse interest regions generalize; fine full-SIDs
  memorize.

**Initialization + search (Table 2).** All deltas are relative to a *Random-init,
no-search* baseline. Two clean orderings fall out:

- **Init:** CPT > Pre-Trained Gemini > Random, consistently. The SID-specific
  semantic grounding baked in during CPT helps downstream fine-tuning beyond the
  base LLM's generic sequence modeling.
- **Search queries:** adding the $S = 10$ interleaved queries helps across *every*
  init, and the benefit is **amplified by stronger init** (CPT+search is best at
  +23.5% Session / +31.5% Cold-Start) — an aligned SID backbone is better able to
  fuse textual intent with behavioral history.

**Token diversity (Fig. 5) — the metric that needs unpacking.** Because each of
the $B = 40$ beams is supposed to be a *distinct* interest signal, beam collapse
(many beams converging to near-identical outputs) would waste representational
capacity. Two redundancy metrics check this:

- **SID Token Collision Rate at position $x$** — how often the code at a *single*
  level $x$ is identical across beams. High collision at a level = **semantic
  beam collapse** at that granularity.
- **SID Prefix Duplication Rate up to $x$** — the fraction of beams whose *entire*
  prefix path $[1 \dots x]$ is identical. High duplication = beams all walking one
  **single branch** of the SID tree (isolated exploration).

The distinction: token collision is per-level agreement (ignoring the rest of the
path); prefix duplication is whole-path agreement (stricter, and naturally falls
as $x$ grows because a longer path is harder to match exactly.)

Crucially the **benchmark is the ground truth, not zero redundancy.** Real future
behavior has natural repetition, so the goal is to *match reality*, not to
maximize spread. The comparison is **per user, between two SID sets**: for each
user, both metrics measure the *internal redundancy of a set* — computed once on
the **generated** set (that user's $B = 40$ decoded beams, i.e. decoding
diversity) and once on the **ground-truth** set (that user's actual watches in the
same 24-hour look-ahead window, converted to SIDs, i.e. the diversity of what the
user really consumed). Because a user's real-watch count is not $40$, the larger
set is down-sampled to the smaller (repeated 10× and averaged for fairness). The
per-user scores are then aggregated across 5K users into **CDFs**, and the
generated-side curve sits **on par with the ground-truth curve** — so the beams
are as diverse as the user's genuine consumption: neither collapsed nor
artificially over-spread.

### §4.3 Online Performance (RQ1 viability + RQ2 complementary)

Live 7-day A/B on production **ranking** models (TokenMinds is also in retrieval
and LLM systems, but this paper reports ranking). Two quality metrics on both
surfaces: **Engaged Users** and **Satisfied Engagement**; bold in the tables =
statistically significant at 95%.

**Token adaptation: LE beats fixed EM (answers the first half of RQ1).** A
lightweight 110M pivot on SFV compared the *static* **Prefix Embedding Mapping
(EM)** against a **Learnable Embedding (LE)** (Unigram, $N = 1$, matching that
surface's item tokenization):

| Strategy | Engaged Users | Satisfied Engagement |
| --- | --- | --- |
| EM (static) | +0.07% | −0.02% |
| LE (learnable) | +0.08% | **+0.22%** |

LE wins, and the gap is almost entirely on Satisfied Engagement (EM is even
slightly negative there) — letting the downstream model *learn* its own embedding
space adapts better than a frozen mapping. LFV with SPM-based LE showed the same
trend, so **LE is used for all full-scale runs**.

**Complementary value: Embed + Token is best (answers RQ1's second half + RQ2).**
Comparing continuous embedding alone, discrete SID tokens alone (via LE), and both
(Table 4):

| Surface | Representation | Engaged Users | Satisfied Engagement |
| --- | --- | --- | --- |
| SFV | Embed-only | 0.00% | +0.05% |
| SFV | Token-only | +0.04% | +0.40% |
| SFV | Embed+Token | **+0.11%** | **+0.62%** |
| LFV | Embed-only | +0.04% | +0.03% |
| LFV | Token-only | +0.01% | +0.04% |
| LFV | Embed+Token | +0.02% | +0.08% |

Two findings. First, **SID tokens carry additive value on their own** (token-only
already beats embed-only on Satisfied Engagement, dramatically so on SFV:
+0.40% vs +0.05%) — the latter half of RQ1. Two extra LFV surfaces confirmed
token-only generalizes (significant +0.04%/+0.16% Engaged, +0.07%/+0.11%
Satisfied). Second, **combining them amplifies the gain**, validating **RQ2**: on
SFV the effect is clean and monotone with Embed+Token best on both metrics
(+0.11% / +0.62%). On LFV the deltas are smaller and noisier (on Engaged Users,
embed-only is actually marginally ahead), but Embed+Token still tops Satisfied
Engagement — so the complementary story is strong on SFV and directionally
present, if weaker, on LFV.

### §4.4 Scaling Studies (partial — input length & batch size)

These use an **accelerated offline protocol**: train on 7 randomly shuffled days,
evaluate on the sequential **8th day** (so all numbers here are *8th-Day
Recall@10*).

**Input length (user history) scaling.** 8th-Day Recall@10 for both LFV and SFV
climbs as history grows but **saturates at roughly 1K watches**. Pushing to **2K**
gives only comparable or **slightly degraded** performance, and the degradation
shows up specifically on **SFV**. So longer history helps up to a point; past ~1K
there is no free lunch, which matters for compute-optimal sizing (the 1,024-token
input cap in §4.1 is consistent with this).

**Batch size scaling.** Batches of **4K / 8K / 16K**, with **8K as the tuned
anchor** and other sizes reached by scaling the learning rate via the standard
**$\sqrt{N}$ rule**. Relative to the 4K baseline, 8th-Day Recall@10 improves by
**+2.5% / +5.5% (SFV / LFV) at 8K** and **+7.6% / +13.7% at 16K**. Larger batches
accelerate convergence and yield stronger representations within the same training
window (consistent with PLUM), so the practical takeaway is to **max out batch
size up to hardware capacity**.

## Open questions / net read

- *(resolved by §4)* The gain is genuinely **complementary**, not redundant: token-only already beats embed-only on Satisfied Engagement (dramatically on SFV, +0.40% vs +0.05%), and Embed+Token amplifies it (SFV +0.11% / +0.62%) — validating RQ2. The ablations pin *why* the tokens generalize: the **look-ahead window** and **coarse prefix-$L$ truncation** are the two choices that most drive cold-start Recall (−10.0% and −17.1% when removed). The story is clean on SFV, weaker and noisier on LFV. (Details in the Experiments section above.)

**Net read:** well-framed and clearly motivated — the grounding and modality-gap arguments are sound, and dual-output backward compatibility is the pragmatic key to shipping. The claim it stands or falls on is empirical — that SID user tokens add *complementary* value on top of dense embeddings in production ranking — and §4 **does** deliver it on SFV (clean, monotone Embed+Token wins on both metrics), while the LFV evidence is directionally present but weaker and noisier. Net: the core thesis holds most convincingly where the feedback loop is strongest (SFV); the honest caveat is that the LFV gains are marginal.

<!-- To be continued: a few §4 sub-parts still unread — §4.2 Embedding Quality (cosine-consistency: Sim(E_A,E_A*)=0.993 within-user vs Sim(E_A,E_B)=0.761 across users); §4.3 Downstream Cost + Cross-Scenario/RQ3 (Table 5 integration overhead; Table 6: −50% training / −31% serving, +0.33%/+0.19% Fresh Engagement, 481 vs 698 chips); §4.4 Model Variants & Capacity Allocation (Balanced MoE vs Balanced Dense vs Unbalanced, Fig 6 iso-FLOPS, MoE decoder edge). -->
