# D5：Neo4j 查询降级与缓存

> summary: 决策：图谱关系查询加Redis缓存TTL 5分钟，Neo4j不可用时返回空关联降级，提供batch-relations与health接口。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D5-neo4j查询降级与缓存.md
> 类别：架构设计

> 检索摘要：决策：图谱关系查询加Redis缓存TTL 5分钟，Neo4j不可用时返回空关联降级，提供batch-relations与health接口。

**决策**: 图谱关系查询（直接查 Neo4j）在应用层加短期缓存（Redis，TTL 5 分钟），并提供降级机制。

- **缓存策略**: 查询结果存入 Redis，key 为 `kg:neo4j:{uri}:{query_type}`，TTL = 300s
- **降级机制**: Neo4j 不可用时，返回空关联数据，不抛异常。前端通过 `neo4jAvailable: false` 标识隐藏图谱模块
- **批量查询**: 提供 `/api/kg/concepts/batch-relations` 接口，一次性传入多个 URI，避免 N+1 查询
- **健康检查**: `/api/kg/neo4j/health` 接口定期检查 Neo4j 连接状态

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D5：Neo4j 查询降级与缓存）
