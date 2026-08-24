# 页面化-ui-tasks（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/gog0ky55pqr467gs
> 字数：3134 ｜ 下载：2026-08-24

## 1. 数据库与基础设施

- [x] 1.1 设计 MySQL 表结构：4 张节点主表（uri 主键，status 枚举 + merged_to_uri）+ 3 张层级关联表（含 order_index，无软删除）+ 1 张同步记录表（含 scope/reconciliation_status/details JSON 字段）
- [x] 1.2 创建 Flyway 迁移脚本 `V1__init_knowledge_graph.sql`
- [x] 1.3 在 `ai-edu-infrastructure/pom.xml` 添加 `neo4j-java-driver` 依赖
- [x] 1.4 在 `application.yml` 添加 Neo4j 连接配置
- [x] 1.5 创建 `Neo4jConfig` 配置类，初始化 Neo4j Driver Bean（含连接池配置）
- [x] 1.6 在 `ErrorCode.java` 增加知识图谱错误码段（7xxxx）
- [x] 1.7 创建数据库索引：t_kg_textbook(grade/subject/phase) + t_kg_knowledge_point(status/label/difficulty) + 关联表排序索引

## 2. Domain 层建模

- [x] 2.1 创建 `domain/edukg/model/entity/` 目录及 4 个节点实体类（KgTextbook, KgChapter, KgSection, KgKnowledgePoint），主键为 URI（String）
- [x] 2.2 创建 `domain/edukg/model/entity/relation/` 目录及 3 个关联实体类（KgTextbookChapter, KgChapterSection, KgSectionKP），复合主键 + orderIndex
- [x] 2.3 创建 `domain/edukg/model/entity/KgSyncRecord.java` 同步记录实体（含 scope/reconciliationStatus/details 字段）
- [x] 2.4 创建 `domain/edukg/model/valueobject/` 枚举类（KgDifficulty, KgImportance, KgCognitiveLevel, KgNodeStatus）
- [x] 2.5 创建 `domain/edukg/repository/` 目录及 7 个 Repository 接口（4 节点 + 3 关联）

## 3. Infrastructure 层实现

- [x] 3.1 创建 `infrastructure/persistence/repository/` 目录下 JPA Repository 实现（7 个：4 节点 + 3 关联）+ 7 个 MyBatis Mapper（@Select 注解 + 软删除过滤 + 批量操作）
- [x] 3.2 创建 `infrastructure/persistence/neo4j/Neo4jKgSyncService.java` Neo4j 同步服务
- [x] 3.3 实现 Neo4j 查询节点并映射为 MySQL Entity（按 URI）- 4 类节点通用查询映射
- [x] 3.4 实现 Neo4j 查询层级关系（CONTAINS/IN_UNIT，含 order_index）并映射为关联 Entity - 3 类关系查询映射
- [x] 3.5 实现 UPSERT 批量写入逻辑（按 URI 判断 INSERT/UPDATE，关联表全量重建）
- [x] 3.6 实现关联表 UPSERT 同步逻辑（按复合键对比 Neo4j 与 MySQL 记录，差异化执行 INSERT / UPDATE order_index / 软 DELETE，而非全量 DELETE + INSERT）
- [x] 3.7 实现状态变更逻辑（MySQL 中有但 Neo4j 中无的标记 `status = 'deleted'`）
- [x] 3.8 实现同步记录写入与更新逻辑（含 insertedCount/updatedCount/statusChangedCount/scope/reconciliationStatus 统计）
- [x] 3.9 实现 URI 校验逻辑（非空/格式/重复检查，异常记录到同步日志并跳过）
- [x] 3.10 实现同步对账校验逻辑（同步完成后对比 MySQL vs Neo4j 节点数/关联数）
- [x] 3.11 创建 `infrastructure/cache/Neo4jRelationCacheService.java` Redis 缓存服务（TTL 300s）
- [x] 3.12 创建 `infrastructure/neo4j/Neo4jRelationQueryService.java` Neo4j 图谱关系查询服务（含降级机制）
- [x] 3.13 实现 Neo4j 健康检查逻辑（连接测试 + 响应时间）

## 4. Application 层服务

