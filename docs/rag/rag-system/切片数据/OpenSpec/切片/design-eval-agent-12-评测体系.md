# 评测体系（可观测评测 agent：hit@k + answer_quality）

> summary: 评测体系 — 可观测评测 agent 设计：评测集 + hit@k/answer_quality/cost/latency 四指标 + 报告对比
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-eval-agent-12-评测体系.md
> 类别：数据关联


### Context：为什么需要可观测的评测 agent

> 检索摘要：project-intro-rag 知识库整理缺乏质量反馈手段，引入可观测评测 agent 跑评测集、用 LLM 判答案质量、算指标、输出观测报告，驱动模块逐个迭代。

`project-intro-rag`（项目介绍 RAG 问答系统）的第一步是**整理知识库**：逐个模块产出完善文档 → 切片 → 索引。但当前没有手段知道"整理得好不好、检索准不准、答案质量如何"。

本变更引入**可观测的评测 agent**：跑评测集、用 LLM 判答案质量、算指标、输出观测报告，驱动知识库逐个模块迭代。

约束：
- 语料 = 完善版设计文档（`project-intro-rag` 的 rag-corpus 定义，8 节结构）。
- 检索/生成复用 `project-intro-rag` 的 rag-retrieval / rag-generation（双池、页面锚定、范围门、doubao 流式、usage）。
- 评测需要"可观测"：每轮 trace + 指标聚合 + 报告对比。
- 定位：内部评测工具，服务面试准备的质量把关，不是对外功能。

### Goals / Non-Goals

> 检索摘要：评测 agent 目标是知识库整理状态可跟踪、评测集覆盖概览/为什么/数据流/难点/指标，产出 hit@k 与 answer_quality 指标观测报告；不做线上评测服务、不引入 RAGAS 全量框架。

**Goals:**
- 知识库整理流程化、状态可跟踪（模块逐个：待整理 → 已整理 → 已切片 → 已索引 → 已评测）。
- 评测集（每模块 ≥5 条 Q&A，覆盖 概览/为什么/数据流/难点/指标 类型）。
- 评测 agent：跑评测集 → 算 `hit@k`（召回命中）、`answer_quality`（LLM 判分）、`cost`、`latency` → 输出观测报告。
- 观测：每轮 trace 可查（query/召回路径/得分/引用/token）、报告可对比（模块间、语料版本间）。
- 每个阶段可测试。

**Non-Goals:**
- 不做线上/生产评测服务——评测 agent 是离线/手动触发的质量把关工具。
- 不做 RAGAS 全量框架——聚焦 hit@k + LLM 判分两个核心信号。
- 不自动改语料——评测只报告问题，完善文档仍由人（+LLM 辅助）迭代。
- 不做真实用户反馈采集——评测集是预写的预期问答对。

### D1. 知识库整理 = 模块清单 + 状态机

> 检索摘要：知识库整理按固定模块清单（知识图谱/AI答疑/题型知识点/组织中心/RAG问答系统）加状态机 pending→evaluated 逐个推进，状态持久化到 _status.json，进度可见、单模块卡住不影响其他。

- 模块清单固定：知识图谱 / AI答疑 / 题型知识点 / 组织中心 / RAG 问答系统。
- 每模块状态机：`pending → organized → chunked → indexed → evaluated`，持久化到 `docs/project-intro/corpus/_status.json`。
- **为什么**：逐个模块推进，进度可见；一个模块卡住不影响其他。
- **备选**：一次性全量整理 → 工作量不可控、无法逐步验证，弃。

### D2. 评测集结构

> 检索摘要：评测集每条含 module/question/question_type/expected_references/expected_points，每模块5条共25条，预期引用与要点作为 hit@k 和答案质量的 ground truth。

每条：`{module, question, question_type, expected_references[], expected_points[]}`，每模块 5 条，共 25 条。
- `question_type` ∈ 概览/为什么/数据流/难点/指标——保证覆盖索引层 QA 的各类问题。
- **为什么**：预期引用/要点让 hit@k 和答案质量有 ground truth。

### D3. 评测 agent 流程

> 检索摘要：评测流程先走检索算 hit@k 再走生成与 LLM 判分 answer_quality，分层定位"检索捞不对"与"答案答不好"两类问题，避免端到端评测掩盖检索缺陷。

```
对每条评测问题:
  1. 走 rag-retrieval（页面锚定该模块）→ 记录召回 top-K 及其得分
  2. hit@k: 预期引用（references）是否命中召回集
  3. 走 rag-generation（doubao 生成）→ 记录答案、引用、usage
  4. LLM 判分: answer_quality(答案, 预期要点, 预期引用) → 0~5 分 + 理由
聚合: 每模块 + 全量 的 hit@k / 平均质量分 / 总成本 / 平均耗时
```

- **为什么**：先测"检索是否捞得对"（hit@k），再测"答案是否答得好"（质量分），分层定位问题。
- **备选**：只测端到端答案 → 检索问题被答案问题掩盖，无法定位，弃。
