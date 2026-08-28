# rag-assistant-eval Specification

## Purpose

扩展既有评测链（run_eval/eval_agent/eval_dataset）以覆盖白盒助手：新增 `边界拒答` 评测类型、`precision_at_k` 纯函数、is_quoted 入评估、baseline 报告白盒展示。目标"证明有效"可量化/可复现/可追溯。

## ADDED Requirements

### Requirement: 评测集扩面（边界拒答类型）

系统 SHALL 在 `eval_dataset.py` 的 `VALID_TYPES` 增加 `边界拒答`；该类评测断言 = 必须触发固定话术（boundary）且不产生 token 流。

#### Scenario: 边界拒答评测
- **WHEN** 评测集含"边界拒答"类问题（如无语料模块提问）
- **THEN** 断言返回固定低置信话术，tokens_usage 为 0，不进入 generate

### Requirement: precision_at_k

系统 SHALL 新增 `precision_at_k` 纯函数：召回 top-k 中相关块占比（与 expected_references 节匹配），可单测、可聚合。

#### Scenario: 计算 precision@3
- **WHEN** 召回 top3 含 2 个相关块
- **THEN** precision@3 = 2/3

### Requirement: is_quoted 校验

系统 SHALL 将 `lcs_quote_match`（is_quoted 判定）作为纯函数单测，并纳入评估（断言 quotedKeys ⊆ 召回块）。

#### Scenario: quotedKeys 合法
- **WHEN** 一轮生成完成
- **THEN** quotedKeys 中每个 key 都对应一个精排召回块

### Requirement: baseline 报告白盒展示

系统 SHALL 复用 run_eval 链产出 baseline 报告（hit@k / 质量分 / 成本 / 耗时），供 `GET /api/rag/assistant/eval/report` 白盒展示"怎么证明有效"。

#### Scenario: 报告可查
- **WHEN** 评测完成
- **THEN** eval/report 返回 hit@k/质量分/cost/latency 聚合（含语料版本）