- [x] 4.1 创建 `application/dto/kg/` 目录及响应 DTO（KgTextbookDTO, KgChapterDTO, KgSectionDTO, KgKnowledgePointDTO, KgGradeSystemDTO, KgGradeStatsDTO, KgSyncStatusDTO, KgBatchRelationsDTO）
- [x] 4.2 创建 MapStruct 转换器 `KgConvert.java`
- [x] 4.3 创建 `infrastructure/service/KgSyncAppService.java` 同步应用服务
- [x] 4.4 创建 `infrastructure/service/KgNavigationAppService.java` 导航查询服务
- [x] 4.5 创建 `infrastructure/service/KgKnowledgeSystemAppService.java` 知识体系服务
- [x] 4.6 创建 `infrastructure/service/KgNeo4jService.java` Neo4j 查询服务（含缓存 + 降级）
- [x] 4.7 实现 `syncFull(subject, phase, grade, textbookUri)` 全量/定向同步方法（**整个流程在 @Transactional 事务内**：同步锁、URI 校验、UPSERT、关联表重建、状态变更、对账校验）
- [x] 4.8 实现 `getSyncStatus()` 同步状态查询（含 reconciliationStatus）
- [x] 4.9 实现 `getSyncRecords()` 同步历史查询（含 scope/reconciliationStatus）
- [x] 4.10 实现 `getTextbooks(subject, phase)` 教材列表查询
- [x] 4.11 实现 `getChaptersByTextbook(textbookUri)` 章节树查询（JOIN 关联表，含 orderIndex，空章节过滤）
- [x] 4.12 实现 `getKnowledgePointsBySection(sectionUri)` 知识点查询（JOIN 关联表）
- [x] 4.13 实现 `getKnowledgePointDetail(kpUri)` 知识点详情（含 2 层父级）
- [x] 4.14 实现 `getGradeSystem(grade, groupBy)` 年级知识体系
- [x] 4.15 实现 `getGradeStats(grade)` 年级知识点统计
- [x] 4.16 实现 `getNeo4jHealth()` Neo4j 健康检查
- [x] 4.17 实现 `batchGetConceptRelations(uris)` 批量获取概念关联（Redis 缓存 + 降级）

## 5. Interface 层 API

- [x] 5.1 创建 `interface_/api/KnowledgeGraphController.java`
- [x] 5.2 实现 `POST /api/kg/sync/full` 同步接口（支持可选 subject/phase/grade/textbookUri 参数）
- [x] 5.3 实现 `GET /api/kg/sync/status` 同步状态接口
- [x] 5.4 实现 `GET /api/kg/sync/records` 同步历史接口
- [x] 5.5 实现 `GET /api/kg/textbooks` 教材列表接口
- [x] 5.6 实现 `GET /api/kg/textbooks/{uri}/chapters` 章节树接口（URI 需要 URL 编码）
- [x] 5.7 实现 `GET /api/kg/sections/{uri}/points` 知识点列表接口
- [x] 5.8 实现 `GET /api/kg/knowledge-points/{uri}` 知识点详情接口（返回 2 层父级）
- [x] 5.9 实现 `GET /api/kg/system/grade/{grade}` 年级知识体系接口
- [x] 5.10 实现 `GET /api/kg/system/stats/{grade}` 年级统计接口
- [x] 5.11 实现 `GET /api/kg/neo4j/health` Neo4j 健康检查接口
- [x] 5.12 实现 `POST /api/kg/concepts/batch-relations` 批量概念关联接口
- [x] 5.13 为所有接口添加 `ApiResponse<T>` 统一包装和 CORS 配置

## 6. 单元测试

### 6.1 Domain 层 — 实体与值对象

> 测试目标：工厂/方法、状态转换、行为方法

- [x] 6.1.1 `KgTextbookTest` — `create()` 方法（验证 status 默认 active、字段正确赋值）、`markDeleted()` 方法（验证 status 变为 merged、mergedToUri 设置）、`isMerged()` 方法
- [x] 6.1.2 `KgChapterTest` — `create()` 方法、`updateTopic()` 方法
- [x] 6.1.3 `KgSectionTest` — `create()` 方法
- [x] 6.1.4 `KgKnowledgePointTest` — `create()` 方法、`updateAttributes()` 方法、`isHighImport()` 方法
- [x] 6.1.5 `KgSyncRecordTest` — `create()` 方法、`completeSuccess()` 方法、`completeFailure()` 方法
- [x] 6.1.6 关联实体测试 — `KgTextbookChapter.create()`、`KgChapterSection.create()`、`KgSectionKP.create()`（验证字段正确赋值、orderIndex 默认 0）
- [x] 6.1.7 值对象枚举测试 — `KgDifficulty`、`KgImportance`、`KgCognitiveLevel`、`KgNodeStatus`（验证 getValue() 返回正确、fromValue() 逆向转换）

