# 三端架构与分工

> summary: 三端架构与分工
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-frontend-11-三端架构与分工.md
> 类别：架构设计

---

> 检索摘要：知识图谱三端怎么分工？前端 React SPA 在整体架构里是什么角色？前端消费后端哪些 API？独立部署的前端怎么与现有项目集成？

## 前端定位

前端为 React SPA，独立项目、独立部署，只读展示知识图谱。前端不直接操作图谱数据，仅通过后端 API 获取数据；图谱编辑/拖拽连线、数据持久化或导出均不在本期范围（Non-Goals）。

三端分工（本变更口径）：后端（Java）完成 Neo4j → MySQL 同步并提供知识图谱 API；前端 React SPA 只读调用这些 API 完成页面展示；Neo4j 作为图谱数据源在后端侧，前端不直连。

## 前端消费的后端 API

- GET /api/auth/kg/knowledge-points/{uri}/graph —— 图谱关系数据（原计划，当前后端未实现）
- GET /api/auth/kg/sync/status —— 同步状态
- POST /api/auth/kg/sync/full —— 手动触发全量同步（支持按学科/学段/年级/教材筛选参数）
- GET /api/auth/kg/sync/records —— 同步历史记录
- GET /api/auth/kg/system/stats/{grade} —— 系统统计（教材/章节/小节/知识点数量、难度分布）
- GET /api/auth/kg/system/grade/{grade} —— 学科体系
- GET /api/auth/kg/neo4j/health —— Neo4j 健康检查

## 联调状态

前端正与后端联调对接上述接口，本变更同步修复前后端字段不一致问题。

## 集成风险

当前 React SPA 为独立项目，与现有项目集成需确认：路由前缀、Nginx 转发、CORS 配置、构建输出方式。
