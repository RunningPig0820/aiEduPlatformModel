# 同步策略与状态机

> summary: 同步策略与状态机
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-10-页面化与服务化-3.md
> 类别：操作流程

---

> 检索摘要：Neo4j 数据怎么同步到 MySQL？为什么按需触发不实时监听？UPSERT 和状态机 deleted/merged 怎么保证数据一致？并发怎么锁？同步表索引怎么设计？

## 同步策略：按需触发 + UPSERT + 状态机（D2）

同步为手动按需触发（非实时监听/CDC），同步粒度为教材-学科-年级维度。采用 UPSERT 策略（按 URI 判断），同步节点属性和层级关系。图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等）不同步到 MySQL，后续通过 Neo4j 直接查询。

同步范围：

| 同步对象 | MySQL 操作 | Neo4j 角色 |
|---------|-----------|-----------|
| 节点属性 | 根据 URI UPSERT 到主表 | 数据源 |
| 层级关系 | 同步 CONTAINS/IN_UNIT 到关联表（含 order_index） | 数据源 |
| 图谱关系 | 不同步 | 直接提供查询服务 |

同步流程：
1. 获取同步锁（MySQL 应用层锁或 Redis 分布式锁）
2. 后端连接 Neo4j，依次查询：节点 Textbook → Chapter → Section → TextbookKP；层级关系 CONTAINS（含 order_index）、IN_UNIT
3. URI 校验：拦截非法 URI（空值、重复、格式异常），记录到同步日志并跳过
4. 按 URI 执行 UPSERT（整个同步流程在一个大事务内）：节点主表 INSERT ... ON DUPLICATE KEY UPDATE；关联表先清空该层级全部关联再重新 INSERT（order_index 从 Neo4j 关系属性读取）
5. 标记 MySQL 中有但 Neo4j 中无的记录为 status = 'deleted'（知识点表还需设置 merged_to_uri 如已知合并目标）
6. 对账校验：同步完成后对比 MySQL 与 Neo4j 的节点数/关联数，不一致则记录警告
7. 记录同步结果到 t_kg_sync_record（含 reconciliation_status 字段）
8. 释放同步锁，返回同步统计

同步失败处理：同步失败后用户可重新触发，从头执行。因为 UPSERT 是幂等的且整个流程在事务内，失败会自动回滚，不会导致重复数据或半清空状态。后续全量同步也是基于教材-学科-年级维度生成多个同步任务。

同步事务原子性保证：
- 整个同步流程（节点 UPSERT + 关联表重建 + 状态变更 + 对账校验）在一个 Spring @Transactional 事务内执行
- 关联表重建期间，前端导航查询看到的是旧数据（事务未提交前不可见），避免「空目录」问题
- 同步完成后事务提交，前端立即看到新数据，无中间状态

支持定向同步参数：
- POST /api/kg/sync/full 支持可选参数：subject（学科）、phase（学段）、grade（年级）、textbookUri（指定教材）
- 不传参数则全量同步所有数据
- 同步记录表 t_kg_sync_record 增加 scope 字段（JSON 格式）记录本次同步范围

状态机说明：

| 状态 | 含义 | 查询行为 |
|------|------|---------|
| active | 正常节点 | 正常展示 |
| deleted | Neo4j 中已删除 | 导航/知识体系查询中过滤掉（视为不存在），但进度记录不受影响（进度查询不过滤 deleted） |
| merged | 被合并到其他知识点 | 同上过滤，运营可通过 merged_to_uri 做进度迁移 |

查询过滤：所有导航/知识体系查询自动加 WHERE status = 'active'。进度查询例外：学习进度查询需要包含已删除知识点的历史记录，通过 isDeprecated 字段标识，前端展示为「已归档」。

## 并发控制：MySQL 同步锁（D3）

同步接口使用 MySQL 应用层行锁（SELECT ... FOR UPDATE on a sync lock row）或 Redis 分布式锁，确保同一时间只有一个同步任务执行。

## 数据库索引设计（D4）

除主键外，对常用查询字段添加索引。

```sql
-- 教材表查询索引
CREATE INDEX idx_kg_textbook_grade ON t_kg_textbook(grade);
CREATE INDEX idx_kg_textbook_subject ON t_kg_textbook(subject);
CREATE INDEX idx_kg_textbook_phase ON t_kg_textbook(phase);

-- 章节表查询索引
CREATE INDEX idx_kg_chapter_topic ON t_kg_chapter(topic);

-- 知识点表查询索引
CREATE INDEX idx_kg_kp_status ON t_kg_knowledge_point(status);
CREATE INDEX idx_kg_kp_label ON t_kg_knowledge_point(label(100));
CREATE INDEX idx_kg_kp_difficulty ON t_kg_knowledge_point(difficulty);
CREATE INDEX idx_kg_kp_merged ON t_kg_knowledge_point(merged_to_uri(100));

-- 层级关联表排序索引
CREATE INDEX idx_kg_tc_chapter ON t_kg_textbook_chapter(chapter_uri, order_index);
CREATE INDEX idx_kg_cs_section ON t_kg_chapter_section(section_uri, order_index);
CREATE INDEX idx_kg_sk_kp ON t_kg_section_kp(kp_uri, order_index);

-- 同步记录表查询索引
CREATE INDEX idx_kg_sync_status ON t_kg_sync_record(status, started_at);
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D2 同步策略、§D3 并发控制、§D4 索引设计）