### 6.2 Domain 层 — 领域服务接口

> 测试目标：接口契约正确（仅验证接口定义，无实现测试）

- [x] 6.2.1 验证 `KgSyncDomainService` 接口方法签名完整（sync*Nodes、upsert*、rebuild*Relations、markDeletedNodes、reconcile、validateUris、checkNeo4jHealth）
- [x] 6.2.2 验证 `KgRelationQueryDomainService` 接口方法签名完整（get*Relations）
- [x] 6.2.3 验证 Repository 接口方法签名完整（7 个 Repository 的 findAll/findBy/findAllActive/updateStatus 等方法）

### 6.3 Infrastructure 层 — Neo4jKgSyncService

> 测试目标：Mock Neo4j Driver，验证节点同步、关联同步、UPSERT、对账、URI 校验

- [x] 6.3.1 `Neo4jKgSyncServiceTest` — `syncTextbookNodes()` 方法（Mock Neo4j 返回 Textbook 节点 → 验证返回的 KgTextbook 列表正确）
- [x] 6.3.2 `syncChapterNodes()` / `syncSectionNodes()` / `syncKnowledgePointNodes()` 方法
- [x] 6.3.3 `syncTextbookChapterRelations()` / `syncChapterSectionRelations()` / `syncSectionKPRelations()` 方法（Mock Neo4j 返回关系数据 → 验证关联实体正确映射）
- [x] 6.3.4 `upsertTextbooks()` 方法 — 新增场景（MySQL 中不存在 → 执行 insert）、更新场景（MySQL 中已存在 → 执行 updateById）
- [x] 6.3.5 `upsertChapters()` / `upsertSections()` / `upsertKnowledgePoints()` 方法 — 仅新增（验证已存在的不重复插入）
- [x] 6.3.5.1 `upsertChapters()` 更新场景 — Neo4j 数据变化时 MySQL 对应更新（验证 label 等可变字段被更新）
- [x] 6.3.6 `rebuildTextbookChapterRelations()` 方法 — 新增关联、更新 orderIndex、软删除不存在关联、全量删除（空列表场景）
- [x] 6.3.7 `rebuildChapterSectionRelations()` / `rebuildSectionKPRelations()` 方法（同上）
- [x] 6.3.8 `markDeletedNodes()` 方法 — 4 类节点类型分别验证（MySQL 中有但 Neo4j 中无 → 标记 deleted）
- [x] 6.3.9 `validateUris()` 方法 — 正常 URI、空 URI、非法格式、重复 URI
- [x] 6.3.10 `validateAllUris()` 方法 — 混合场景（部分类型有非法 URI）
- [x] 6.3.11 `reconcile()` 方法 — 数量一致（matched）、数量不一致（mismatched + 差异详情）
- [x] 6.3.12 `checkNeo4jHealth()` 方法 — 健康场景、异常场景

### 6.4 Infrastructure 层 — Neo4jRelationQueryService

> 测试目标：缓存 → Neo4j → MySQL 三层降级链路

- [x] 6.4.1 `Neo4jRelationQueryServiceTest` — `getTextbookChapterRelations()` 方法 — 缓存命中场景
- [x] 6.4.2 缓存未命中 → 查询 Neo4j 成功场景
- [x] 6.4.3 Neo4j 异常 → 降级到 MySQL 场景
- [x] 6.4.4 `getChapterSectionRelations()` / `getSectionKPRelations()` 方法（同上）

### 6.5 Infrastructure 层 — Neo4jRelationCacheService

> 测试目标：Redis 缓存读写、TTL、序列化/反序列化

- [x] 6.5.1 `Neo4jRelationCacheServiceTest` — `setTextbookChapterRelations()` + `getTextbookChapterRelations()` 读写链路
- [x] 6.5.2 `setChapterSectionRelations()` + `getChapterSectionRelations()` 读写链路
- [x] 6.5.3 `setSectionKPRelations()` + `getSectionKPRelations()` 读写链路
- [x] 6.5.4 缓存未命中（key 不存在 → 返回 null）
- [x] 6.5.5 反序列化异常场景（损坏的 JSON → 返回 emptyList）
- [x] 6.5.6 `evictTextbook()` / `evictChapter()` / `evictSection()` 方法 — 验证正确的 key 被删除

