# 分析-11 Java同步与前端页面（代码真相）

> 证据说明: 本文档基于 OpenSpec design 文档撰写,Java/前端代码不在本仓,非代码真值
> summary: 解答「图谱怎么页面化给学生/教研看」——本文档基于 OpenSpec design 文档（design-backend-2026-06-03-knowledge-graph-{datasource,ui}.md、design-frontend-2026-06-09-knowledge-graph-ui-front.md）撰写，Java/前端代码不在本仓（aiEduPlatform/、aiEduPlatformFront/ 不存在），非代码真值（权威度 0.8）。核心方案 B：Neo4j→MySQL 手动按需同步（非 CDC）、前端只读 MySQL，不做图谱编辑/搜索/导出。同步流：管理员点「同步」→ POST /api/kg/sync/full → 同步锁（MySQL 行锁/Redis 锁）→ 查 Neo4j 教材节点+层级（CONTAINS/IN_UNIT 含 order_index）→ URI 校验（非空、前缀 http://edukg.org/knowledge/、不重复，D6）→ 单大事务 UPSERT 节点主表 + 关联表先清空再 INSERT → MySQL 有而 Neo4j 无则 status='deleted'（知识点另设 merged_to_uri）→ 对账写 t_kg_sync_record.reconciliation_status → 失败回滚可重跑（幂等）。数据模型 8 张表（design-backend-ui D1）：4 节点主表 t_kg_textbook/chapter/section/knowledge_point 均以 uri VARCHAR(255) 主键（跨库唯一锚点）+ 3 层级关联表（联合主键含 order_index）+ 1 同步记录表。双数据源 @DS("kg") 路由 ai_edu_kg（persistence.edukg.mapper.*），primary:user、strict:true、@Transactional("kg")，Flyway 全禁用表手动创建（design-backend-datasource 96-114）。状态机 active/deleted/merged：导航/知识体系过滤 WHERE status='active'，deleted=Neo4j 已删（进度查询例外），merged 经 merged_to_uri 迁移（D2）；枚举 KgSubjectEnum 六科/KgPhaseEnum primary/middle/high（D10）。前端 React SPA 三栏（左教材树+中 React Flow 关系图+右详情），逐级懒加载自定义递归树，6757 节点不一次性渲染；6 级导航 GET /api/kg/subjects→{subject}/grades→{grade}/textbooks→textbooks/{uri}/chapters→sections/{uri}/points→knowledge-points/{uri}；知识点详情含 2 层父级（小节+章节，D9）；图谱关系直查 Neo4j（concepts/{uri}/relations、batch-relations 防 N+1），Redis kg:neo4j:{uri}:{query_type} TTL 300s 降级，Neo4j 不可用返回空关联+neo4jAvailable:false 隐藏图谱模块；同步管理弹窗（status/records）+统计面板（system/stats/{grade}、neo4j/health）；React Flow useNodesState/useEdgesState，节点>50 简化视图仅 Top 10。设计要点：方案 B 避免业务事实污染权威图谱（D17 权威图谱零写入）、URI 永不修改改动走合并、软删除可回溯、降级优先、手动按需同步而非 CDC。已知坑：knowledge-points/{uri}/graph 后端未实现（design 自相矛盾）；前后端前缀不一致（/api/kg/** vs /api/auth/kg/** 易 404）；年级下拉须先全量同步才有数据；关联表 DELETE+INSERT 依赖单事务防「空目录」；deleted 清理需确认无下游引用；<1 万节点 URI 主键可行。对账：8 表/双数据源/前端三栏文档层面一致，graph 契约断裂、前缀不一致、Flyway 设计降级均。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-source/knowledge-graph/代码/分析-11-Java同步与前端页面.md
> 类别：架构设计

## 业务描述与业务场景

**业务描述**：Neo4j 图谱要变成教研/学生能点的页面——后端把教材结构同步到 MySQL 供前端只读，前端三栏页面逐级浏览教材树、看知识点关联图和详情、手动触发同步。这是图谱从"数据管道"走向"可视消费"的最后一公里。

**业务场景**：
- 教研在知识图谱页点开「一年级上册」→ 展开教材→章节→小节→知识点，逐级懒加载，不卡顿
- 点某个知识点，右栏显示详情（含 2 层父级：小节+章节），中间用关系图展示它关联到图谱概念
- 管理员在页面上点"同步"，把 Neo4j 最新教材结构拉进 MySQL，同步完自动对账，不一致在记录里标红

## 职责

