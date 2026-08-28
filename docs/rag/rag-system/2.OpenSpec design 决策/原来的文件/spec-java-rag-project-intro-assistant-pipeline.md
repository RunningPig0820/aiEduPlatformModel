# rag-assistant-pipeline Specification

## Purpose

Python 侧白盒 RAG 链路：intent（LLM 结构化输出，anchor/category/switch/ambiguous，失败回退规则）→ rewrite（改写 query）→ recall（向量 + BM25 双路，单路 2s 超时降级）→ rerank（RRF 融合 Top-K）→ generate（doubao 流式）。产出 SSE 事件与 done 完整结果。本能力定义 Python 引擎行为与事件契约；实现在 aiEduPlatformModel 仓库对应变更。

## ADDED Requirements

### Requirement: intent 结构化输出

系统 SHALL 在每轮开头调用 LLM（非流式、快模型、0 温度、关思考）将学生问题分类为闭集类别，并输出结构化元数据 `{anchor, category, switch_detected, ambiguous, candidates}`；LLM 失败/超时/非闭集输出时回退关键词锚定（复用 `ANCHOR_RULES` + `_fallback_anchor`），标记 degraded 且走 200 返回。`anchor` 为**模块级**（路由层，决定语料池）；`locked_sections` 为**节级**（加权层，池内 authority × 节锚定），两层并存，orchestrate 节级锚定逻辑保留、仅新增按 anchor 选池。

#### Scenario: 正常分类

- **WHEN** 学生问题"这个项目的整体架构是什么"
- **THEN** intent 输出 `{anchor:"ai-tutoring", category:"项目介绍", switch_detected:false, ambiguous:false, candidates:[]}` 及锁定章节

#### Scenario: 歧义输出候选

- **WHEN** 学生问题"这个功能的流转是什么样的"（跨功能指代不明）
- **THEN** intent 输出 `ambiguous:true` 及候选模块 `candidates:["ai-tutoring","rag-system"]`（主源；LLM 未给/给 <2 时以会话最近 N 轮锚过的模块去重兜底）

#### Scenario: LLM 失败兜底

- **WHEN** intent LLM 调用失败或输出非闭集类别
- **THEN** 系统回退关键词锚定得出 `locked_sections`，intent 事件携带 degraded 标记，不阻断链路

#### Scenario: 问候语识别

- **WHEN** 学生发"你好"等问候/寒暄语
- **THEN** intent 输出 `category="问候"`、`ambiguous=false`，不触发 clarify，直接走欢迎引导路径（固定欢迎话术 + 引导建议指向 ①项目介绍②操作③数据关联④难点，0 生成 token）

### Requirement: Query 改写透传

系统 SHALL 基于原始问题与当前上下文（锚点、历史）生成改写后检索式 query，并在 `rewrite` 事件中透传 `{originalQuestion, rewrittenQuery}` 供前端展示。

#### Scenario: 改写展示

- **WHEN** 学生问题含口语化表达
- **THEN** `rewrite` 事件返回改写后检索式，前端展示"原始问题 / 改写后问题"对比

### Requirement: 多路召回

系统 SHALL 执行向量召回（COS rag 索引）与 BM25 关键词召回（本地 jsonl，jieba 分词）双路，任一单路 2s 硬超时或异常 → 该路结果降级为空并继续另一路（`{hits:[], confidence:0}` 冒泡捕获），不阻断链路。

#### Scenario: 双路正常

- **WHEN** 两路均在超时内返回
- **THEN** 编排器融合两路结果（RRF）

#### Scenario: 单路降级

- **WHEN** 向量路超时/挂掉
- **THEN** 系统降级为纯 BM25 路径，链路继续，rerank 事件携带 degraded 标记（前端可展示"该步降级"）

### Requirement: RRF 精排 Top-K

系统 SHALL 对双路召回结果做 RRF 融合（融合常数沿用 `RRF_K`），按综合分取 Top-K（默认 K=3，可配），仅将精排后块回传；严禁将全量召回原始列表吐给前端。

#### Scenario: 仅回传精排块

- **WHEN** 召回双路命中多块
- **THEN** `rerank` 事件仅携带精排 Top-K 块（blockId/title/summary/filePath/score），不吐全量列表

### Requirement: doubao 流式生成

系统 SHALL 基于精排 Top-K 块与改写后 query 调用 doubao 流式生成答案（强模型、温度 0.2、`include_usage` 取 usage），按 token 事件流式输出；生成只基于检索上下文，语料未覆盖不编造。

#### Scenario: 流式输出

- **WHEN** 进入生成阶段
- **THEN** 系统以 `token` 事件增量输出正文直至生成完成

### Requirement: 白盒阶段事件序列

系统 SHALL 按固定顺序产出 SSE 事件：`intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done`；`clarify`/`switch` 分支无 rewrite/recall/generate，`boundary` 分支无 token 流。

#### Scenario: 正常流

- **WHEN** 链路完整
- **THEN** 事件顺序为 intent → rewrite → rerank → token* → done

#### Scenario: 早停分支

- **WHEN** 澄清或切换（clarify/switch）触发
- **THEN** 对应分支事件后直接 done，无 rewrite/rerank/token 流
- **WHEN** 范围门低置信度触发
- **THEN** rerank（可为空）后 boundary 事件 + done，无 token 流
