# LettinGo: Explore User Profile Generation for Recommendation System

**Authors:** Lu Wang, Di Zhang, Fangkai Yang, Pu Zhao, Jianfeng Liu, Yuefeng Zhan, Hao Sun, Qingwei Lin, Weiwei Deng, Dongmei Zhang, Feng Sun, Qi Zhang

**arXiv:** https://arxiv.org/abs/2506.18309 (v1)

**PDF:** https://arxiv.org/pdf/2506.18309

**Venue:** 11 pages, 3 figures

**Categories:** cs.IR (primary), cs.AI

**Published:** 2025-06-23

---

<!-- Reading progress: the abstract and §1 introduction have been discussed and verified against the PDF. §2 and later sections have not yet been discussed. Statements are the paper's unless marked *(inference)*. -->

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

<!-- To be continued: continue with §2 after the reader shares their understanding. -->
