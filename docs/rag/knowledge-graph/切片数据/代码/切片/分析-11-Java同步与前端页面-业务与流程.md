# 分析-11-Java同步与前端页面-业务与流程

> summary: Java同步与前端页面业务与流程
> 来源: 切片 ｜ 锚点: 业务与流程
> 节: 分析-11-Java同步与前端页面
> COS路径: rag-slices/knowledge-graph/代码/分析-11-Java同步与前端页面-业务与流程.md
> 类别：业务流程
> target: 面试项目问答

---

## 业务描述与业务场景

图谱要变成教研/学生能点的页面——后端把教材结构从 Neo4j 同步到 MySQL 供前端只读，前端三栏页面逐级浏览教材树、看知识点关联图和详情、手动触发同步。这是图谱从"数据管道"走向"可视消费"的最后一公里。

典型场景：
1. 教研在知识图谱页点开「一年级上册」→ 展开教材→章节→小节→知识点，逐级懒加载不卡顿。
2. 点某个知识点，右栏显示详情（含 2 层父级：小节+章节），中间用关系图展示它关联到图谱概念。
3. 管理员在页面上点"同步"，把 Neo4j 最新教材结构拉进 MySQL，同步完自动对账，不一致在记录里标红。

## 职责

**做什么**：Neo4j 教材结构 → MySQL ai_edu_kg（8 张表）→ REST API → 前端 React SPA 展示与同步管理。
**不做什么**：不同步图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等直查 Neo4j）、不做图谱编辑/拖拽连线、不做前端搜索过滤、不做数据导出、不做实时 CDC（手动按需同步）。
**分工**：Java 后端负责双数据源 + 同步/导航/API，前端 React SPA 负责三栏/懒加载/React Flow。**注意：本主题 Java/前端两端均不在本仓，以下事实全部来自 OpenSpec design 文档（权威 0.7 设计素材），非代码真值**。

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

**文字复述链路**：管理员点"同步"触发全量同步 → 先加同步锁（同一时间只跑一个任务）→ 连接 Neo4j 查教材/章节/小节/知识点节点及层级关系 → URI 校验（非空/前缀合法/同批不重复，异常跳过）→ 单大事务内 UPSERT 节点主表、关联表先清空再重建（含排序）→ MySQL 有而 Neo4j 无的节点置为 deleted（知识点另记 merged_to_uri）→ 对账校验节点数/关联数写入同步记录 → 写记录、释放锁、返回统计；失败整体回滚可重跑（UPSERT 幂等）。数据落到 MySQL 后，前端只读 MySQL 逐级懒加载（教材→章节→小节→知识点，展开才请求子节点、切教材根清缓存）；图谱关系直查 Neo4j 并走 Redis 缓存（TTL 300s），Neo4j 不可用时返回空关联 + 前端隐藏图谱模块降级；最终 React SPA 三栏展示（左树/中 React Flow 关系图/右详情 2 层父级）+ 顶部统计面板 + 同步管理弹窗。

> 证据：详见 `3.代码/分析-11-Java同步与前端页面.md`（§业务描述与业务场景 / §职责 / §高层业务调用链）｜ `4.完善文档/03-架构与三端分工.md` + `09-业务闭环与图谱价值落地.md`
