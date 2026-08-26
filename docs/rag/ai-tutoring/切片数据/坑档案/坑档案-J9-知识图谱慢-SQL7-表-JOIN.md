# 坑档案

> summary: 解决知识图谱慢SQL问题，改造下钻接口逻辑
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J9. 知识图谱慢 SQL（7 表 JOIN）
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J9. 知识图谱慢 SQL（7 表 JOIN）
**1. 问题现象**：教材树下钻接口慢到不可用（腾讯 MySQL 慢 SQL 报告）。**注意：本坑属于知识图谱模块，不属于答疑主链路**——答疑主链路不经过该接口。

**2. 触发流程**（旧链路）：`POST /api/kg/knowledge-points`（`KgKnowledgeOverviewAppService.page`）→ `KgKnowledgePointMapper.selectPageByStage/countByStage/*AndKeyword`。另有独立 kp-coverage 聚合链路 `GET /students/{id}/kp-coverage`（`KpCoverageAppService`）→ `selectPlacementByUris` kp 反向 7 JOIN 归属反查。

**3. 根因分析**：
- 7 表 JOIN（`t_kg_textbook` → textbook_chapter → chapter → chapter_section → section → section_kp → knowledge_point）分页投影：`GROUP BY kp.uri,...` **先于 `LIMIT`**、`COUNT(DISTINCT kp.uri)` **全扫**、`tb.stage` 无索引、每个 JOIN 都带 `is_deleted`。
- kp-coverage 聚合链路经 kp 反向 7 JOIN 归属反查，同样慢。

**4. 排查过程**：慢 SQL 报告定位到 7 表 JOIN 的 `selectPageByStage` 与 `countByStage`；再用 EXPLAIN 确认 GROUP BY 先于 LIMIT 导致全量分组、stage 无索引全扫。

**5. 解决方案 & 改动点**：
- **点击式下钻改造**：`学段→年级→课本→章节→小节→知识点` 5 层 GET（`KgOverviewTreeMapper.java:31-63`），每层单表或 2 表 JOIN（索引命中），点击才查、每层几~十几条不分页
- 删 `/kp-coverage` 链路（`KpCoverageAppService/DTO/ItemDTO`、`findPlacementByUris/selectPlacementByUris`、`KgKpPlacement`）
- 删未接线封闭域池约束组件群（`KpPoolAssociateService`、`KpConstrainedAssociationPort/KpConstrainedAssociator`）
修复 commit：`33e03bf`（下钻）、`0b285d2`（删 kp-coverage）、`c112e60`（下钻联调）。

**6. 面试口述要点**：讲"**大 JOIN + 分页 = 慢 SQL 典型组合**"——7 表 JOIN + GROUP BY 先于 LIMIT + COUNT DISTINCT 全扫。技术权衡：**点击式下钻**（每层单表/2 表 JOIN + 索引命中）替代一次查全量；删掉 kp-coverage 冗余链路。踩坑收获：**树形/层级数据用"点击才查"替代"一次全量投影"，是既简单又根治的做法**；同时要说明这坑在知识图谱模块，和答疑主链路无关。

---
