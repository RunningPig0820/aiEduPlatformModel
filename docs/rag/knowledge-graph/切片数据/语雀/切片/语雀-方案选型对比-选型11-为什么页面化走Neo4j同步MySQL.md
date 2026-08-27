# 选型11 页面化同步：Neo4j→MySQL 同步 vs Neo4j 实时查询
> summary: 图谱页面化用哪种？方案 B——Neo4j→MySQL 同步、前端读 MySQL，图谱关系直查 Neo4j + Redis 缓存降级，不做实时查询。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型11-为什么页面化走Neo4j同步MySQL.md
> 类别：架构设计

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| Neo4j→MySQL 同步（方案 B） | 前端轻量/查库快/物理隔离 | 需同步机制 | ✅ 采用 |
| Neo4j 实时查询 | 数据实时 | 前端重/连接管理复杂 | ❌ 否决 |
| 证据 | 证据：语雀-页面化-ui-design.md / design-backend-ui Decision 2 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型11）
