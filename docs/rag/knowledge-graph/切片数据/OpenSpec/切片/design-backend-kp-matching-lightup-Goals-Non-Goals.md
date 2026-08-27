# Goals / Non-Goals

> summary: 目标让 AI 题型可靠解析到教材知识点 URI、沉淀知识点题型库、掌握度主体翻转并派生层全自动维护闭环；不做 embedding 语义聚类与掌握度自动迁移。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-Goals-Non-Goals.md
> 类别：项目介绍

> 检索摘要：目标让 AI 题型可靠解析到教材知识点 URI、沉淀知识点题型库、掌握度主体翻转并派生层全自动维护闭环；不做 embedding 语义聚类与掌握度自动迁移。

**Goals:**
- 让 AI 题型可靠解析到教材知识点 URI（跨年级、可纠错、低置信挂起）。
- 从答疑数据沉淀"知识点的题型库"（个体派生 → 共现聚合 → 稳定），业务隔离。
- 掌握度主体翻转：题型直接观测落库（`t_student_topic_mastery`），知识点覆盖度运行时派生，学生端可见（绿/黄/红 + 疑似态）。
- 派生层全自动维护闭环（冲突检测 → 重判 → 回流先验），权威图零写入。

**Non-Goals:**
- **不写 Neo4j**；不做 embedding 语义聚类（后续大数据手段）。
- 不做消费方：变式题生成、错题本分组、薄弱点溯源（LangGraph 阶段 2 复用）。
- 不改变掌握度单调策略（保持"只升、显式纠正才降"）。
- 本期不做掌握度自动迁移（错解析回退只打标 + 人工复核，见 Decisions §6）。
- 本期不删除/迁移旧 KP 掌握度表 `t_student_kp_mastery`（并行过渡，见 Decisions §20）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§Goals / Non-Goals）
