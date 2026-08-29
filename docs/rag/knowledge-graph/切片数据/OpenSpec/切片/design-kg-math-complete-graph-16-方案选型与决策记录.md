# 方案选型与决策记录

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-16-方案选型与决策记录.md
> 类别：架构设计

---

> 检索摘要：kg-math-complete-graph 做了哪些关键选型？粗筛为什么选向量检索？单元层级为什么选方案 B？各决策理由是什么？

本文档（kg-math-complete-graph）在设计阶段的关键选型与决策记录：

D1 目录结构设计：核心代码进 edukg/core/textbook 与 edukg/core/llm_inference，scripts 只做命令行入口。

D2 两阶段流程：第一阶段数据生成（无 LLM），第二阶段 LLM 增强（推断 + 匹配），支持断点续传。

D4.2 粗筛方式选型：对比 difflib（字符相似度，无依赖快但语义弱）与向量检索（Embedding 语义匹配，强但需装依赖），采纳向量检索方案，粗筛 top-20 候选再 LLM 投票。

D4.3 向量检索技术选型：Embedding 用 BAAI/bge-small-zh-v1.5（中文小模型 SOTA，512 维，2-4GB）；索引用 numpy 暴力搜索（图谱 ≤5000 条，<10ms）；依赖库 sentence-transformers。资源评估约 3.5GB，低于 8GB 限制。

D5 断点续传选型：所有 LLM 任务集成 llmTaskLock（TaskState + CachedLLM + ProcessLock），--resume 续传；纯 JSON 数据生成与精确匹配不需要。

D12 单元/专题层级选型：对比方案 A（新增 Unit 节点，结构清晰支持跨年级专题但需改数据模型）、方案 B（Chapter 增加 topic 字段，改动小不影响现有关系但无法细化到节）、方案 C（Section 增加 unit_id 字段，简单但需人工或 LLM 划分）。采纳方案 B，后续迭代可扩展为方案 A。

D13 多版本教材：URI 从隐含版本扩展为 {edition}-{grade}{semester}，数据模型加 version_code；当前阶段不实现，列为 Non-Goals，v3.2 规划。

D7/D8 数据模型与 URI：节点 Textbook/Chapter/Section/TextbookKP（uri UNIQUE/id UNIQUE 约束），关系 CONTAINS/IN_UNIT/MATCHES_KG；URI v3.1 规范 http://edukg.org/knowledge/3.1/{type}/math#{id}。

匹配阈值选型：≥0.9 建 MATCHES_KG，0.7-0.9 建 MATCHES_KG_CANDIDATE，<0.7 不匹配（双模型投票 + 置信度阈值 + 候选关系保留兜底）。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D1-D13 决策）
