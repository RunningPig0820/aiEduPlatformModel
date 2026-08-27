# 场景13 Neo4j 不可用（图谱关系降级）
> summary: Neo4j 挂了对前端影响什么？图谱关系直查降级——Redis TTL 300s 缓存 + neo4jAvailable:false 隐藏模块，不抛异常。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-边界场景清单-场景13-Neo4j不可用降级.md
> 类别：开发难点

| 属性 | 内容 |
|---|---|
| 触发条件 | Neo4j 服务不可用/网络故障 |
| 当前处理 | Redis key `kg:neo4j:{uri}:{query_type}` TTL 300s；降级返回空关联 + `neo4jAvailable:false` 前端隐藏图谱关系模块 |
| 兜底 | `/api/kg/neo4j/health` 健康检查；批量概念关联避免 N+1 |
| 风险 | 缓存与实时数据不一致（300s 窗口） |
| 证据 | 证据：design-backend-ui Decision 5 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（场景13）
