# 核心功能与白盒问答（Python 白盒链路引擎）

> summary: 核心功能与白盒问答 — 白盒 SSE 全链路（intent→rewrite→recall→rerank→generate→done）+ 后端契约对齐 + 复用映射
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-02-核心功能与白盒问答.md
> 类别：操作流程


### Context

> 检索摘要：RAG 项目介绍助手 Python 白盒链路引擎要对齐哪些后端契约、复用哪些既有检索生成能力？

后端（OpenSpec 变更）已定义完整契约：SSE 事件时序（permission→intent→rewrite→rerank→token→done）、5 个接口（ask 流式/非流式、close、turns、eval/report）、4 份 spec（pipeline/guardrails/resilience/eval）。本变更在 Python 侧实现引擎，对齐该契约，并复用既有 `/api/tutoring/rag/query` 的检索/生成/评估能力。

### 复用 vs 新增映射（白盒 SSE / suggestions / eval 扩展）

> 检索摘要：白盒 SSE 事件流、suggestions 追问建议、eval 评测扩展哪些复用现有代码、哪些是新增函数？

- **白盒 SSE**：`api/rag.py` 或新 `api/rag_assistant.py`；复用现有鉴权 `verify_internal_token`；新增 `assistant` router + 事件流。
- **suggestions**：新函数；复用 doubao 连接；LLM 生成 + 静态池兜底。
- **eval 扩展**：`eval_dataset` / `eval_agent`；复用 run_eval 链；新增边界拒答类型 / precision_at_k / is_quoted。

### 白盒链路（Python 侧事件产出）

> 检索摘要：白盒链路完整事件时序是什么——intent/rewrite/recall/rerank/generate 到 done 的产出顺序？

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