### 6.6 Infrastructure 层 — RepositoryImpl
    
> 测试目标：验证 Mapper 委托正确、软删除过滤生效

- [x] 6.6.1 `KgTextbookRepositoryImplTest` — `save()` / `findByUri()` / `findAllActive()` / `findBySubject()` / `updateStatus()`
- [x] 6.6.2 `KgChapterRepositoryImplTest` — `save()` / `findByUri()` / `findByUris()` / `findByStatus()` / `updateStatus()`
- [x] 6.6.3 `KgSectionRepositoryImplTest` — `save()` / `findByUri()` / `findByUris()` / `findByStatus()` / `updateStatus()`
- [x] 6.6.4 `KgKnowledgePointRepositoryImplTest` — `save()` / `findByUri()` / `findByUris()` / `findByStatus()` / `updateStatus()`
- [x] 6.6.5 `KgTextbookChapterRepositoryImplTest` — `save()` / `selectByTextbookUri()` / `selectByCompositeKey()` / `selectAllActiveRelations()` / `softDeleteRelation()` / `batchDeleteAll()`
- [x] 6.6.6 `KgChapterSectionRepositoryImplTest` — 同上模式
- [x] 6.6.7 `KgSectionKPRepositoryImplTest` — 同上模式

### 6.7 Application 层 — KgSyncAppService

> 测试目标： 领域服务，验证同步流程编排、状态管理

- [x] 6.7.1 `KgSyncAppServiceTest` — `syncFull()` 全量同步流程（Mock KgSyncDomainService → 验证调用 sync*Nodes、upsert*、rebuild*Relations、markDeletedNodes、reconcile 的完整链路）
- [x] 6.7.2 `syncFull()` 定向同步 — 按 textbookUri 过滤（验证仅同步指定教材）
- [x] 6.7.3 `syncFull()` 同步锁 — 同步中再次调用 → 抛异常
- [x] 6.7.4 `syncFull()` 异常回滚 — Mock DomainService 抛异常 → 验证同步记录标记 failed
- [x] 6.7.5 `getSyncStatus()` 方法 — 空闲状态、运行中状态
- [x] 6.7.6 `getSyncRecords()` 方法 — 分页查询验证

### 6.8 Application 层 — KgNavigationAppService

> 测试目标： Repository，验证导航查询逻辑

- [x] 6.8.1 `KgNavigationAppServiceTest` — `getTextbooks()` 方法 — 全部查询、按 subject 过滤、按 phase 过滤
- [x] 6.8.2 `getChaptersByTextbook()` 方法 — 教材存在（返回章节树含小节和知识点计数）、教材不存在（抛异常）、空章节自动过滤
- [x] 6.8.3 `getKnowledgePointsBySection()` 方法 — 小节存在、小节不存在（抛异常）
- [x] 6.8.4 `getKnowledgePointDetail()` 方法 — 知识点存在（含 2 层父级）、知识点不存在、知识点已删除/已合并
- [x] 6.8.5 DTO 转换验证 — 验证 Entity → DTO 字段映射正确

### 6.9 Application 层 — KgKnowledgeSystemAppService

> 测试目标：Mock Repository，验证知识体系构建

- [x] 6.9.1 `KgKnowledgeSystemAppServiceTest` — `getGradeSystem()` 方法 — 按教材分组、按专题分组、年级不存在（返回空结构）
- [x] 6.9.2 `getGradeStats()` 方法 — 验证 totalKnowledgePoints、难度分布、认知层级分布计算正确
- [x] 6.9.3 空数据场景 — 验证返回结构完整（total=0, 空列表）

### 6.10 Application 层 — KgNeo4jService

> 测试目标：Mock 领域服务和缓存，验证 Neo4j 查询编排

- [x] 6.10.1 `KgNeo4jServiceTest` — `getNeo4jHealth()` 方法 — 健康（available=true）、异常（available=false）
- [x] 6.10.2 `batchGetConceptRelations()` 方法 — 正常返回、Neo4j 不可用（降级）、部分 URI 无关联

### 6.11 Interface 层 — KnowledgeGraphController

