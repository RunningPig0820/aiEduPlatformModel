# Test: RAG 项目介绍助手 - Python 白盒链路

> 测试策略：pytest 单元测试为主（mock 外部边界），复用 tests/rag/ 既有模式（monkeypatch + FakeCosClient）。
> 真实链路冒烟（COS+doubao）单独标注，不跑在常规 pytest。

## 测试文件规划

| 文件 | 覆盖 |
|---|---|
| `tests/rag/test_assistant_pipeline.py` | intent/rewrite/recall/rerank/generate 各阶段 + 白盒事件 |
| `tests/rag/test_assistant_guardrails.py` | 范围门低置信/clarify/is_quoted |
| `tests/rag/test_assistant_resilience.py` | 分层超时/断连取消/tokens_usage |
| `tests/rag/test_assistant_api.py` | SSE 事件时序/非流式/鉴权/turns/guide |
| `tests/rag/test_assistant_eval.py` | 边界拒答类型/precision_at_k/is_quoted 校验 |
| `tests/rag/test_rag_query.py`（回归） | corpus 参数向后兼容，现有 query 测试全过 |

## 用例清单

### A. 意图（intent）
- [ ] 正常分类：LLM 返回闭集 → `{anchor, category, switch, ambiguous, candidates}` 正确
- [ ] 失败兜底：LLM 抛异常 → `_fallback_anchor` 得 locked_sections + degraded
- [ ] 非闭集：LLM 返回闭集外 → 回退关键词
- [ ] candidates 闭集去重

### B. 改写（rewrite）
- [ ] 口语→检索式改写
- [ ] LLM 失败 → 返回原问题

### C. 召回/精排（recall/rerank）
- [ ] anchor 选池：corpus 参数过滤语料，锚定公式不变（回归）
- [ ] 双路正常 → RRF Top-K 仅回传精排块
- [ ] 向量超时 → 降级纯 BM25 + degraded
- [ ] 不吐全量召回（rerank 只含 Top-K）

### D. 生成/引用（generate/is_quoted）
- [ ] 流式 token 增量（mock ark_stream）
- [ ] 8s 超时 → 写死降级话术 + 召回清单
- [ ] is_disconnected → 中止流
- [ ] `lcs_quote_match`：命中（≥8 中字符）/改写未命中/英文 12 字符窗口

### E. 护栏（guardrails）
- [ ] 范围门：综合分<0.75/0.5 → boundary(low_confidence) 固定话术 0 token
- [ ] clarify：多候选触发 / 澄清一次仍模糊直接默认 / 单候选不触发 / 0 token 不计轮次
- [ ] clarify 点选候选重发：前端重发原问 + `current_project=点选模块` → intent 以 current_project 权威锚定、不再 ambiguous（不因问题含糊再拉 ambiguous）；点选模块与会话锚点不同 → switch 照常
- [ ] 四模块放行（无禁区）：问知识图谱 → 召回→低置信（C1）

### F. API
- [ ] SSE 事件时序冻结（mock 各阶段，断言事件顺序不重排不丢失）
- [ ] 非流式 stages 摘要
- [ ] turns/{traceId} 断线补查
- [ ] guide 静态池（含 RAG 方向）
- [ ] eval/report baseline
- [ ] 鉴权失败 403（缺/错 token）

### G. 评估扩展
- [ ] eval_dataset `边界拒答` 类型校验 + 断言（触发固定话术且 0 token）
- [ ] `precision_at_k` 纯函数（top-k 相关占比）
- [ ] quotedKeys ⊆ 召回块

### H. 回归
- [ ] `/api/tutoring/rag/query` 现有测试全过（corpus 参数向后兼容）

## 真实冒烟（非常规 pytest，手动/标注）
- [ ] 起服务 `POST /api/rag/assistant/ask`（SSE）问"这个项目的整体架构是什么" → 看事件流
- [ ] 问"知识图谱怎么流转" → 低置信 boundary（C1 预期）
- [ ] 生成中点"停止" → 前后端中止
- [ ] `run_eval.py` 扩面后 baseline 报告
