# SIDReasoner 内置 `verl` 的定制改动清单（verl_patch）

> 目的：记录本仓库 `baselines/generative_semantic_id/SIDReasoner/verl/` 相对上游
> [`volcengine/verl`](https://github.com/volcengine/verl) 的**全部定制改动**，作为将来升级 / 移植到新版 verl（以及更高
> torch + vllm）的 patch 依据。
>
> 调查日期：2026-07-08

---

## 0. TL;DR

- 内置 `verl` 是 **上游 verl `0.4.1.dev` 的完整 vendored 源码副本 + 若干 SID/推荐专用改动**（fork，不是纯 copy，也不是重写）。
- 依赖被锁死的**根约束是 verl**，不是 torch：
  - verl 深度 monkey-patch / 调用了 vllm 内部 API ⇒ 锁 `vllm==0.8.5.post1`
  - vllm 官方 wheel 的 ABI 绑定 ⇒ 锁 `torch==2.6.0`（+ torchvision 0.21.0 / torchaudio 2.6.0）
  - torch 版本 ⇒ 锁 `flash-attn` / `flashinfer` 的 `cu124torch2.6` 预编译 wheel
- 真正需要移植的定制只有 **一处重（rollout beam search）+ 一处轻（naive.py 注入 num_turns）+ 5 个新文件**；其余全是外部 config/CLI 注入，不算 verl 源码 diff。

---

## 1. 版本基线

| 项 | 值 | 来源 |
|---|---|---|
| verl 版本 | `0.4.1.dev` | `verl/version/version` |
| 版权头 | `Copyright 2024 Bytedance Ltd.` | `verl/__init__.py` |
| 目录树 | 完整（`single_controller/` `experimental/` `models/mcore/` `trainer/` `workers/` …） | 说明是完整 vendored 源码 |

> 注意：`verl/experimental/dataset/sampler.py`、`verl/models/mcore/*.py` 里出现的
> `Copyright 2025 Amazon.com Inc` 是 **上游 verl 自带的 Amazon 贡献代码**，
> **不是**本项目的定制，不要误判。

---

## 2. 为什么依赖被锁死（约束链）

```
VERL (RL 框架, Stage 3)
  └─ 深度调用 / patch vllm 内部 rollout & 权重同步 API
       └─ vllm==0.8.5.post1        (verl 版本白名单校验 + beam_search API)
            └─ torch==2.6.0        (vllm wheel 的 C++/CUDA ABI 绑定)
                 └─ flash-attn 2.7.4.post1 / flashinfer 0.2.2.post1
                      (cu124torch2.6 预编译 wheel, 文件名写死)
```

相关证据文件：
- `scripts/install_vllm_sglang_mcore.sh`：torch / vllm / flash-attn / flashinfer 版本在同一套安装脚本里咬合。
- `verl/third_party/vllm/__init__.py`：显式做 vllm 版本白名单（`Currently supported vllm versions are 0.7.0+`）。
- `verl/workers/rollout/vllm_rollout/__init__.py`：按 vllm 版本号切换 rollout 后端。
- `verl/workers/sharding_manager/fsdp_vllm.py`：`VLLMHijack` / `patch_vllm_moe_model_weight_loader`（直接 hack vllm 内部）。

Stage 1 / 2（SFT + 评估）其实只需要 torch + transformers；vllm 完全是 Stage 3 RL 才引入的。

---

## 3. 完整 diff 清单

### A. 新增文件（上游没有）

| 文件 | 作用 |
|---|---|
| `verl/utils/reward_score/direct_recommendation_StepRule_Games.py` | SID 推荐 reward（Games 域），含 `prefix_map` 合法性校验 |
| `verl/utils/reward_score/direct_recommendation_StepRule_Industrial.py` | 同上（Industrial_and_Scientific 域） |
| `verl/utils/reward_score/direct_recommendation_StepRule_Office.py` | 同上（Office_Products 域） |
| `verl/utils/reward_score/recommend.py` | **第 4 个 reward 文件**：`data_source=="recommendation"` 打分入口 + 工具调用惩罚 |
| `verl/tools/rec_tool.py` | `RecTool(BaseTool)`：模拟用户的推荐器工具，加载 `embedding_path` 的 item embedding |

`recommend.py` 核心逻辑：

```python
def compute_score(data_source, solution_str, ground_truth, extra_info=None,
                  format_score=0.05, score=1.0, tool_penalty_lambda=0.6):
    if data_source == "recommendation":
        answer = extract_solution(solution_str=solution_str)   # 取最后一个 <answer>...</answer>
        if answer is None:
            return 0
        if ground_truth in answer:
            num_tool_calls = extra_info.get("num_turns", 0) or 0
            # 每次工具调用都乘一个惩罚因子
            return score * (tool_penalty_lambda ** num_tool_calls)
        return format_score
    raise ValueError(f"Unsupported data source: {data_source}")
```

---

### B. 被修改的核心文件（真正和 verl 内核纠缠的）

#### B.1 `verl/workers/rollout/vllm_rollout/vllm_rollout_spmd.py` —— 改动最重、最危险

全部为了 **SID 约束 beam search**。升级 vllm 时这里最容易炸（绑死了 vllm 的
`beam_search` / `BeamSearchParams` API）。

具体插入：

1. 新增 import（约 L48）
   ```python
   from vllm.sampling_params import BeamSearchParams
   ```

2. 新增 helper `truncate_at_end_think()`（约 L79）
   - 在 token 序列末尾 `clip_chars` 范围内找 `</think>\n` marker（默认 `[151668, 271]`），截断到 marker 处。

3. 新增 helper `extract_content_after_think()`（约 L107）
   - 取 `</think>` 之后的文本（限制在末尾 `_SOLUTION_CLIP_CHARS=100` 字符内）。

4. 新增函数 `vllm_beam_search_concat()`（约 L118）
   - 用 `BeamSearchParams(beam_width, max_tokens=depth, temperature=0.0, length_penalty=0.0)`
     调 `llm.beam_search(prompts, beam_params)`，把每个 prompt 的多条 beam 用
     `sep="<|beam_sep|>\n"` 拼成一条字符串返回。

5. `__init__` 里新增（约 L305–L313）
   ```python
   self.tokenizer = tokenizer
   self.truncate_marker = self.tokenizer.encode("</think>\n\n")
   self.activate_beam_search = ("sid_beam_size" in config) and ("sid_length" in config) and (config.sid_beam_size > 1)
   if self.activate_beam_search:
       self.sid_beam_size = config['sid_beam_size']
       self.num_sid_tokens = config['sid_length']
   ```

6. `generate_sequences()` 里新增 beam-search 分支（约 L444–L467）
   ```python
   if self.activate_beam_search:
       response_ids_truncated = truncate_at_end_think(response_ids, marker=self.truncate_marker, clip_chars=20)
       response_reasonings.append(response_ids_truncated)
   ...
   if self.activate_beam_search:
       input_prompt_ids = [vllm_inputs[i]['prompt_token_ids'] + response_reasonings[i] for i in range(batch_size)]
       response_beam_search = vllm_beam_search_concat(
           self.inference_engine, self.tokenizer,
           prompts_ids=input_prompt_ids,
           params=self.sampling_params.__copy__(),
           beam_width=self.sid_beam_size,
           depth=self.num_sid_tokens,
       )
       non_tensor_batch['beam_search_results'] = np.array(response_beam_search)
   ```
   > 产出的 `non_tensor_batch['beam_search_results']` 在 verl 之外（评估脚本）被消费。

#### B.2 `verl/workers/reward_manager/naive.py` —— 已和上游 v0.4.1 逐行核对，确认被改

- **上游 v0.4.1**：
  ```python
  extra_info = data_item.non_tensor_batch.get("extra_info", None)
  score = self.compute_score(
      data_source=data_source, solution_str=response_str,
      ground_truth=ground_truth, extra_info=extra_info,
  )
  ```
- **本 fork**（约 L78–L80）：
  ```python
  extra_info = data_item.non_tensor_batch.get("extra_info", {})   # 默认 None -> {}
  num_turns = data_item.non_tensor_batch.get("__num_turns__", None)
  extra_info["num_turns"] = num_turns                              # 新增注入
  ```
- 作用：把工具调用轮数 `__num_turns__` 喂给 `recommend.py` 做惩罚。
- ⚠️ **移植时极易遗漏**：漏了这一处，`recommend.py` 的工具惩罚（`tool_penalty_lambda ** num_turns`）就会永远按 0 轮算，等于失效。

---

### C. 调试残留（不是功能，是手改工作副本留下的痕迹）

| 位置 | 说明 | 建议 |
|---|---|---|
| `verl/utils/reward_score/gsm8k.py` L65 | **未注释的 `breakpoint()`**，会卡住 gsm8k 打分 | 删除（本项目不走 gsm8k 所以没炸，但是实打实的遗留 bug） |
| `verl/trainer/main_ppo.py` L223 / L244 | 已注释 `# breakpoint()` | 可清理 |
| `verl/trainer/ppo/ray_trainer.py` L739 / L919 / L1099 / L1173 | 已注释 `# breakpoint()` | 可清理 |
| 3 个 `StepRule_*` L143 | 已注释 `# breakpoint()` | 可清理 |
| `vllm_rollout_spmd.py` L466 / L469 | 已注释 `# breakpoint()` | 可清理 |

这些散落的 breakpoint 说明该 `verl/` 是**被手工改过的工作副本**，不是干净的 pip 安装。

---

### D. 注意：这些「不是」verl 源码 diff（走外部注入，别去 verl 里找）

- `sid_beam_size` / `sid_length`：**没有**改 verl 任何 yaml，是训练脚本用命令行
  override 注进去的（所以 `("sid_beam_size" in config)` 是软判断）。
- `rec_tool` 的注册：不在 verl 默认 tool config 里，由项目级外部 tool config yaml 挂载。
- `recommend.py` / `StepRule_*` 的调用：`verl/utils/reward_score/__init__.py` 的
  `default_compute_score` **没有**加 `"recommendation"` 分支（会 `raise NotImplementedError`），
  是通过 `custom_reward_function` 外部挂的 ⇒ `__init__.py` 本身没被改。

---

## 4. 升级到新版 verl + 更高 torch/vllm 的评估

**结论：不是「版本号 +1」，而是一次「移植 + 重新验证」的工程。**

风险点：
1. B.1 的 beam search 补丁落在 `vllm_rollout_spmd.py` —— 这是 verl 里跟 vllm 内部
   API 耦合最紧、上游重构最频繁的文件。新版 verl（0.5.x / 0.6.x+）已大幅重写 rollout
   （engine 抽象 / async rollout），补丁无法干净 apply。
2. 补丁依赖 vllm 的 `llm.beam_search()` + `BeamSearchParams`，该 API 在 vllm 版本间被
   改过 / 弱化过。升 vllm 可能直接弄坏 SID 约束生成。
3. 复现性：baseline / 论文结果是用这套锁定栈跑的，升级会引入静默的数值 / 行为差异。

建议：
- **只想复现 / 跑 baseline** → 保持锁定栈（verl 0.4.1.dev + vllm 0.8.5.post1 + torch 2.6.0），别动。
- **确实被硬件或新特性卡住**（如新卡需要更高 torch/vllm）→ 才做移植。

---

## 5. 移植 Checklist（搬到新版 verl 时照做）

- [ ] 拉取目标新版 verl 完整源码。
- [ ] **A. 直接搬 5 个新文件**（几乎原样）：
  - [ ] `verl/utils/reward_score/direct_recommendation_StepRule_Games.py`
  - [ ] `verl/utils/reward_score/direct_recommendation_StepRule_Industrial.py`
  - [ ] `verl/utils/reward_score/direct_recommendation_StepRule_Office.py`
  - [ ] `verl/utils/reward_score/recommend.py`
  - [ ] `verl/tools/rec_tool.py`（注意适配新版 `BaseTool` 接口签名）
- [ ] **B.2 重打 naive.py 补丁**（1 处，简单）：注入 `extra_info["num_turns"] = ...get("__num_turns__")`。
      注意确认新版 reward manager 是否已原生支持 `num_turns`，若已支持则可省。
- [ ] **B.1 移植 beam search（主要工作量，难）**：
  - [ ] 把 `truncate_at_end_think` / `extract_content_after_think` / `vllm_beam_search_concat` 三个 helper 搬过去。
  - [ ] 在新版 rollout 的 `__init__` / `generate_sequences` 找到对应位置重新接线。
  - [ ] **适配新版 vllm 的 beam search API**（确认 `llm.beam_search` / `BeamSearchParams` 是否仍存在、签名是否变化）。
  - [ ] 确认 `non_tensor_batch['beam_search_results']` 的下游消费方（评估脚本）仍能对接。
- [ ] **C. 清理调试残留**：删掉 `gsm8k.py` 里未注释的 `breakpoint()`，清理其余 `# breakpoint()`。
- [ ] **D. 外部注入不用改 verl**：确认训练脚本仍通过 CLI override 传 `sid_beam_size`/`sid_length`，
      tool config 仍挂 `rec_tool`，reward 仍通过 `custom_reward_function` 指向 `recommend.py` / `StepRule_*`。
- [ ] **重新验证指标对齐**（关键：确认迁移后结果与原锁定栈一致）。

---

## 6. 附：涉及文件索引

新增：
- `verl/utils/reward_score/recommend.py`
- `verl/utils/reward_score/direct_recommendation_StepRule_Games.py`
- `verl/utils/reward_score/direct_recommendation_StepRule_Industrial.py`
- `verl/utils/reward_score/direct_recommendation_StepRule_Office.py`
- `verl/tools/rec_tool.py`

修改：
- `verl/workers/rollout/vllm_rollout/vllm_rollout_spmd.py`（beam search，重）
- `verl/workers/reward_manager/naive.py`（注入 num_turns，轻）

调试残留：
- `verl/utils/reward_score/gsm8k.py`（未注释 breakpoint）
- `verl/trainer/main_ppo.py` / `verl/trainer/ppo/ray_trainer.py` / 3 个 StepRule（已注释 breakpoint）

---

## 7. 版本对比：为什么选 v0.6.0（而不是 v0.7.0）

调查了 v0.6.0 与 v0.7.0 两个 tag，结论是 **v0.6.0 是甜点版本**。

| 关键点 | v0.4.1（原 fork） | **v0.6.0（已采用）** | v0.7.0 |
|---|---|---|---|
| SPMD 同步 rollout | ✅ `vllm_rollout_spmd.py` | ✅ 仍在 `vllm_rollout_spmd.py` | ❌ 退役（PR #4411） |
| `generate_sequences` 同步生成 | ✅ | ✅ 正常 | ❌ `raise NotImplementedError` |
| `inference_engine` 类型 | vllm `LLM` | ✅ vllm `LLM`（`.beam_search()` 可用） | `WorkerWrapperBase`（无 beam_search） |
| `beam_search` / `BeamSearchParams` | 有 | ✅ 可用 | ❌ 全仓库 NONE |
| B.2 `num_turns` 注入 | 需手打 | ✅ **已原生** | ✅ 已原生 |
| vllm 支持范围 | 0.7.0+（锁 0.8.5） | ✅ 0.7.0+ / 0.8.5+ 分支 | 0.7.0+ / 0.8.5+ |

> v0.7.0 把整个 vLLM SPMD 同步 rollout 退役了，`beam_search` API 全仓库消失，
> SID beam search 需在 async server 架构上从零重写——因此**不选** v0.7.0。

---

## 8. 移植执行记录（已完成 → `verl/`，基于 v0.6.0）

> 目标目录：`baselines/generative_semantic_id/SIDReasoner/verl/`
> （只含 `verl/` 子文件夹的 v0.6.0，浅克隆无 `.git`）。执行日期：2026-07-08。

### 8.1 已应用的改动

| 改动 | 状态 | 说明 |
|---|---|---|
| A. 4 个 reward 文件 | ✅ 原样复制 | `recommend.py` + 3 个 `StepRule_*`，自包含无接口依赖 |
| A. `rec_tool.py` | ✅ **已适配** | 见 8.2，接口从 0.4.1 迁到 0.6.0 |
| B.1 beam search | ✅ 已移植 | `vllm_rollout_spmd.py`：import + 3 helper + `__init__` + `generate_sequences` 分支 |
| B.1 配置字段 | ✅ **新增** | `RolloutConfig` 加 `sid_beam_size` / `sid_length`，见 8.2 |
| B.2 naive.py num_turns | ⏭️ **跳过** | v0.6.0 已原生（`naive.py` L84-86），无需打补丁 |
| C. 调试残留 | ✅ 天然干净 | v0.6.0 的 `gsm8k.py` 无 stray `breakpoint()` |

### 8.2 v0.6.0 特有的两处适配（与原 fork 不同，务必注意）

1. **`rec_tool.py` 接口升级**：v0.6.0 `BaseTool` 改了签名——
   - `create()`：`-> str` ⟶ `-> tuple[str, ToolResponse]`（现返回 `instance_id, ToolResponse()`）
   - `execute()`：`-> tuple[str, float, dict]` ⟶ `-> tuple[ToolResponse, float, dict]`
     （现返回 `ToolResponse(text=user_response), tool_reward, {}`）
   - 新增 `from .schemas import ... ToolResponse`。业务逻辑（GPT 用户模拟器）未改。

2. **`RolloutConfig` 必须显式声明 SID 字段**：v0.6.0 的 `RolloutConfig(BaseConfig)` 是
   **结构化 dataclass**，不接受任意键，且 `"x" in config` 会抛 `AttributeError`（`BaseConfig.__getitem__`
   抛的是 AttributeError 而非 KeyError）。因此：
   - 在 `workers/config/rollout.py` 的 `RolloutConfig` 里新增
     `sid_beam_size: Optional[int] = None` 和 `sid_length: Optional[int] = None`；
   - rollout `__init__` 里改用 `config.get("sid_beam_size", None)` 读取（**不要**用原 fork 的
     `("sid_beam_size" in config)` / `config['sid_beam_size']`，会在结构化配置上报错）。

### 8.3 校验

- `python -m py_compile` 全部通过（rollout / rollout config / rec_tool / 4 个 reward）。
- grep 确认所有插入点就位（imports / helpers / `__init__` / `generate_sequences` / config 字段）。
- ⚠️ 未做运行时验证：本机 macOS 无 torch/vllm/CUDA，需在 GPU 环境 `import` + 小规模 rollout 冒烟测试。

### 8.4 仍需项目侧外部接线（不属于 verl 源码，需你在训练脚本里配置）

- [ ] 训练脚本用 CLI override 传 `+actor_rollout_ref.rollout.sid_beam_size=<N>`、`+actor_rollout_ref.rollout.sid_length=<L>`。
- [ ] `custom_reward_function` 指向 `recommend.py` / `StepRule_*`（`default_compute_score` 仍不含 `"recommendation"` 分支）。
- [ ] tool config yaml 注册 `RecTool`，并提供 `embedding_path`。
- [x] 把训练/评估脚本里的 `verl` 引用切到顶层 `verl/` 包目录，并对齐更高的 torch/vllm。
- [ ] 确认目标 vllm 版本的 `llm.beam_search()` / `BeamSearchParams` 签名与本移植一致（0.7.0–0.8.5 区间应 OK）。
- [ ] 下游消费 `non_tensor_batch['beam_search_results']` 的评估脚本仍能对接。
- [ ] GPU 环境跑通后，做指标对齐（与原 0.4.1 锁定栈对比）。