> 测试目标：使用 MockMvc 验证 HTTP 请求/响应

- [x] 6.11.1 `KnowledgeGraphControllerTest` — `POST /api/kg/sync/full` 成功场景（200 + SyncResult）
- [x] 6.11.2 `POST /api/kg/sync/full` 权限校验 — 非 ADMIN/TEACHER 角色 → AccessDenied
- [x] 6.11.3 `GET /api/kg/sync/status` 成功场景
- [x] 6.11.4 `GET /api/kg/sync/records` 分页查询
- [x] 6.11.5 `GET /api/kg/textbooks` 列表查询（含 subject/phase 过滤参数）
- [x] 6.11.6 `GET /api/kg/textbooks/{uri}/chapters` 章节树查询
- [x] 6.11.7 `GET /api/kg/sections/{uri}/points` 知识点列表
- [x] 6.11.8 `GET /api/kg/knowledge-points/{uri}` 知识点详情
- [x] 6.11.9 `GET /api/kg/system/grade/{grade}` 知识体系
- [x] 6.11.10 `GET /api/kg/system/stats/{grade}` 年级统计
- [x] 6.11.11 `GET /api/kg/neo4j/health` 健康检查
- [x] 6.11.12 `POST /api/kg/concepts/batch-relations` 批量关联
- [x] 6.11.13 统一响应包装验证 — 所有接口返回 ApiResponse 格式

### 6.12 DTO 序列化测试

> 测试目标：验证 Entity → DTO 转换正确，序列化到 JSON 格式符合 API 文档

- [x] 6.12.1 `KgTextbookDTO` — Entity → DTO 字段映射完整（uri/label/grade/phase/subject）
- [x] 6.12.2 `ChapterTreeNode` — 嵌套结构正确（章节含小节，小节含 knowledgePointCount）
- [x] 6.12.3 `KgKnowledgePointDetailDTO` — 含 2 层父级（sectionLabel/chapterLabel）
- [x] 6.12.4 `SyncResult` — 含 insertedCount/updatedCount/statusChangedCount/reconciliationStatus/details
- [x] 6.12.5 `KgGradeSystemDTO` — 分组结构正确（按教材/按专题）、知识点嵌套完整
- [x] 6.12.6 `StatsDTO` — 难度分布/认知层级分布/总数计算正确
- [x] 6.12.7 JSON 序列化验证 — MockMvc 验证 DTO 序列化为 JSON 后字段名符合 camelCase 规范

### 6.13 错误码验证测试

> 测试目标：验证异常场景下返回正确的错误码

- [x] 6.13.1 教材不存在 → code=70001
- [x] 6.13.2 章节不存在 → code=70002
- [x] 6.13.3 知识点不存在/已删除/已合并 → code=70003
- [x] 6.13.4 小节不存在 → code=70004
- [x] 6.13.5 Neo4j 查询失败 → code=70005
- [x] 6.13.6 同步中重复触发 → code=70006
- [x] 6.13.7 同步参数错误 → code=70007

### 6.14 双数据源路由测试

> 测试目标：验证 `@DS("kg")` 注解生效，知识图谱查询路由到 kg 库

- [x] 6.14.1 验证所有 edukg Mapper 的 `@DS("kg")` 注解存在
- [x] 6.14.2 验证业务 Mapper（User 等）不携带 `@DS("kg")` 注解，走默认 user 库
- [x] 6.14.3 验证 `@Transactional("kg")` 在 KgSyncAppService.syncFull() 上生效

## 7. 前端对接/

> 后端负责 API 设计和 DTO 定义，前端同学根据 API 文档开发页面。

- [ ] 7.1 提供 API 接口文档（api.md）给前端同学
- [ ] 7.2 确认 URI 编码规范与前端约定一致
- [ ] 7.3 联调知识点导航页面
- [ ] 7.4 联调年级知识体系页面

## 8. 联调与集成

- [ ] 8.1 执行全量同步，验证 MySQL 数据正确性（节点 + 关联表）
- [ ] 8.2 联调教材树浏览功能（与前端）
- [ ] 8.3 联调知识点详情展示（验证 2 层父级返回）
- [ ] 8.4 联调年级知识体系页面（与前端）
- [ ] 8.5 联调年级统计卡片（与前端）
- [ ] 8.6 端到端流程测试：选择学科→选择教材→浏览章节→查看知识点详情→切换年级知识体系