<div align="center">

# General-purpose LLMs (zero-shot / prompted)

**18 papers · 6 baselines** — off-the-shelf chat models, no training

</div>

Frozen, **API-only** chat models prompted to rank / recommend. **No repo to clone** — implement the prompt + parsing pipeline yourself and call the vendor API. Keep prompts, few-shot examples, and output parsers in subfolders here.

> **Heads up:** results depend on prompt, model snapshot date, and decoding. Pin the model version and log prompts for reproducibility. Cost scales with the candidate set — sample or pre-rank before prompting.

| Baseline | Papers | Code path | Type |
|---|---:|---|---|
| GPT-4o | 4 | OpenAI API | API (no repo) |
| GPT-4o-mini | 3 | OpenAI API | API |
| GPT4 | 2 | OpenAI API | API |
| GPT-3.5-Turbo | 2 | OpenAI API | API |
| Claude 3.5 Haiku | 2 | Anthropic API | API |
| Gemini 2.5 Flash | 2 | Google API | API |

<sub>For LLMs used as *trained* recommenders (LoRA / RL / agents), see [`../llm_based/`](../llm_based/).</sub>
