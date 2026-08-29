# 选型1 图谱存储：Neo4j vs MySQL vs ES
> summary: 知识图谱为什么选 Neo4j 不用 MySQL/ES？图遍历、前置依赖链查询、可解释路径，CSV 批量导入 10 倍性能。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型1-为什么不用MySQL和ES.md
> 类别：架构设计

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| Neo4j | 原生图查询/前置链/可解释路径/批量导入快 | 运维成本 | 采用 |
| MySQL | 成熟/团队熟 | 多跳查询难 | 否决 |
| ES | 全文检索强 | 无图语义 | 否决 |
| 证据 | 证据：语雀-知识图谱数据清洗方案.md / design-integrate-edukg D1 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型1）
