# Design: RAG 项目介绍助手 - Python 白盒链路引擎

## Context

后端（`aiEduPlatform/openspec/changes/rag-project-intro-assistant`）已定义完整契约：SSE 事件时序（permission→intent→rewrite→rerank→token→done）、5 个接口（ask 流式/非流式、close、turns、eval/report）、4 份 spec（pipeline/guardrails/resilience/eval）。本变更在 Python 侧实现引擎，对齐该契约，并复用既有 `/api/tutoring/rag/query` 的检索/生成/评估能力。

## 复用 vs 新增映射

| 后端要求 | Python 落点 | 复用现有 | 新增 |
|---|---|---|---|
| intent 结构化 | `core/rag/query.py` classify 扩展 | `_fallback_anchor`/`ANCHOR_RULES`/`CATEGORY_SECTIONS`/`_llm_category`(LLM 分类) | schema 加 `candidates`/`switch_detected`/`ambiguous`；重写改写 |
| rewrite | 新函数 | — | `rewrite_query(question, anchor, history)` |
| recall 双路 | `retrieve_vector`/`retrieve_bm25` | 两函数 | 单路 2s 超时包裹（asyncio.wait_for/线程池） |
| rerank | `orchestrate` | RRF/权威度/锚定加权 | **入参加 `corpus`**（按 anchor 选池，锚定公式原样）；只回传 Top-K 精排块 |
| generate 流式 | `core/rag/generate` | doubao 连接 | 改流式（复用 `ark_stream.stream_chat`）+ 8s 超时 + is_disconnected |
| is_quoted | 新纯函数 | — | `lcs_quote_match(answer, block_texts) -> keys` |
| clarify | 新逻辑 | intent 的 ambiguous/candidates | 澄清轮状态机（0 token、最多一轮） |
| suggestions | 新函数 | doubao 连接 | LLM 生成 + 静态池兜底 |
| 范围门 | `core/rag` 新增 | 现有降级语义 | 低置信过滤（索引层 0.75/源 0.5） |
| 白盒 SSE | `api/rag.py` 或新 `api/rag_assistant.py` | 现有鉴权 `verify_internal_token` | `assistant` router + 事件流 |
| close/累计token | 新端点 | — | Redis 或内存会话累计（Python 无状态边界待确认） |
| eval 扩展 | `eval_dataset`/`eval_agent` | run_eval 链 | 边界拒答类型/precision_at_k/is_quoted |

## 沟通结论锁定（2026-08-25 定稿）

- **C1 语料范围**：只管 AI答疑（234 块）；RAG/题型/知识图谱当前低置信拒答正确，语料后补自动可答（数据驱动，无禁区）。
- **C2 anchor 两层**：模块级 anchor（选语料池，新）+ 节级 locked_sections（池内 authority×锚定加权，原样）。orchestrate 入参加 `corpus`，锚定公式不动。anchor 缺失/ambiguous → 维持现状（全池）。
- **C3 cache_hit**：开发时实测 doubao 是否返回 usage.cache_hit；取不到 → tokenizer 估算 + 标注"估算"。
- **C4 clarify 候选**：候选 = intent LLM `candidates`（主源）+ 会话历史锚点（兜底）→ 去重 → ≥2 才 clarify；default = current_project > 会话最后锚定。触发后最多一轮，仍模糊直接默认。
- **C5 suggestions**：必含 ≥1 条 RAG 方向（面试展示，RAG 始终带上非并列模块）。

## 白盒链路（Python 侧事件产出）

```
POST /api/rag/assistant/ask
 → intent(LLM结构化) → 失败回退关键词(degraded)
     ├─ ambiguous & candidates≥2 → event: clarify(0 token, 不计轮次)
     ├─ switch_detected → event: switch + 重置上下文
 → rewrite → event: rewrite{original, rewritten}
 → recall(向量2s超时降级 + BM25) → 按 anchor 选池
 → rerank(RRF Top-K=3) → event: rerank{blocks}  ← 只回传精排块
     ├─ 综合分<0.75/0.5 → event: boundary(low_confidence) 固定话术 0 token → done
     ↓
 → generate(doubao 流式, 8s 超时→固定话术+召回清单)
     ←── is_disconnected → 中止流
 → done{answer, quotedKeys(LCS), tokensUsage, traceId, suggestions}
```

## 关键实现决策

