# TokenMinds: Pretrained User Tokens and Embeddings for User Understanding in Large Recommender Systems

**Authors:** Qingyun Liu, Bo Yan, Yang Liu, Yuji Roh, Ekansh Sharma, Likang Yin, Emma Olowo, Min-hsuan Tsai, Yuxuan Li, Diego Uribe, Saksham Aggarwal, Siqi Wu, Yuan Hao, Vikas Kedigehalli, Lukasz Heldt, Lichan Hong, Li Wei, Xinyang Yi

**arXiv:** https://arxiv.org/abs/2606.25147 (v1)

**PDF:** https://arxiv.org/pdf/2606.25147

**Venue:** —

**Categories:** cs.IR (primary), cs.AI, cs.LG

**Published:** 2026-06-23

---

<!-- Reading progress: abstract, §1–§2, §3.1–§3.2 and §3.4–§3.5. §3.3 (cross-scenario) and §4 (experiments) still to read. Verified against the PDF. Statements are the paper's unless marked (inference) or (open). -->

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
- **Encoder-decoder, not decoder-only** (§3.1). The **encoder** captures full-history sequential patterns and the dense embedding is pooled off its contextualized outputs (last-token / mean); the **decoder** autoregressively generates the SID user tokens. Bonus: encoder/decoder can be **decoupled at serving** — heavy low-frequency encoder for long history, light high-frequency decoder for recent behavior. Both are initialized from PLUM's CPT.
- **Shared SID vocabulary** unifies long-form and short-form video in one model, cutting cost.
- **Serving (§3.5).** Representations are generated **asynchronously** and cached in a KV store; real-time scoring reads the cache (constant latency/cost); a background Refresh Service regenerates on expiry/miss.

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

## Method — how a user's SID tokens are consumed downstream (§3.4)

Core tension: downstream LEM rankers need *dense vectors*, but SID tokens are *discrete*, so tokens are projected back to a continuous space.

1. **Generate.** Beam search over the decoder yields $B$ SID sequences per user, each a predicted future interest (coarse $L$-prefix).
2. **Token → embedding**, three methods: **Prefix Embedding Mapping** (static — map each prefix back to the mean-pooled content embeddings of videos sharing it), **N-gram**, and **SPM** (both are **Learnable Embeddings (LE)**: randomly-init tables trained end-to-end with the ranker).
3. **Aggregate** the $B$ embeddings by pooling — attention, mean, max, or top-$k$ concatenation. All pooling choices perform comparably, which the paper reads as the gain coming from the *token information itself*, not the aggregation.
4. **Ingest.** Both encoder dense embeddings and token-derived SID embeddings serve either as **direct input features** or as **key-value pairs in cross-attention** where candidate items attend over the user.

**Subtlety *(my idea)*.** To be usable, the discrete tokens are ultimately projected back into a *dense* vector, so the ranker still eats a dense embedding — just one carrying SID-grounded, generatively-predicted *future-interest* content (and, for LE, trained end-to-end). Discreteness lives in the intermediate representation and the generation process, not at the ranker interface. This reframes the contribution as the *grounded, generative, sequence-derived content* of the vector.

## Open questions / net read

- *(open)* Where does the measured gain over a plain dense user embedding actually come from — generative future-interest prediction, content grounding, or multi-interest coverage from the $B$ sequences? (§4 should answer.)
- *(open)* §3.2 exact training objective (target-watch SID token loss + how the dense embedding is supervised) and §3.3 cross-scenario / search-query interleaving.

**Net read so far:** well-framed and clearly motivated — the grounding and modality-gap arguments are sound, and dual-output backward compatibility is the pragmatic key to shipping. The claim it stands or falls on is empirical: that SID user tokens add *complementary* value on top of dense embeddings in production ranking, which §4 must demonstrate.

<!-- To be continued: read §3.2 training objective, §3.3 cross-scenario / search extensions, then §4 experiments. -->
