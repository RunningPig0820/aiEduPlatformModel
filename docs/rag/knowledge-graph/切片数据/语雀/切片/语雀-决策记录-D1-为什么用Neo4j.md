# 为什么用 Neo4j 不用 MySQL/ES

> summary: 知识图谱为什么选 Neo4j？图遍历、前置依赖链查询、可解释路径，MySQL/ES 做不了多跳关系。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D1-为什么用Neo4j.md
> 类别：架构设计

---

### D1 为什么用 Neo4j 不用 MySQL/ES
> 检索摘要：知识图谱为什么选 Neo4j？图遍历、前置依赖链查询、可解释路径，MySQL/ES 做不了多跳关系。

| 属性 | 内容 |
|---|---|
| 背景 | 需支撑学习路径推荐和知识缺陷诊断，核心是知识点前置/后置依赖关系 |
| 演进 | 早期方案曾考虑关系库/全文检索 → 演进为图数据库 |
| 拍板理由 | 原生图查询支撑前置链路与关联召回；`neo4j-admin import` 对 CSV 批量导入是 TTL 导入 10 倍以上；十万级节点+百万级关系秒级导入 |
| 系统影响 | Neo4j 最终存储 7 类节点/8 类关系；社区版 4.4.x 单机 4G/100G+（实际 docker 5-enterprise 2G heap/1G pagecache） |
| 证据 | 证据：语雀-知识图谱数据清洗方案.md / design-python-2026-03-28-integrate-edukg-knowledge-graph.md D1 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D1）
