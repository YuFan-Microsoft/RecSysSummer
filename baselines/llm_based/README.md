<div align="center">

# LLM-based recommenders

**41 papers · 20 baselines** — recommend by fine-tuning / prompting an LLM

</div>

LLMs adapted for recommendation via **LoRA fine-tuning**, **DPO/RL alignment**, or **agent/prompt** pipelines. Clone each method's **own repo**. Five ship **native Amazon-2023** code (`ReaRec` lives in the sequential family): **R²ec · Rec-R1 · MiniOneRec** (generative family) plus the LoRA methods below.

> **Heads up:** most need a 7B-class base model and ≥ 1 GPU (often 4–8). API-only rankers (`LLMRank`, `AgentCF`) cost money at scale.

| Baseline | Papers | Code path | Type | Run on Amazon-2023 |
|---|---:|---|---|---|
| [S-DPO](https://arxiv.org/abs/2406.09215) | 7 | [chenyuxin1999/S-DPO](https://github.com/chenyuxin1999/S-DPO) | Official | LoRA+DPO, 4-GPU |
| [TALLRec](https://arxiv.org/abs/2305.00447) | 7 | [SAI990323/TALLRec](https://github.com/SAI990323/TALLRec) | Official | LLaMA-7B LoRA, 1-GPU |
| [BIGRec](https://arxiv.org/abs/2308.08434) | 6 | [SAI990323/BIGRec](https://github.com/SAI990323/BIGRec) | Official | LoRA (data 2018→2023) |
| [LLaRA](https://arxiv.org/abs/2312.02445) | 6 | [ljy0ustc/LLaRA](https://github.com/ljy0ustc/LLaRA) | Official | LoRA (train CF backbone first) |
| [D3](https://arxiv.org/abs/2406.14900) | 5 | [SAI990323/DecodingMatters](https://github.com/SAI990323/DecodingMatters) | Official | Qwen2-0.5B LoRA, 1-GPU |
| [RLMRec](https://arxiv.org/abs/2310.15950) | 4 | [HKUDS/RLMRec](https://github.com/HKUDS/RLMRec) | Official | LLM inference + CF training |
| [AlphaRec](https://arxiv.org/abs/2407.05441) | 4 | [LehengTHU/AlphaRec](https://github.com/LehengTHU/AlphaRec) | Official | frozen LLM emb + MLP/GCN |
| [LLMRank](https://arxiv.org/abs/2305.08845) | 3 | [RUCAIBox/LLMRank](https://github.com/RUCAIBox/LLMRank) | Official | OpenAI API zero-shot |
| [AgentCF](https://arxiv.org/abs/2310.09233) | 3 | [RUCAIBox/AgentCF](https://github.com/RUCAIBox/AgentCF) | Official | GPT-4 API (expensive at scale) |
| [KAR](https://arxiv.org/abs/2306.10933) | 3 | [YunjiaXi/Open-World-Knowledge-Augmented-Recommendation](https://github.com/YunjiaXi/Open-World-Knowledge-Augmented-Recommendation) | Official | LLM knowledge + small CF |
| [RLMRec-Con](https://arxiv.org/abs/2310.15950) | 3 | [HKUDS/RLMRec](https://github.com/HKUDS/RLMRec) | Official (variant) | same as RLMRec |
| [RLMRec-Gen](https://arxiv.org/abs/2310.15950) | 3 | [HKUDS/RLMRec](https://github.com/HKUDS/RLMRec) | Official (variant) | same as RLMRec |
| [InteRecAgent](https://arxiv.org/abs/2308.16505) | 3 | [microsoft/RecAI](https://github.com/microsoft/RecAI) (`InteRecAgent/`) | Official | GPT-4 API + tools |
| [R2ec](https://arxiv.org/abs/2505.16994) | 3 | [YRYangang/RRec](https://github.com/YRYangang/RRec) | Official·2023 | native (4-GPU RL) |
| [LLMInit](https://arxiv.org/abs/2503.01814) | 2 | [DavidZWZ/LLMInit](https://github.com/DavidZWZ/LLMInit) | Official | frozen-LLM init for RecBole CF |
| [LLM-ESR](https://arxiv.org/abs/2405.20646) | 2 | [liuqidong07/LLM-ESR](https://github.com/liuqidong07/LLM-ESR) | Official | adapt |
| [Chat-Rec](https://arxiv.org/abs/2303.14524) | 2 | — | ❌ no official repo | implement from paper (prompt) |
| [Rec-R1](https://arxiv.org/abs/2503.24289) | 2 | [linjc16/Rec-R1](https://github.com/linjc16/Rec-R1) | Official·2023 | native (PPO via veRL) |
| [LLM-Rec](https://arxiv.org/abs/2307.15780) | 2 | — | ❌ no official repo | implement from paper (prompt) |
| [LlamaRec](https://arxiv.org/abs/2311.02089) | 2 | [Yueeeeeeee/LlamaRec](https://github.com/Yueeeeeeee/LlamaRec) | Official | LoRA (Llama-2) |
