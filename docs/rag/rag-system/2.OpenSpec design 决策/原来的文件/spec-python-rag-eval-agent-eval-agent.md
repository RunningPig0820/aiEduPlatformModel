> summary: 评测 agent 需求（spec）：评测集每模块≥5条含预期引用与预期要点、评测流程走页面锚定检索+生成+LLM判分并支持模块/全量聚合、hit@k(k=3)计算、doubao LLM 判 0~5 分输出严格 JSON、cost/latency 指标定义。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-rag-eval-agent-eval-agent.md
> 类别：数据关联

# spec-python-rag-eval-agent-eval-agent（评测 agent 需求）

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。
> ⚠️代码演进说明：真实实现以 0.8 canonical + 代码为准（代码已演进：HIT_K=5 / 判分改硬算，与本文 hit@k k=3 / LLM 判分需求不同）。

### 评测集
> 状态：⚠️
> 检索摘要：评测集要求每模块至少5条 Q&A，每条含 module/question/question_type（概览/为什么/数据流/难点/指标）、expected_references 与 expected_points，加载时校验完整性。

系统 SHALL 维护评测集：每模块 ≥5 条 Q&A，每条含 `module`、`question`、`question_type`（概览/为什么/数据流/难点/指标）、`expected_references[]`（预期引用的 page+section）、`expected_points[]`（预期答案要点）。

#### Scenario: 评测集加载

- **WHEN** 加载评测集
- **THEN** 每模块 SHALL 至少 5 条，且每条含 module/question/question_type/expected_references/expected_points

### 评测流程
> 状态：⚠️
> 检索摘要：评测流程对每条问题执行页面锚定检索→记录召回 top-K 与得分→生成答案→LLM 判分，并支持按模块/全量聚合出 hit@k、平均质量分、总成本、平均耗时。

系统 SHALL 对每条评测问题执行：页面锚定检索（该模块）→ 记录召回 top-K 与得分 → 生成答案 → LLM 判分，并支持按模块/全量聚合。

#### Scenario: 单条评测执行

- **WHEN** 对某条评测问题执行评测
- **THEN** 输出 SHALL 包含：召回条目及得分、hit 结果、生成答案、引用、usage、耗时、判分

#### Scenario: 聚合报告

- **WHEN** 完成一个模块或全量评测
- **THEN** 输出 SHALL 聚合出 hit@k、平均质量分、总成本、平均耗时

### hit@k 计算
> 状态：⚠️
> 检索摘要：hit@k 按预期引用出现在召回 top-k 的比例计算（k=3，源文档池 top-k），如预期引用3条中2条在 top-3 则 hit@3=2/3。

系统 SHALL 计算 `hit@k`：预期引用中出现在召回 top-k 的比例（k=3，源文档池 top-k）。

#### Scenario: hit 计算

- **WHEN** 预期引用 3 条，其中 2 条在召回 top-3
- **THEN** hit@3 = 2/3

### LLM 答案质量判分
> 状态：⚠️
> 检索摘要：答案质量由 LLM（doubao 复用 ark_stream）按准确性/引用正确性/覆盖预期要点判 0~5 分，输出严格 JSON {score, rationale}，无 usage 时降级估算。

系统 SHALL 用 LLM（doubao，复用 ark_stream）对答案判 0~5 分，按 准确性/引用正确性/覆盖预期要点 三方面，输出 `{score, rationale}`（严格 JSON）；无 usage 时降级估算。

#### Scenario: 判分解析

- **WHEN** LLM 返回判分 JSON
- **THEN** 系统 SHALL 解析出 score（0~5）与 rationale；解析失败则重试 1 次，仍失败记 0 分并标记

### 指标定义
> 状态：⚠️
> 检索摘要：评测指标：hit@k、answer_quality（平均判分）、cost（prompt+completion tokens×单价）、latency（检索/生成/总耗时），报告含累计成本¥与平均耗时ms，超时按降级计。

系统 SHALL 计算指标：`hit@k`、`answer_quality`（平均判分）、`cost`（prompt+completion tokens × 单价）、`latency`（检索/生成/总耗时）。

#### Scenario: 成本与耗时统计

- **WHEN** 评测完成
- **THEN** 报告 SHALL 含累计成本（¥）与平均耗时（ms），超时按降级计
