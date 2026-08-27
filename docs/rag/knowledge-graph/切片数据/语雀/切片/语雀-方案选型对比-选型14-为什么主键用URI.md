# 选型14 图谱数据主键：URI vs 自增 ID
> summary: 图谱节点主键用哪个？URI（非自增 ID），生成后永不修改、跨 Neo4j/MySQL 对齐、改动走合并流程。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型14-为什么主键用URI.md
> 类别：架构设计

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| URI 主键 | 跨源唯一/可对齐图谱 | VARCHAR 性能（<1 万节点可行） | ✅ 采用 |
| 自增 ID | 性能好 | 无法跨源对齐/漂移 | ❌ 否决 |
| 证据 | 证据：design-backend-ui Decision 6 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型14）
