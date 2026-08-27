# 先纯分析展示

> summary: 展示=先纯分析（题型+知识点清单），掌握度标注预留（数据到位自然亮），PENDING 需覆盖有/无候选。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D3-先纯分析展示.md
> 类别：操作流程

---

### 决策 3：展示 = 先纯分析（题型 + 关联知识点清单），掌握度标注预留

> 检索摘要：展示=先纯分析（题型+知识点清单），掌握度标注预留（数据到位自然亮），PENDING 需覆盖有/无候选。

单题分析结果展示「题型 + 关联知识点（kpLabel + 年级分布 + 占比 ratio）」清单。掌握度标注（叠加「你已掌握/待巩固」）第一版不做，但前端数据层预留：`analyze-question` 返回 kpUri，前端可查 `kp-coverage` 的 `coverageMap` 有则标、无则灰，待数据到位自然点亮。

**PENDING 分支需处理两种**：后端 WEAK（LLM 冷启动猜测）现在也返回 `PENDING`（不再冒充 RESOLVED），故 PENDING 出现频率变高，需同时处理「有 candidates（可确认）」与「candidates 空（仅空态提示）」。

理由：现在 `kp-coverage` 数据是空的（题型掌握度表空），第一版标了也全是灰。先跑通「贴题→分析→展示」主流程。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 3）｜ 语雀-决策记录.md D21 ｜ 完善文档 02-题型分析主流程怎么走.md
