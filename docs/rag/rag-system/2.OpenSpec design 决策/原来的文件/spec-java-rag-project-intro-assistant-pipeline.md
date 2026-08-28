> summary: Python 侧白盒 RAG 链路完整能力规格：intent 结构化输出（LLM 闭集分类、模块级 anchor 路由 + 节级 locked_sections 两层锚定、失败关键词兜底）、Query 改写透传、向量+BM25 多路召回（单路 2s 超时降级）、RRF 精排 Top-K、doubao 流式生成、以及白盒 SSE 阶段事件时序（intent→(clarify|switch)→rewrite→rerank→(boundary)→token→done）。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-java-rag-project-intro-assistant-pipeline.md
> 类别：操作流程

# rag-assistant-pipeline Specification

## 文档说明
> 本文件为原始 spec 文档的 RAG 结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

## ADDED Requirements

### Requirement: intent 结构化输出
> 状态：✅
> 检索摘要：intent怎么把学生问题分类成闭集并输出anchor/switch/ambiguous/candidates？LLM失败时怎么回退关键词锚定且不阻断链路？

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
> 状态：✅
> 检索摘要：口语化问题怎么改写成检索式query？rewrite事件怎么透传originalQuestion/rewrittenQuery给前端展示？

系统 SHALL 基于原始问题与当前上下文（锚点、历史）生成改写后检索式 query，并在 `rewrite` 事件中透传 `{originalQuestion, rewrittenQuery}` 供前端展示。

#### Scenario: 改写展示

- **WHEN** 学生问题含口语化表达
- **THEN** `rewrite` 事件返回改写后检索式，前端展示"原始问题 / 改写后问题"对比

### Requirement: 多路召回
> 状态：✅
> 检索摘要：召回为什么用向量加BM25双路并行？单路2s超时或异常怎么降级为空而不阻断链路？
> 落地说明：当前实现为双池三路（rag-full 全量向量 + rag-slice 切片向量 + BM25 本地关键词），各向量路 2s 超时降级；语义兼容并超越原双路设计。

系统 SHALL 执行向量召回（COS rag 索引）与 BM25 关键词召回（本地 jsonl，jieba 分词）双路，任一单路 2s 硬超时或异常 → 该路结果降级为空并继续另一路（`{hits:[], confidence:0}` 冒泡捕获），不阻断链路。

#### Scenario: 双路正常

- **WHEN** 两路均在超时内返回
- **THEN** 编排器融合两路结果（RRF）

#### Scenario: 单路降级

- **WHEN** 向量路超时/挂掉
- **THEN** 系统降级为纯 BM25 路径，链路继续，rerank 事件携带 degraded 标记（前端可展示"该步降级"）

### Requirement: RRF 精排 Top-K
> 状态：✅
> 检索摘要：双路召回结果怎么RRF融合取Top-K？为什么只回传精排块、严禁把全量召回列表吐给前端？

系统 SHALL 对双路召回结果做 RRF 融合（融合常数沿用 `RRF_K`），按综合分取 Top-K（默认 K=3，可配），仅将精排后块回传；严禁将全量召回原始列表吐给前端。

#### Scenario: 仅回传精排块

- **WHEN** 召回双路命中多块
- **THEN** `rerank` 事件仅携带精排 Top-K 块（blockId/title/summary/filePath/score），不吐全量列表

### Requirement: doubao 流式生成
> 状态：✅
> 检索摘要：精排Top-K块和改写query怎么进doubao流式生成？为什么生成只基于检索上下文、语料未覆盖不编造？

系统 SHALL 基于精排 Top-K 块与改写后 query 调用 doubao 流式生成答案（强模型、温度 0.2、`include_usage` 取 usage），按 token 事件流式输出；生成只基于检索上下文，语料未覆盖不编造。

#### Scenario: 流式输出

- **WHEN** 进入生成阶段
- **THEN** 系统以 `token` 事件增量输出正文直至生成完成

### Requirement: 白盒阶段事件序列
> 状态：✅
> 检索摘要：白盒SSE事件固定顺序是什么？clarify/switch分支为什么无rewrite/rerank/token流、boundary分支为什么无token流？

系统 SHALL 按固定顺序产出 SSE 事件：`intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done`；`clarify`/`switch` 分支无 rewrite/recall/generate，`boundary` 分支无 token 流。

#### Scenario: 正常流

- **WHEN** 链路完整
- **THEN** 事件顺序为 intent → rewrite → rerank → token* → done

#### Scenario: 早停分支

- **WHEN** 澄清或切换（clarify/switch）触发
- **THEN** 对应分支事件后直接 done，无 rewrite/rerank/token 流
- **WHEN** 范围门低置信度触发
- **THEN** rerank（可为空）后 boundary 事件 + done，无 token 流
