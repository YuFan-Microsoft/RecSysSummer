# 从 Topic 到交互式论文阅读计划：完整流程

## 1. 目标

这个流程把用户给出的研究 topic 转换成一个可直接打开的交互式 HTML：

- 先决定调用 Paper Finder、arXiv Finder，或同时调用两者；
- 所有 API query 使用英文；
- 从一个宽泛 query 开始，基于结果不断裂变新的 query；
- 对候选论文去重、分层、分类，并建立推荐阅读顺序；
- 生成包含搜索、进度、笔记、摘要和研究空白的独立 HTML。

对应的个人 Copilot skill 已安装到：

```text
~/.copilot/skills/paper-reading-plan/
```

Skill 名称：

```text
paper-reading-plan
```

## 2. 两个检索端点

### 2.1 Paper Finder

- 当前示例 URL：`https://5a814d55d33d77ac88.gradio.live/`
- 实现代码：`/Users/yufzhao/Desktop/RecSysSummer/paper_search_engine`
- 输入：英文 research idea、top-K。
- 数据：精选 Markdown 论文库。
- 检索：Qwen embedding recall，再用 Qwen reranker 重排。
- 特点：检索阶段使用论文的核心章节，但展示时可返回完整论文分析。
- 适合：推荐系统、semantic IDs、generative retrieval、多模态推荐、电商搜索等主题。

### 2.2 arXiv Finder

- 当前示例 URL：`https://290153a7edde7b4837.gradio.live/`
- 实现代码：`/Users/yufzhao/Desktop/RecSysSummer/arxiv_search_engine`
- 输入：英文 query、domain、years、sort、top-K。
- 数据：2020-2026 arXiv title + abstract metadata。
- 检索：选择 domain shard，按年份过滤，embedding recall，reranker 重排。
- 输出字段：title、abstract、authors、year、citation count、arXiv URL 等。
- 适合：广泛、近期、跨方向的学术检索。

> `gradio.live` 地址会轮换。Skill 优先读取 `PAPER_SEARCH_URL` 和
> `ARXIV_SEARCH_URL`，也可以在调用脚本时显式传入 `--url`。

## 3. 为什么不能只调用一次公开 API

Gradio 的公开 `do_search` API 直接返回：

- 左侧结果列表的截断 label；
- 当前第一篇论文的完整 Markdown。

完整结果对象被放在 `gr.State` 中，因此简单 HTTP 调用看不到其他论文的
完整 title 和 abstract。

解决方案是使用官方 `gradio_client.Client`：

1. 在同一个 client session 中调用 `/do_search`；
2. 保留相同的 session state；
3. 对结果索引逐个调用 `/on_select`；
4. 取回每一篇论文的完整 Markdown；
5. 解析为结构化 JSON。

Skill 内置脚本：

```text
scripts/gradio_search.py
```

示例：

```bash
uv run --with gradio_client python scripts/gradio_search.py \
  --kind arxiv \
  --url "$ARXIV_SEARCH_URL" \
  --query "recent advances in text embedding models" \
  --domain Computer_Science \
  --years 2024 2025 2026 \
  --top-k 20 \
  --output results/01-landscape.json
```

## 4. API 选择逻辑

### 只用 arXiv Finder

适用于通用、近期、需要广覆盖的主题，例如：

- embedding models；
- reasoning-aware retrieval；
- diffusion models；
- multilingual encoders。

### 只用 Paper Finder

适用于明确要求从精选论文库推荐，或需要完整论文分析的主题。

### 两个都用

适用于：

- recommender systems；
- semantic IDs；
- generative retrieval；
- multimodal recommendation/search；
- e-commerce；
- user/item representation。

arXiv Finder 提供广度和结构化 metadata，Paper Finder 补充经过整理的研究
脉络与应用视角。

## 5. Query 裂变

### 5.1 第一层：宽泛 landscape

先把用户 topic 改写成一个准确的英文 query。例如：

```text
recent advances in text embedding models for retrieval and representation learning
```

### 5.2 第二层：从命中结果识别主分支

阅读 titles 和 abstracts 后，提取不同研究轴：

- architecture；
- supervision 和 synthetic data；
- hard negatives 和 distillation；
- multilingual / low-resource；
- sparse、dense、multi-vector、late interaction；
- long-context；
- reasoning-aware retrieval；
- efficiency、Matryoshka、quantization；
- multimodal / omni-modal；
- benchmarks、robustness 和 contamination；
- code、science、biomedicine、recommendation 等 specialization。

每个轴生成一个独立英文 query，而不是把所有关键词塞进同一个 query。

### 5.3 第三层及以后：根据新结果继续裂变

新结果可能暴露更细方向，例如：

- LLM-to-embedder architecture；
- embedding geometry 和 calibration；
- agentic retrieval；
- visual-document retrieval；
- unified embedding/reranking；
- routed experts；
- binary / low-bit embeddings。

