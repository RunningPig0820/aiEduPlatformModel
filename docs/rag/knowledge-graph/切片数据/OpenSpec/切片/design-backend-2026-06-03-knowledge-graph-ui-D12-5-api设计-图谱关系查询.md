# D12.5：API 设计 - 图谱关系查询

> summary: 图谱关系API直接查Neo4j：概念关联图、批量关联、知识点到概念完整路径与Neo4j健康检查，含Redis缓存。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D12-5-api设计-图谱关系查询.md
> 类别：架构设计

> 检索摘要：图谱关系API直接查Neo4j：概念关联图、批量关联、知识点到概念完整路径与Neo4j健康检查，含Redis缓存。

```
GET  /api/kg/concepts/{uri}/relations - 获取概念关联图（Neo4j，含 Redis 缓存）
GET  /api/kg/concepts/batch-relations - 批量获取概念关联图（避免 N+1）
GET  /api/kg/knowledge-points/{uri}/path - 获取知识点到概念的完整路径（Neo4j）
GET  /api/kg/neo4j/health            - Neo4j 健康检查
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D12.5：API 设计 - 图谱关系查询）
