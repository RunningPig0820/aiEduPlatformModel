# 边界场景与兜底

> summary: 边界场景与兜底
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-13-边界场景与兜底.md
> 类别：开发难点

---

> 检索摘要：同步耗时、并发冲突、事务原子性、URI 脏数据、Neo4j 不可用、首次下拉为空等边界场景各自的风险与兜底措施是什么？还有哪些开放问题？

## 风险与权衡（Risks / Trade-offs）

| 风险 | 缓解措施 |
|------|----------|
| Neo4j 同步耗时长 | UPSERT 批量写入 + 事务控制，6,757 节点预计 < 10s |
| 同步并发冲突 | MySQL 应用层锁或 Redis 分布式锁，同一时间仅一个同步任务 |
| 同步期间前端看到空数据 | 整个同步在事务内执行，提交前前端看不到中间状态 |
| 状态变更导致 MySQL 数据膨胀 | status='deleted' 的数据定期清理（需确认无下游引用后物理删除） |
| 层级关联表重建开销 | 关联表无状态，每次同步先 DELETE 再 INSERT，简单可靠 |
| 图谱关系与 MySQL 不同步 | 层级关系同步到 MySQL，图谱关系实时查 Neo4j，不存在不一致 |
| 前端跨域问题 | Java 后端配置 CORS |
| Neo4j 服务不可用 | Redis 缓存 + 降级机制，Neo4j 不可用时返回空关联，不影响 MySQL 导航 |
| URI 脏数据写入 | 同步时校验 URI 格式/非空/唯一性，异常记录日志并跳过 |
| 同步后数据不一致 | 对账校验：同步完成自动对比 MySQL vs Neo4j 节点数/关联数 |
| URI 主键性能问题 | 当前 < 1 万节点，VARCHAR(255) 主键完全可行；若后续暴涨可引入整型代理键 |
| 首次使用下拉选项为空 | 提示用户先执行全量同步，t_kg_textbook 有数据后下拉选项自动可用 |

## 开放问题（Open Questions）

已确认，无遗留问题。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§Risks / Trade-offs 风险与权衡、§Open Questions 开放问题）