### D-A. anchor 选池（C2）
- `corpus` 参数：`orchestrate(question, blocks, vec, bm, strategy, top_k, corpus=None)`；`corpus` 给定时先过滤 blocks（按 module/tags.module），再走现有 RRF/权威/锚定。
- 现有 `/api/tutoring/rag/query` 不传 corpus → 全池行为不变（向后兼容）。

### D-A2. history 上下文（联调审查 ①⑦ 定死）
- `intent(question, history)` / `rewrite_query(question, anchor, history)`：history 为最近 N 轮 `{question, answer, anchor}` 列表（**默认 3，含 clarify 轮**）。
- **显式截断**：取 `history[-N:]`（最近 N 轮），后端 resilience spec 的上下文窗口。history 由 Java 网关组装传入，Python 只消费+截断。

### D-B. 双路超时（pipeline/resilience）
- 向量路/COS 可能阻塞：用 `asyncio.wait_for(retrieve_vector(...), timeout=2)`（若 retrieve 是同步，包 `run_in_threadpool` + 超时）；BM25 本地快，超时留给网络路。
- 生成 8s：`ark_stream.stream_chat` 已是 httpx 流式，超时由 httpx `timeout` 控制 + 外层捕获 → 写死降级话术。

### D-C. is_quoted（D6）
- `lcs_quote_match(answer, blocks)`：对每个精排块的 text/summary，与 answer 做最长公共子串；`len(match) >= 8`（中文按字符）→ quoted。纯函数，入评估。
- done 后补发（chunk 粒度会撕裂连续 8 字窗口）。

### D-D. 会话状态（close/trace_id）——定死 2026-08-25
- **Python 保持无状态**：history/trace_id 由 Java 网关传入（请求字段），Python 只消费。
- **trace_id**：定死 Java 生成 → 请求传 Python → Python 贯穿日志并在 done 回显；Python 不自己生成。
- **close**：Python **不建 close 端点**——close = Java 关中继 → Python `is_disconnected()` 中止 doubao + Java Redis 置 closed + 返回累计。累计 token 归 Java。
- **turns 补查**：存 Java Redis（聚合点），Python 不落会话 trace。Python 的 eval trace jsonl 是评估用，与会话补查分开。

### D-E. suggestions（D11）
- done 后调一次 doubao（复用生成连接，0.2 温度）→ 1~3 条，prompt 约束"必含 ≥1 条 RAG 方向"。
- LLM 失败 → 静态池兜底（预写 2~3 条固定文案，含 RAG 方向）。

### D-F. 事件时序冻结——定死 2026-08-25
- 对齐后端：`permission → intent → (clarify|switch) → rewrite → rerank → (boundary|token) → done`，不得重排/丢失。
- **permission 归属定死**：production API Python **不产 permission**（角色门在 Java，Python 无角色信息）。Python 自测时在测试里模拟完整时序，生产端点从 intent 开始。

### D-G. 非流式 ask
- `stream=false`：内部走同一链路，产出 `done` 结构 + `stages` 摘要（intent/rewrite/rerank），一次性 JSON。

## Risks / Trade-offs

- [双路超时实现复杂度] asyncio vs 同步检索 → 用 run_in_threadpool + wait_for 包裹，测超时降级路径。
- [anchor 选池后语料少] 当前仅 AI答疑 → 其他模块命中空 → 低置信过滤（C1 预期）。
- [is_quoted 8 字窗口对改写答案] doubao 可能改写用词 → 评估集加"改写答案"用例验证窗口。
- [history 由 Java 传、时序对不上] 定死契约：Java 组装 history/trace_id，Python 只消费+截断；联调时逐轮核对。

## Migration Plan

1. `core/rag/query.py` 泛化：classify→intent 扩展、orchestrate 加 corpus、generate 流式化（独立函数，不动现有）。
2. 新增 `api/rag_assistant.py`：assistant router（ask/close/turns/eval/report），复用鉴权。
3. 新增 `core/rag/assistant.py`：白盒编排（intent/rewrite/recall/rerank/generate/is_quoted/clarify/suggestions）。
4. 评估扩展：eval_dataset 边界拒答类型 + precision_at_k + is_quoted。
5. 测试：pipeline 各阶段、SSE 事件时序、降级/超时/断连、评估新增。
6. 交付契约给前端/后端联调。
