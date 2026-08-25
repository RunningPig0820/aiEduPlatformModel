# RAG 项目介绍助手 - Python API（内部端点）

> 对齐后端契约：`aiEduPlatform/openspec/changes/rag-project-intro-assistant/api.md`
> Python 侧实现 `/api/rag/assistant/*` 内部端点（`x-internal-token`，Java 网关中继给前端）
> 基础路径：`/api/rag/assistant`（Python 内部，不经前端直接调）

---

## 事件时序（冻结，对齐后端）

`permission → intent → (clarify|switch) → rewrite → rerank → (boundary|token) → done`

> **归属（定死 2026-08-25）**：**production API Python 不产 permission**——permission 仅 Java（角色门在 Java，Python 无角色信息，Python 产了 Java 桥还得去重）。Python **自测时**可在测试里模拟完整时序，但生产端点从 intent 开始。

---

## 1. 发起问答（SSE 流式）`POST /api/rag/assistant/ask`

**请求**（Python 内部接收，字段 snake_case，Java 中继时 camel 化；**history/trace_id 由 Java 网关组装**）：
```json
{ "question": "这个项目的整体架构是什么？",
  "session_id": "sess-001",
  "current_project": "ai-tutoring",
  "history": [
    { "question": "前一轮问题", "answer": "前一轮答案", "anchor": "ai-tutoring" }
  ],
  "trace_id": "trc-abc123",
  "stream": true, "top_k": 3 }
```

> **history**：最近 N 轮（默认 3，**含 clarify 轮**），Java 网关每轮过手 done 天然有，Python 只消费（intent/rewrite/clarify 兜底用）。**截断到最近 N 轮是 Python 侧显式任务**（后端 resilience spec）。
>
> **trace_id**：**定死 Java 生成** → 请求传 Python → Python 贯穿日志并在 done 回显。Python 不自己生成（否则两端 trace 对不上）。

**Python 产出 SSE 事件**：
| 事件 | data | 说明 |
|---|---|---|
| `intent` | `{anchor, category, switch_detected, ambiguous, candidates, locked_sections, degraded}` | LLM 结构化，失败→关键词兜底 |
| `clarify` | `{message, candidates, default}` | ambiguous & candidates≥2，随后 done |
| `switch` | `{from_anchor, to_anchor}` | 上下文切换 |
| `rewrite` | `{original_question, rewritten_query}` | 改写对比 |
| `rerank` | `{blocks: [{block_id, title, summary, file_path, score}]}` | RRF Top-K 精排块（灰显） |
| `boundary` | `{message, reason}` | 低置信拒答（reason=low_confidence），随后 done |
| `token` | `{text}` | 生成增量 |
| `done` | 完整结果 | answer/quoted_keys/tokens_usage/trace_id/suggestions/reason |

**done data**：
```json
{ "answer": "……", "quoted_keys": ["block-01", "block-03"],
  "tokens_usage": {"prompt_tokens": 320, "completion_tokens": 140,
                   "cache_hit_tokens": 0, "total_tokens": 460},
  "trace_id": "trc-abc123",
  "suggestions": ["想了解RAG的整体架构吗？", "RRF融合算法有什么难点？"],
  "reason": null }
```

## 2. 发起问答（非流式）`POST /api/rag/assistant/ask`（stream=false）

返回 done 结构 + `stages` 摘要：`{intent, rewrite, rerank, permission}`。

## 3. 关闭对话 `POST /api/rag/assistant/sessions/{sessionId}/close`

> **定死（2026-08-25）：Python 不建 close 端点。** close = Java 关中继连接 → Python `is_disconnected()` 自然触发中止 doubao + Java Redis 置 closed + 返回累计 token。累计 token 由 Java 聚合（每轮 done 后累加 Redis）。Python 只支持 is_disconnected 中止在途流，不建会话态、不建 close 端点（否则重复职责）。

## 4. 断线补查 `GET /api/rag/assistant/turns/{traceId}`

> **定死（2026-08-25）：turns 存 Java Redis**——Java 是聚合点，每轮 done 过手天然能按 trace_id 落一份；Python 彻底无状态。Python 的 eval trace jsonl（评估用）与 turns 补查（会话用）**分开**，不混。

> 补查返回该轮 done 结果（answer/quoted_keys/tokens_usage/suggestions/reason）由 Java 从 Redis 读回。

## 5. 评估报告 `GET /api/rag/assistant/eval/report`

```json
{ "version": "2026-08-25-e966ac", "count": 15, "hit_at3": 0.80,
  "quality_avg": 4.2, "avg_latency_ms": 5599, "avg_cost_yuan": 0.0157,
  "judged_ratio": 1.0 }
```
复用 `run_eval` 链 + eval_dataset（加 `边界拒答` 类型）。

## 6. 开始引导 `GET /api/rag/assistant/guide`

```json
{ "suggestions": [
    { "title": "想了解RAG的整体架构吗？", "direction": "architecture" },
    { "title": "想知道知识库数据是如何流转的吗？", "direction": "data_flow" },
    { "title": "想看看评测体系是怎么设计的吗？", "direction": "evaluation" } ] }
```
静态池 0 token，RAG 定向（架构/数据流/评测/坑），会话入口展示。

---

## Python 实现要点

- **鉴权**：`verify_internal_token`（同现有 API）
- **流式**：复用 `ark_stream.stream_chat`（doubao OpenAI 兼容 SSE）；`is_disconnected()` 中止
- **超时**：召回 2s / 生成 8s（settings 参数化），降级话术写死 0 token
- **无状态**：Python 只产出 per-turn 结果；history/trace_id 由 Java 传入，会话/累计 token/close/turns 补查全归 Java（Python 不建 close/turns 端点）
- **permission**：production API 不产，仅 Java（Python 测试里模拟）