继续为缺失方向、争议点、counterpoint 和 benchmark 生成 query。

### 5.4 停止条件

- 每个重要子类已有约 4-6 篇差异明确的论文；
- 新 query 大部分只返回重复论文；
- 已包含核心方法、counterpoint、evaluation 和部署视角；
- 新结果不再改变整体 taxonomy。

## 6. 去重与策展

### 6.1 去重

- 只在去重时移除 arXiv ID 尾部的 `v1`、`v2`、`v3`；
- 同一论文同时出现在两个 API 时，优先使用 arXiv Finder 的结构化 metadata；
- 保留原始 title、authors、abstract、year、citation count 和 URL。

### 6.2 选论文

不是简单取 rerank top-K，也不是按 citations 排序。LLM 逐篇判断：

- 是否代表方法转折点；
- 是否提供新的训练或架构设计；
- 是否是重要 counterpoint；
- 是否提供真实部署或效率证据；
- 是否代表 2025-2026 的新方向；
- 是否和同类论文重复。

### 6.3 层级和阅读顺序

最终结构为：

```text
Major phase
  -> Sub-cluster
       -> Globally ordered papers
```

每篇论文分配一个 role：

- `Start`
- `Core`
- `Deep Dive`
- `Frontier`
- `Counterpoint`

阅读顺序依据概念依赖与争议结构，而不是搜索排名。

### 6.4 Citations

Citation count 只作为粗略、随时间变化的 impact signal，不能代表论文质量。
新论文即使 citation 很低，只要代表新的研究方向，也应保留。

### 6.5 单位信息

最终要求已撤回，因此当前 skill 和 HTML 默认不包含作者单位或公司标签。
只有用户未来再次明确要求时才加入。

## 7. Embedding Models 示例

Topic：

```text
最近两年 embedding model 的进展
```

由于 API 只支持年份过滤，本次把“最近两年”近似为：

```text
2024, 2025, 2026
```

检索过程：

- 共 25 个英文 query 分支；
- 两个 API 配合；
- 约 300 个候选结果；
- 去重并策展为 82 篇论文；
- 7 个 major phases；
- 18 个 sub-clusters。

最终阶段包括：

1. Orienting the Field and Rebuilding the Embedder
2. Supervision, Adaptation, and Embedding Geometry
3. Languages, Interaction, Experts, and Unified Ranking
4. Long Context, Reasoning, and Agentic Retrieval
5. Elastic Embeddings and Deployment Economics
6. Visual, Omni-Modal, and Domain-Specialized Spaces
7. Evaluation, Robustness, Attacks, and Open Problems

最终 HTML：

```text
/Users/yufzhao/Desktop/embedding_models_reading_plan.html
```

## 8. HTML 功能

- major phase 和 sub-cluster 分层；
- 全局推荐阅读顺序；
- year、citations、role、arXiv 链接；
- `why_read`；
- authors 和可展开 abstract；
- 全文搜索；
- 总体、phase、cluster 阅读进度；
- 本地笔记；
- `localStorage` 持久化；
- key debates；
- query branching 记录；
- `where_to_push` 研究方向；
- responsive layout；
- dark mode。

通用渲染脚本：

```text
scripts/render_reading_plan.py
```

Plan JSON 设置 `locale: "en"` 或 `locale: "zh-CN"` 后，HTML 控件也会使用
对应语言。Paper Finder-only 论文如果没有 arXiv ID，会保留稳定的 `paper_id`；
缺失年份或 citations 时显示“不可用”，不会伪装成零引用。

## 9. 验证

每次生成前后检查：

1. 所有 JSON 可以解析；
2. paper order 从 1 连续递增；
3. normalized arXiv ID 不重复；
4. 每个 phase/cluster 引用都能解析；
5. 所有 selected paper 都来自实际 API result；
6. HTML 可以解析；
7. 内嵌 JavaScript 可以编译；
8. 最终文件已写到用户指定位置。

Skill 使用统一验证器完成前七项：

```bash
SKILL_DIR="${COPILOT_HOME:-$HOME/.copilot}/skills/paper-reading-plan"
uv run python "$SKILL_DIR/scripts/validate_plan.py" \
  --plan artifacts/reading_plan.json \
  --query-manifest artifacts/query_manifest.json \
  --result-files results/*.json \
  --html artifacts/reading_plan.html
```

## 10. 使用 Skill

自然触发：

```text
帮我研究最近两年 reasoning-aware retrieval 的进展，并生成阅读计划。
```

显式触发：

```text
Use the /paper-reading-plan skill to research multimodal generative retrieval.
```

新增 skill 后，在当前 Copilot CLI 会话执行：

```text
/skills reload
```

查看信息：

```text
/skills info paper-reading-plan
```
