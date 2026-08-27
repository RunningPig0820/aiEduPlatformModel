# 分析-11-Java同步与前端页面-代码事实

> summary: Java同步与前端页面代码事实
> 来源: 切片 ｜ 锚点: 代码事实
> 节: 分析-11-Java同步与前端页面
> COS路径: rag-slices/knowledge-graph/代码/分析-11-Java同步与前端页面-代码事实.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

> 本节约束：以下全部为 design 文档描述（`design-backend-*-knowledge-graph-{datasource,ui}.md` / `design-frontend-*-knowledge-graph-ui-front.md`），**代码实现不在本仓，未真读，非代码真值**。

### 数据模型：8 张表（design-backend-ui D1）
| 表 | 用途 | 主键 |
|---|---|---|
| t_kg_textbook | 教材 | uri VARCHAR(255) |
| t_kg_chapter | 章节 | uri |
| t_kg_section | 小节 | uri |
| t_kg_knowledge_point | 知识点（全局存储，下游关联引用） | uri |
| t_kg_textbook_chapter | 教材→章节 层级（order_index） | (textbook_uri, chapter_uri) |
| t_kg_chapter_section | 章节→小节 层级（order_index） | (chapter_uri, section_uri) |
| t_kg_section_kp | 小节→知识点 层级（order_index） | (section_uri, kp_uri) |
| t_kg_sync_record | 同步记录（scope/status/inserted/updated/reconciliation） | id BIGINT 自增 |

### 双数据源与状态机
1. **@DS("kg") 双数据源**：`dynamic-datasource-spring-boot3-starter`，业务 Mapper（`persistence.mapper.*`）默认 user 库，图谱 Mapper（`persistence.edukg.mapper.*`）加 `@DS("kg")` 路由 ai_edu_kg；`primary: user`、`strict: true`（未匹配数据源抛异常）；`@Transactional` 默认绑 user，图谱 Service 用 `@Transactional("kg")`；Flyway 按库分组且**当前全禁用，表手动创建**（design-backend-datasource 1-6）。
2. **状态机 active/deleted/merged**：所有主表带 `status` 与 `merged_to_uri`；导航/知识体系查询过滤 `WHERE status='active'`；deleted=Neo4j 已删（进度查询例外，含历史），merged=被合并（运营经 merged_to_uri 做进度迁移）（design-backend-ui D2）。
3. **对账校验**：同步完成对比 MySQL vs Neo4j 节点数/关联数，不一致写 `reconciliation_status=mismatched` + `reconciliation_details`（design-backend-ui D1/D2）。
4. **并发控制**：同步用 MySQL 行锁 `SELECT ... FOR UPDATE` 或 Redis 分布式锁，同一时间仅一个同步任务（D3）。
5. **Neo4j 关系查询降级**：Redis key `kg:neo4j:{uri}:{query_type}` TTL 300s；Neo4j 不可用返回空关联 + `neo4jAvailable:false`，不抛异常；批量接口 `/api/kg/concepts/batch-relations` 避免 N+1（D5）。

### 枚举/常量/配置
| 类型 | 名称 | 取值 | 出处 |
|---|---|---|---|
| 数据源 | primary / strict | user / true | design-backend-datasource:96-101 |
| 数据源 | kg 库 | ai_edu_kg | design-backend-datasource:108 |
| 连接池 | hikari minimum-idle / maximum-pool-size | 5 / 20 | design-backend-datasource:112-114 |
| 缓存 | kg:neo4j:{uri}:{query_type} TTL | 300s（5 分钟） | design-backend-ui D5 |
| 状态 | KgNodeStatus | active / deleted / merged | design-backend-ui D7 |
| 学科枚举 | KgSubjectEnum | math/chinese/english/physics/chemistry/biology | design-backend-ui D10 |
| 学段枚举 | KgPhaseEnum | primary/middle/high | design-backend-ui D10 |
| 教材枚举 | KgTextbookEnum | pep-math-primary-g1-v1 等 | design-backend-ui D10 |
| URI 前缀校验 | 以 `http://edukg.org/knowledge/` 开头 | design-backend-ui D6 |
| 详情父级 | 2 层（小节 + 章节） | design-backend-ui D9 |
| 前端简化视图 | 节点 >50 时仅显示 Top 10 | design-frontend:134 |

> 证据：详见 `3.代码/分析-11-Java同步与前端页面.md`（§代码事实 数据模型 / 双数据源与状态机 / 枚举常量配置）
