# 7. 系统统计实现
> summary: 系统统计用页面顶部概览栏，stats/{grade}、grade/{grade}、neo4j/health 三接口，展示教材章节知识点数量与难度分布。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D7-系统统计实现.md
> 类别：业务视角

> 检索摘要：系统统计用页面顶部概览栏，stats/{grade}、grade/{grade}、neo4j/health 三接口，展示教材章节知识点数量与难度分布。

**选择：页面顶部概览栏**

- 统计数据通过 `GET /api/auth/kg/system/stats/{grade}` 获取（教材数、章节数、小节数、知识点总数、难度分布）
- 学科体系通过 `GET /api/auth/kg/system/grade/{grade}` 获取
- Neo4j 健康通过 `GET /api/auth/kg/neo4j/health` 检查
- 展示形式：页面头部下方横条（统计卡片）

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§7. 系统统计实现）
