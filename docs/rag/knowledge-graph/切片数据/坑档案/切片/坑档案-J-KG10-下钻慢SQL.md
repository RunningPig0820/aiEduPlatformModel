# 坑档案-J-KG10-下钻慢SQL

> summary: 下钻慢SQL
> 来源: 坑档案 ｜ 锚点: J-KG10 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG10-下钻慢SQL.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：知识图谱总览接口（POST /api/kg/knowledge-points）在腾讯 MySQL 慢 SQL 报告中被打标——7 表 JOIN 分页，请求响应慢、DB 压力大。

**2. 触发流程**：前端打开知识图谱总览 → 一次拉全学段→年级→课本→章节→小节→知识点全量 → `selectPageByStage/countByStage/*AndKeyword` 做 7 表 JOIN（textbook→chapter→section→kp）+ 分页。

**3. 根因分析**：`33e03bf` 提交信息：慢 SQL 根因 = **7 表 JOIN + GROUP BY 先于 LIMIT + COUNT DISTINCT 全扫 + tb.stage 无索引 + 每 JOIN 带 is_deleted**——一次性把整棵教材树拼出来分页，等价于全表扫描。

**4. 排查过程**：腾讯云慢 SQL 报告定位到该接口；分析执行计划确认 7 表 JOIN 全扫 + 无索引条件。

**5. 解决方案 & 改动点**：**点击式下钻改造**：新增 `KgOverviewTreeRepository`（`ai-edu-backend/.../domain/edukg/repository/KgOverviewTreeRepository.java`，接口注释"每次单层查询，最多 2 表 JOIN，索引命中"）——学段→年级→课本→章节→小节→知识点逐层查询，每层单表/2 表 JOIN、数据量小无需分页；删除 7 JOIN 分页端点（`selectPageByStage/countByStage/*AndKeyword` + POST /knowledge-points）；`0b285d2` 再删 /kp-coverage 独立聚合链路（`KpCoverageAppService` 整删）。前端 `901ff5e`/`327a901` 同步改菜单式下钻 5 层 GET。提交：`33e03bf [知识点]-[knowledge-graph-slow-sql]`、`0b285d2`；前端 `901ff5e [学生端]-[知识点]`。

**6. 面试口述要点**：树形/层级数据**一次拼全量**是大忌——每层数据量小、用户是逐步下钻的，改成"点哪层查哪层"就把 7 JOIN 全扫拆成 N 个索引单查。慢 SQL 优化先看"是不是查了用户不需要的量"（数据量/分页位置），再看索引。这里 `COUNT DISTINCT 全扫 + GROUP BY 先于 LIMIT` 是分页场景典型反模式。