**职责**：Neo4j 教材结构 → MySQL ai_edu_kg（8 张表）→ REST API → 前端 React SPA 展示与同步管理。
**不做什么**：不同步图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等直查 Neo4j）、不做图谱编辑/拖拽连线、不做前端搜索过滤、不做数据导出、不做实时 CDC（手动按需同步）。
**分工要点**：Java 后端（datasource 双数据源 + ui 同步/导航/API）+ 前端 React SPA（三栏/懒加载/React Flow）。本主题 Java/前端两端均**不在本仓**（`aiEduPlatform/`、`aiEduPlatformFront/` 不存在），以下事实全部来自 OpenSpec design 文档（权威 0.7 设计素材），非代码真值。

## 高层业务调用链（Neo4j 图谱→MySQL→前端页面）

```
Neo4j（教材结构 Textb/Chapter/Section/TextbookKP + 图谱关系）
  │
  ├─ 管理员点"同步" → POST /api/kg/sync/full（可选 subject/phase/grade/textbookUri）
  │    ① 获取同步锁（MySQL 行锁或 Redis 分布式锁）
  │    ② 连接 Neo4j 查节点（Textbook→Chapter→Section→TextbookKP）+ 层级关系（CONTAINS/IN_UNIT 含 order_index）
  │    ③ URI 校验（非空/前缀 http://edukg.org/knowledge//同批不重复）→ 异常记录日志并跳过
  │    ④ 单大事务内 UPSERT 节点主表（INSERT ... ON DUPLICATE KEY UPDATE）
  │       + 关联表先清空本层再重新 INSERT（含 order_index）
  │    ⑤ MySQL 有、Neo4j 无 → status='deleted'（知识点另设 merged_to_uri）
  │    ⑥ 对账校验：MySQL vs Neo4j 节点数/关联数 → t_kg_sync_record.reconciliation_status
  │    ⑦ 写同步记录、释放锁、返回统计
  │    失败 → 事务回滚，可重新触发（UPSERT 幂等）
  │
  ▼
MySQL ai_edu_kg（8 张表：4 节点主表 + 3 层级关联表 + 1 同步记录表）
  │
  ▼ 前端只读 MySQL
GET /api/kg/subjects → /grades → /textbooks → /textbooks/{uri}/chapters → /sections/{uri}/points → /knowledge-points/{uri}
  │  逐级懒加载（树展开才请求子节点，切教材根清缓存）
  ▼
图谱关系 → GET /api/kg/concepts/{uri}/relations（直查 Neo4j，Redis key kg:neo4j:{uri}:{query_type} TTL 300s）
  │  Neo4j 不可用 → 返回空关联 + neo4jAvailable:false，前端隐藏图谱模块（降级）
  ▼
React SPA 三栏（左树 / 中 React Flow 关系图 / 右详情 2 层父级）+ 顶部统计面板 + 同步管理弹窗
```

## 代码事实

> 本节约束：以下全部为 design 文档描述（`design-backend-*-knowledge-graph-{datasource,ui}.md` / `design-frontend-*-knowledge-graph-ui-front.md`），**代码实现不在本仓，未真读**。

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

### API 设计（design-backend-ui D12.1-D12.5）
| 接口 | 作用 |
|---|---|
| `POST /api/kg/sync/full` | 触发全量同步（可选 subject/phase/grade/textbookUri） |
| `GET /api/kg/sync/status` / `GET /api/kg/sync/records` | 同步状态/历史 |
| `GET /api/kg/dimensions/subjects|grades|phases|textbooks` | 下拉选项（枚举+MySQL 混合） |
| `GET /api/kg/subjects` / `{subject}/grades` / `{grade}/textbooks` | 6 级导航前三层 |
| `GET /api/kg/textbooks/{uri}/chapters` / `sections/{uri}/points` | 章节树/小节知识点 |
| `GET /api/kg/knowledge-points/{uri}` | 知识点详情（含 2 层父级） |
| `GET /api/kg/knowledge-points/{uri}/graph` / `{uri}/path` | 图谱关系/到概念完整路径（Neo4j） |
| `GET /api/kg/system/grade/{grade}` / `system/stats/{grade}` | 年级知识体系/统计 |
| `GET /api/kg/concepts/{uri}/relations` / `concepts/batch-relations` | 概念关联图（Neo4j+Redis 缓存） |
| `GET /api/kg/neo4j/health` | Neo4j 健康检查 |

### 前端页面（design-frontend）
1. **三栏布局**：左教材树 + 中 React Flow 关系图 + 右详情，父组件 `KnowledgeGraphPage` 用 state+props 管理选中联动（不引入 zustand）（design-frontend:8,116-124）。
2. **逐级懒加载**：自定义递归树组件（daisyUI Tree 不支持动态懒加载），树展开请求子节点并缓存，切换教材根清空缓存；6757 节点不一次性渲染（design-frontend:61-82）。
3. **React Flow**：`useNodesState/useEdgesState` 管理，优先后端返回力导向初始坐标；节点>50 提供"简化视图"仅显示 Top 10；无数据给空态文案（design-frontend:50-59,126-139）。
4. **同步管理页**：页面头部按钮触发 `POST /api/kg/sync/full`（可按学科/学段/年级/教材筛选），`status/records` 展示，MVP 用 Modal/侧边面板（design-frontend:94-103）。
5. **统计面板**：页面顶部概览卡片，`system/stats/{grade}`（教材/章节/小节/知识点数+难度分布）、`neo4j/health`（design-frontend:105-115）。
6. **错误处理**：树展开/图谱加载失败给重试按钮；渲染异常全局 Error Boundary 捕获；未登录统一拦截跳登录（design-frontend:140-146）。

