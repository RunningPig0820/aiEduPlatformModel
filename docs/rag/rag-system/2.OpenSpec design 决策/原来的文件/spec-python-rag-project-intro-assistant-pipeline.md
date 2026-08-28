> summary: 08-25 Python 白盒 RAG 链路引擎流水线 spec：intent LLM 结构化+关键词兜底、Query 改写透传、按 anchor 选池的向量+BM25 双路召回(单路 2s 超时)、RRF 精排 Top-K 仅回传、doubao 流式生成，全链路产出与后端一致的 SSE 事件与 done 结果。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-rag-project-intro-assistant-pipeline.md
> 类别：操作流程

# rag-assistant-pipeline Specification

## 文档说明
> 本文件为原始 spec 文档（08-25 白盒 spec）的 RAG 结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**（08-25 白盒 spec），真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；文档同时包含 ✅已落地 / ⚠️构想未实现 / ❓待决策内容。本文件独立完整，内容不拆分到外部 canonical 文档。

### Purpose
> 状态：⚠️
> 检索摘要：Python 白盒 RAG 链路引擎的定位与各阶段流水线是什么？

Python 白盒 RAG 链路引擎：intent（LLM 结构化输出 + 关键词兜底）→ rewrite → recall（向量+BM25，按 anchor 选池，单路 2s 超时降级）→ rerank（RRF Top-K，仅回传精排块）→ generate（doubao 流式）。产出与后端契约一致的 SSE 事件与 done 结果。

### Requirement: intent 结构化输出（扩展既有 classify）
> 状态：⚠️
> 检索摘要：intent 阶段怎么结构化识别——LLM 输出 anchor/candidates、失败回退关键词且不阻断链路？

系统 SHALL 在每轮开头调用 LLM（非流式、0 温度、关思考）输出结构化元数据 `{anchor, category, switch_detected, ambiguous, candidates}`；LLM 失败/超时/非闭集 → 回退关键词锚定（`ANCHOR_RULES` + `_fallback_anchor`），degraded 标记走 200，不阻断链路。

#### Scenario: 正常分类
- **WHEN** 学生问"这个项目的整体架构是什么"
- **THEN** intent 输出 `{anchor:"ai-tutoring", category:"项目介绍", switch_detected:false, ambiguous:false, candidates:["ai-tutoring"]}` 及锁定节

#### Scenario: LLM 失败兜底
- **WHEN** intent LLM 调用失败或输出非闭集类别
- **THEN** 回退 `_fallback_anchor` 得 locked_sections，intent 事件带 degraded 标记，链路继续

### Requirement: Query 改写透传
> 状态：⚠️
> 检索摘要：Query 改写怎么透传——基于原始问题与上下文生成检索式改写、前端看前后对比？

系统 SHALL 基于原始问题与当前上下文（anchor、历史）生成改写后检索式 query，`rewrite` 事件透传 `{originalQuestion, rewrittenQuery}`。

#### Scenario: 口语改写展示
- **WHEN** 问题含口语化表达（"这个咋防抄答案"）
- **THEN** rewrite 输出检索式改写（"怎么防学生套答案"），前端展示改写前后对比

### Requirement: 按 anchor 选语料池的多路召回
> 状态：⚠️
> 检索摘要：多路召回怎么按 anchor 选语料池——向量+BM25 双路、单路 2s 超时降级、池内锚定加权？

系统 SHALL 执行向量（COS rag 索引）与 BM25（本地 jsonl + jieba）双路召回，且**先按 intent 的 anchor（模块）过滤语料池**（orchestrate 入参加 `corpus`），池内继续 authority × 节级锚定加权；任一单路 2s 硬超时/异常 → 该路降级为空（`{hits:[], confidence:0}`）继续另一路。anchor 缺失/ambiguous → 维持全池现状。

#### Scenario: 双路正常
- **WHEN** 两路均在 2s 内返回
- **THEN** 编排器 RRF 融合两路，池内锚定加权生效

#### Scenario: 单路降级
- **WHEN** 向量路超时/挂掉
- **THEN** 降级纯 BM25，链路继续，rerank 事件带 degraded 标记

#### Scenario: anchor 选池
- **WHEN** intent anchor="ai-tutoring"
- **THEN** 仅在该模块语料池内召回（当前 234 块），池内继续节级锚定加权

### Requirement: RRF 精排 Top-K 仅回传精排块
> 状态：⚠️
> 检索摘要：RRF 精排后回传什么——只回传 Top-K 精排块、严禁吐全量召回列表？

系统 SHALL 对双路召回 RRF 融合（`RRF_K`），按综合分取 Top-K（默认 3），**仅回传精排后块**（blockId/title/summary/filePath/score）；严禁吐全量召回列表。

#### Scenario: 仅回传精排块
- **WHEN** 双路命中多块
- **THEN** `rerank` 事件仅携带 Top-K 精排块

### Requirement: doubao 流式生成
> 状态：⚠️
> 检索摘要：生成阶段怎么流式输出——doubao 基于精排块与改写 query、只基于检索上下文不编造？

系统 SHALL 基于精排 Top-K 块与改写 query 调 doubao 流式生成（温度 0.2，`include_usage` 取 usage），按 token 事件流式输出；只基于检索上下文，语料未覆盖不编造。

#### Scenario: 流式输出
- **WHEN** 精排完成进入生成
- **THEN** token 事件逐增量输出，done 前不含截断
