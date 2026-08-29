# Java 同步 MySQL 怎么保证两边数据一致？

> summary: 架构设计引导问题回答：四重保证——手动按需按URI UPSERT幂等可重跑+状态机active/deleted/merged软删可回溯+单大事务内重建关联表+同步后MySQL vs Neo4j计数对账
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-42-架构设计-Java同步MySQL怎么保证两边数据一致.md
> 类别：架构设计

**核心结论**：四重保证——手动按需（非 CDC）按 URI UPSERT 幂等可重跑 + 状态机 active/deleted/merged 软删可回溯 + 单大事务内重建关联表 + 同步后 MySQL vs Neo4j 计数对账；并发用行锁/分布式锁 + 卡死检测兜底。

## 分层展开
- **UPSERT 幂等**：按 URI 主键 `INSERT ... ON DUPLICATE KEY UPDATE` 写入节点主表，失败可重跑不重复（UPSERT 幂等）。（依据：分析-11 / 完善文档 03）
- **状态机软删**：所有主表带 `status` 与 `merged_to_uri`——active（正常）/ deleted（Neo4j 已删，进度查询例外含历史）/ merged（被合并，运营经 merged_to_uri 做进度迁移）；导航/知识体系查询过滤 `WHERE status='active'`，删除可回溯、进度历史不丢。（依据：分析-11 / 完善文档 03）
- **单大事务**：关联表先清空本层再重新 INSERT（含 order_index），单事务保证提交前前端看不到中间态；失败回滚可重新触发。（依据：分析-11 / 完善文档 03）
- **对账校验**：同步完成对比 MySQL vs Neo4j 节点数/关联数，不一致写 `reconciliation_status=mismatched` + `reconciliation_details`。（依据：分析-11 / 完善文档 03）
- **并发控制与卡死防护**：同步用 MySQL 行锁 `SELECT ... FOR UPDATE` 或 Redis 分布式锁，同一时间仅一个同步任务；J-KG11 落地按年级拆子任务 + Redis 分布式锁 + 卡死检测（超过 10 分钟 running 标记 failed，解除僵尸阻塞）+ 每个年级独立对账。（依据：分析-11 / 坑档案 J-KG11）
- **落地边界**：以上 8 张表/@DS 双数据源/状态机/对账均为 design-backend-ui 文档口径（D1/D2/D3），Java 代码不在本仓，分析-11 明确"非代码真值"——真实实现细节以 Java 仓为准。（依据：分析-11 / 完善文档 03）

## 追问防御
- **可能追问：同步和前端数据一致性怎么保证？** → 单大事务内重建关联表，提交前前端看不到中间态；失败回滚，UPSERT 幂等可重跑。（依据：分析-11）
- **可能追问：同步卡死/并发触发怎么办？** → J-KG11 卡死检测：超过 10 分钟的 running 记录标记 failed 解除阻塞；Redis 分布式锁防并发，锁粒度 `edition:subject:stage:grade`。（依据：坑档案 J-KG11）
- **可能追问：图谱关系也同步吗？** → 不同步——MATCHES_KG/PART_OF/RELATED_TO 等图谱关系直查 Neo4j（Redis TTL 300s + 空关联降级），避免无限业务事实污染权威图谱。（依据：分析-11 / 完善文档 03）

> 证据：详见 `3.代码/分析-11-Java同步与前端页面.md` ｜ `4.完善文档/03-架构与三端分工.md` ｜ `5.难点/坑档案.md（J-KG11）`