## 隐性坑与注意事项
- **graph 接口未实现**：前端原计划 `GET /api/kg/knowledge-points/{uri}/graph`，但 design 标注"后端当前未实现此接口"，替代方案待确认（补接口 / batchGetConceptRelations 自建 / 其他接口组合）（design-frontend:83-92,154）。
- **路径前缀不一致**：后端 design 写 `/api/kg/**`，前端 design 全部用 `/api/auth/kg/**` 前缀——两者口径未对齐，联调易 404。
- **首次下拉为空**：年级下拉来自 `t_kg_textbook DISTINCT grade`，必须先做一次全量同步才有数据（design-backend-ui D10）。
- **关联表重建有窗口**：同步先 DELETE 再 INSERT 关联表，依赖单事务保证前端看不到中间态；若事务失效会重现"空目录"联调问题（design-backend-ui D2）。
- **deleted 数据膨胀**：status='deleted' 定期物理清理需确认无下游引用（design-backend-ui Risks）。
- **URI 主键性能**：<1 万节点 VARCHAR(255) 主键可行，暴涨才考虑整型代理键（design-backend-ui Risks）。

## 设计要点
- **方案 B：Neo4j→MySQL 同步、前端读 MySQL**（语雀 D13）：Java 无 Neo4j 集成、前端独立 SPA，MySQL 只存节点属性+层级关系，图谱关系直查 Neo4j 而非同步——避免无限业务事实污染权威图谱（配合 D17 权威图谱零写入）。
- **URI 主键**（语雀 D15）：非自增 ID，跨 Neo4j/MySQL 唯一锚点，同步按 URI UPSERT，URI 永不修改、改动走合并流程。
- **状态机软删除**：active/deleted/merged 让"删除"可回溯、进度历史不丢（进度查询例外不过滤 deleted）。
- **降级优先**：Neo4j 关系查询 Redis TTL 300s + 空关联降级，核心导航不依赖图谱服务可用性。
- **手动按需同步而非 CDC**：demo 阶段避免实时监听复杂度，失败可重跑（UPSERT 幂等 + 单事务原子）。

## 对账要点
| 对账分类 | 项 | 语雀/design 口径 | 现状 | 结论 |
|---|---|---|---|---|
| 方案vs实现 | Java/前端代码 | 语雀 D13/D14 描述页面化落地 | **代码不在本仓**（aiEduPlatform/aiEduPlatformFront 不存在），仅有 design 文档 | 无法核实（非代码真值） |
| 接口契约 | 图谱 graph 接口 | design-backend-ui 列出 `knowledge-points/{uri}/graph` | design-frontend 标注该接口后端未实现 | 契约断裂（design 内自相矛盾） |
| 接口契约 | API 前缀 | 后端 `/api/kg/**` | 前端 `/api/auth/kg/**` | 口径不一致 |
| 方案vs实现 | 8 张表 | D13 4 节点主表+3 层级关联+1 同步记录 | design-backend-ui D1 表结构与状态机一致 | 文档层面一致 |
| 方案vs实现 | 双数据源 | D14 @DS("kg") ai_edu_kg | design-backend-datasource 全链路设计 | 文档层面一致 |
| 方案vs实现 | 前端三栏/懒加载/React Flow | design-frontend 目标 | design 一致 | 文档层面一致 |
| 注释vs运行行为 | Flyway | 双库分组管理 | 当前全禁用，表手动创建 | 设计降级 |

## 已读代码清单
- **Python 管道（edukg）**：无（本主题不涉 Python 管道）。
- **Python 桥（ai-service）**：无实际读取（本主题为 Java/前端；Python 桥端点未纳入本次范围）。
- **Java**：`aiEduPlatform/` 不在本仓 → 基于 `docs/rag/knowledge-graph/2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（@DS/事务/yml/Flyway）与 `design-backend-2026-06-03-knowledge-graph-ui.md`（8 表/状态机/同步流/API/DTO）撰写。
- **前端**：`aiEduPlatformFront/` 不在本仓 → 基于 `docs/rag/knowledge-graph/2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（三栏/懒加载/React Flow/同步页/统计面板）撰写。
> 本主题跨 2 端（Java + 前端），但 Java/前端代码均不在本仓，**仅基于 design 文档，非代码真值**。
