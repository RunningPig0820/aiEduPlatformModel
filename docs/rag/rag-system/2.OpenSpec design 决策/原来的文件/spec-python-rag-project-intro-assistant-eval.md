> summary: 白盒助手 rag-assistant-eval 评测扩展 spec：复用 run_eval 评测链新增边界拒答评测类型、precision_at_k 纯函数与 is_quoted 校验入评估，baseline 报告白盒展示，目标"证明有效"可量化可复现可追溯。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-rag-project-intro-assistant-eval.md
> 类别：数据关联

# rag-assistant-eval Specification

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

### Purpose
> 状态：⚠️
> 检索摘要：白盒助手怎么证明检索有效？扩展既有评测链覆盖边界拒答、precision_at_k、is_quoted，让"有效"可量化可复现可追溯。

扩展既有评测链（run_eval/eval_agent/eval_dataset）以覆盖白盒助手：新增 `边界拒答` 评测类型、`precision_at_k` 纯函数、is_quoted 入评估、baseline 报告白盒展示。目标"证明有效"可量化/可复现/可追溯。

### 评测集扩面（边界拒答类型）
> 状态：⚠️
> 检索摘要：边界拒答问题怎么进评测集？eval_dataset 的 VALID_TYPES 新增边界拒答类型，断言必须触发固定话术且 token 流为 0。

系统 SHALL 在 `eval_dataset.py` 的 `VALID_TYPES` 增加 `边界拒答`；该类评测断言 = 必须触发固定话术（boundary）且不产生 token 流。

#### Scenario: 边界拒答评测
- **WHEN** 评测集含"边界拒答"类问题（如无语料模块提问）
- **THEN** 断言返回固定低置信话术，tokens_usage 为 0，不进入 generate

### precision_at_k
> 状态：⚠️
> 检索摘要：precision_at_k 纯函数怎么算？召回 top-k 中与预期引用匹配的相关块占比，可单测可聚合。

系统 SHALL 新增 `precision_at_k` 纯函数：召回 top-k 中相关块占比（与 expected_references 节匹配），可单测、可聚合。

#### Scenario: 计算 precision@3
- **WHEN** 召回 top3 含 2 个相关块
- **THEN** precision@3 = 2/3

### is_quoted 校验
> 状态：⚠️
> 检索摘要：is_quoted 引用判定怎么校验？lcs_quote_match 作为纯函数单测并纳入评估，断言 quotedKeys 必须对应精排召回块。

系统 SHALL 将 `lcs_quote_match`（is_quoted 判定）作为纯函数单测，并纳入评估（断言 quotedKeys ⊆ 召回块）。

#### Scenario: quotedKeys 合法
- **WHEN** 一轮生成完成
- **THEN** quotedKeys 中每个 key 都对应一个精排召回块

### baseline 报告白盒展示
> 状态：⚠️
> 检索摘要：怎么向面试官白盒展示白盒助手有效？run_eval 链产出 hit@k/质量分/成本/耗时报告，供 eval/report 接口查询。

系统 SHALL 复用 run_eval 链产出 baseline 报告（hit@k / 质量分 / 成本 / 耗时），供 `GET /api/rag/assistant/eval/report` 白盒展示"怎么证明有效"。

#### Scenario: 报告可查
- **WHEN** 评测完成
- **THEN** eval/report 返回 hit@k/质量分/cost/latency 聚合（含语料版本）
