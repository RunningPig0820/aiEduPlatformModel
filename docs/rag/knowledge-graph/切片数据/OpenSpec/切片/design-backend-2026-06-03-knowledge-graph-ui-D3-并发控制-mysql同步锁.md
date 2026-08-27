# D3：并发控制：MySQL 同步锁

> summary: 决策：同步接口用MySQL应用层行锁SELECT FOR UPDATE或Redis分布式锁，确保同一时间只有一个同步任务执行。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D3-并发控制-mysql同步锁.md
> 类别：架构设计

> 检索摘要：决策：同步接口用MySQL应用层行锁SELECT FOR UPDATE或Redis分布式锁，确保同一时间只有一个同步任务执行。

**决策**: 同步接口使用 MySQL 应用层行锁（`SELECT ... FOR UPDATE` on a sync lock row）或 Redis 分布式锁，确保同一时间只有一个同步任务执行。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D3：并发控制：MySQL 同步锁）
