## Why

学生需要一个能**证明 RAG 能力**、又能**讲清本项目设计逻辑**的白盒问答助手：回答遵循 RAG 标准链路（权限→意图→改写→多路召回→重排→生成）并把中间状态**实时透传前端**。后端（`aiEduPlatform/openspec/changes/rag-project-intro-assistant`）已定义完整契约（proposal/design D1~D12/api.md/specs×4），本变更在 **Python 侧实现其白盒链路引擎与 `/api/rag/assistant/*` 内部端点**，供 Java 网关中继、前端展示。

Python 侧已有单模块（AI答疑）RAG 链路 `/api/tutoring/rag/query`（classify→向量+BM25→RRF→generate，含 references/usage/降级链）与评测链（run_eval/eval_agent/eval_dataset），本变更**泛化复用**，非重写。

## What Changes

Python 侧（aiEduPlatformModel 仓库，对齐后端方案 D1~D12 + specs×4）：

- **泛化 `core/rag/query.py` 为白盒链路**：
  - `intent`：结构化输出扩展 `{anchor, category, switch_detected, ambiguous, candidates}`（LLM 0 温度快模型），失败回退 `_fallback_anchor` + `ANCHOR_RULES`，degraded 标记走 200
  - `rewrite`：改写 query 透传前端
  - `recall`：**按 anchor 选语料池**（orchestrate 入参加 `corpus`，锚定加权公式原样——沟通点 2 定稿：模块级 anchor 选池 + 节级 locked_sections 池内加权，两层保留）+ 单路 2s 超时降级
  - `rerank`：RRF 融合 Top-K（默认 3）仅回传精排块，不吐全量召回
  - `generate`：doubao 流式（复用 `ark_stream.py`）+ 8s 硬超时降级 + `is_disconnected()` 断连取消
  - `is_quoted`：LCS 硬匹配（连续 8 中/12 英字符），done 后补发，非 LLM 自述
  - `clarify`：ambiguous 且 candidates ≥2 → 澄清轮（0 token、不计轮次、最多一轮）
  - `suggestions`：运行时 LLM 生成（必含 ≥1 条 RAG 方向——面试展示决策，沟通点 5）+ 静态池兜底
- **新增 `/api/rag/assistant/*` 内部端点**（`x-internal-token`，独立路由不影响现有 `/api/tutoring/rag/query`）：
  - `POST /ask`：SSE 流式（intent→(clarify|switch)→rewrite→rerank→(boundary)→token→done，permission 由 Java 产）+ 非流式（stages 摘要）
  - `GET /guide`：开始引导（静态池 RAG 定向）
  - `GET /eval/report`：baseline 报告
  - **close/turns 归 Java（Python 不建）**：close = Java 关中继 → Python is_disconnected 中止；turns 存 Java Redis。history/trace_id 由 Java 传入 Python。
- **健壮性**：分层超时（召回 2s/生成 8s）写死降级话术 0 token、断连取消、tokens_usage{prompt/completion/cache_hit/total} + trace_id
- **评估扩展**：评测集加 `边界拒答` 类型、`precision_at_k` 纯函数、is_quoted 入评估、baseline 报告
- **多模块语料路由**：语料按模块目录组织；当前仅 AI答疑（234 块），其他模块（RAG/题型/知识图谱）入库即自动可答（数据驱动，无禁区硬拒答）——沟通点 1 定稿：其他模块当前低置信拒答是正确的，语料后补

**BREAKING**：无。新增独立路由 + 泛化内部函数（加参数不破坏现有签名），`/api/tutoring/rag/query` 保持不变。

## Capabilities

### New Capabilities
- `rag-assistant-pipeline`: Python 白盒链路（intent/rewrite/recall/rerank/generate）与 SSE 事件产出
- `rag-assistant-guardrails`: 模块全放行（语料驱动）+ 范围门低置信过滤（唯一拒答）+ clarify + is_quoted
- `rag-assistant-resilience`: 分层超时、断连取消、tokens_usage/trace_id、写死降级话术
- `rag-assistant-eval`: 边界拒答评测类型、precision_at_k、is_quoted 校验

### Modified Capabilities
（无既有 spec 需求变化——`/api/tutoring/rag/query` 与评测链契约不变，白盒为独立新能力）
