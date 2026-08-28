## ADDED Requirements

### Requirement: 评测集

系统 SHALL 维护评测集：每模块 ≥5 条 Q&A，每条含 `module`、`question`、`question_type`（概览/为什么/数据流/难点/指标）、`expected_references[]`（预期引用的 page+section）、`expected_points[]`（预期答案要点）。

#### Scenario: 评测集加载

- **WHEN** 加载评测集
- **THEN** 每模块 SHALL 至少 5 条，且每条含 module/question/question_type/expected_references/expected_points

### Requirement: 评测流程

系统 SHALL 对每条评测问题执行：页面锚定检索（该模块）→ 记录召回 top-K 与得分 → 生成答案 → LLM 判分，并支持按模块/全量聚合。

#### Scenario: 单条评测执行

- **WHEN** 对某条评测问题执行评测
- **THEN** 输出 SHALL 包含：召回条目及得分、hit 结果、生成答案、引用、usage、耗时、判分

#### Scenario: 聚合报告

- **WHEN** 完成一个模块或全量评测
- **THEN** 输出 SHALL 聚合出 hit@k、平均质量分、总成本、平均耗时

### Requirement: hit@k 计算

系统 SHALL 计算 `hit@k`：预期引用中出现在召回 top-k 的比例（k=3，源文档池 top-k）。

#### Scenario: hit 计算

- **WHEN** 预期引用 3 条，其中 2 条在召回 top-3
- **THEN** hit@3 = 2/3

### Requirement: LLM 答案质量判分

系统 SHALL 用 LLM（doubao，复用 ark_stream）对答案判 0~5 分，按 准确性/引用正确性/覆盖预期要点 三方面，输出 `{score, rationale}`（严格 JSON）；无 usage 时降级估算。

#### Scenario: 判分解析

- **WHEN** LLM 返回判分 JSON
- **THEN** 系统 SHALL 解析出 score（0~5）与 rationale；解析失败则重试 1 次，仍失败记 0 分并标记

### Requirement: 指标定义

系统 SHALL 计算指标：`hit@k`、`answer_quality`（平均判分）、`cost`（prompt+completion tokens × 单价）、`latency`（检索/生成/总耗时）。

#### Scenario: 成本与耗时统计

- **WHEN** 评测完成
- **THEN** 报告 SHALL 含累计成本（¥）与平均耗时（ms），超时按降级计
