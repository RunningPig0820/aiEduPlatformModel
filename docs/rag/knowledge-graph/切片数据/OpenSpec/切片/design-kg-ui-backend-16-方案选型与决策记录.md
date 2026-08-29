# 方案选型与决策记录

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-16-方案选型与决策记录.md
> 类别：架构设计

---

> 检索摘要：知识图谱 UI 后端做了哪些关键选型？为什么选方案 B 同步 Neo4j 到 MySQL 而不实时查询？URI 主键还是自增 ID？导航树怎么从 4 级扩到 6 级？

本文档（design-backend-2026-06-03-knowledge-graph-ui）在设计阶段的关键选型与决策记录：

D1 数据方案：选方案 B —— Neo4j 节点同步到 MySQL（存核心节点属性和层级关系，供导航与进度统计），图谱关系（MATCHES_KG/PART_OF/RELATED_TO）不同步、后续直接查 Neo4j。表设计 8 张（4 节点主表 + 3 层级关联表 + 1 同步记录表）。

D2 同步策略：手动按需触发（非 CDC/实时监听），按 URI UPSERT，整个同步在一个 Spring @Transactional 大事务内保证原子性；状态机 active/deleted/merged，查询过滤 deleted 但进度查询例外。

D3 并发控制：MySQL 应用层行锁（SELECT ... FOR UPDATE）或 Redis 分布式锁，保证同一时间仅一个同步任务。

D4 数据库索引：主键外对 grade/subject/phase/topic/status 等常用查询字段加索引，层级关联表加 (子uri, order_index) 排序索引。

D5 图谱查询降级：图谱关系查 Neo4j 加 Redis 缓存（key kg:neo4j:{uri}:{query_type}，TTL 300s）；Neo4j 不可用返回空关联降级（前端 neo4jAvailable: false），提供 batch-relations 与 health 接口。

D6 主键选型：MySQL 主表以 uri 为主键（非自增 ID），URI 是 Neo4j 天然唯一标识，格式校验（http://edukg.org/knowledge/ 开头）且生成后永不修改。

D7 Domain 建模：JPA Entity 主键为 URI（String），Repository 用 Spring Data JPA + MyBatis-Plus 混合，含关联表 Entity 与值对象枚举（KgNodeStatus: active/deleted/merged）。

D8 分层架构：对齐现有 Domain/Infrastructure/Application/Interface 四层，同步与导航分别由 KgSyncAppService / KgNavigationAppService 负责，接口层为 KnowledgeGraphController（/api/kg/**）。

D9 前端对接：后端负责 API 设计和 DTO 定义，前端按 API 文档开发；知识点详情 DTO 返回 2 层父级（小节 + 章节）不过度展示。

D10 下拉选型：同步对话框下拉用枚举 + MySQL 混合 —— 学科/学段/教材来自 Java 枚举，年级从 t_kg_textbook DISTINCT grade 查询；首次需先全量同步才有年级数据。

D11 导航树：从 4 级（教材→章节→小节→知识点）扩为 6 级（学科→年级→教材→章节→小节→知识点），新增 subjects/grades/textbooks 接口，数据均来自 t_kg_textbook 聚合查询。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D1~D11 决策）
