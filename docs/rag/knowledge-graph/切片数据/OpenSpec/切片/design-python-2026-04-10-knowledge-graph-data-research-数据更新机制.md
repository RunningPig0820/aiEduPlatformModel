# 十二、数据更新机制（Demo 阶段）
> summary: Demo 数据更新机制：edukg 基准知识点冻结只读，仅增量补充题目-知识点关联，CSV 按版本命名，长期维护待正式迭代。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-数据更新机制.md
> 类别：数据存储

> 检索摘要：Demo 数据更新机制：edukg 基准知识点冻结只读，仅增量补充题目-知识点关联，CSV 按版本命名，长期维护待正式迭代。

方面	策略
基准数据	edukg 静态权威库，知识点永久冻结只读
维护规则	仅增量补充「题目-知识点」关联，不修改基准知识点
版本管理	CSV 文件命名区分（如 knowledge_points_v1.csv）
长期维护	Demo 阶段不考虑，正式迭代再设计

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十二、数据更新机制（Demo 阶段））
