# Context：后端就绪与前端待补功能
> summary: 后端已完成知识图谱数据建模（Neo4j→MySQL 同步）并提供教材导航/知识点详情/同步管理 API，前端 React SPA 三栏布局正在联调，本变更补齐同步管理页与系统统计面板。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-Context.md
> 类别：架构设计

> 检索摘要：后端已完成知识图谱数据建模（Neo4j→MySQL 同步）并提供教材导航/知识点详情/同步管理 API，前端 React SPA 三栏布局正在联调，本变更补齐同步管理页与系统统计面板。

后端已完成知识图谱数据建模（Neo4j → MySQL 同步），提供教材导航 API、知识点详情 API、同步管理 API（sync/status/records）和系统统计 API。前端已完成 React SPA 基础架构和知识图谱三栏布局（树 + 图谱 + 详情），正在联调对接后端接口。

本变更在现有 React SPA 中补充缺失功能：同步管理页面、系统统计面板、以及联调修复前后端字段不一致问题。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§Context：后端就绪与前端待补功能）
