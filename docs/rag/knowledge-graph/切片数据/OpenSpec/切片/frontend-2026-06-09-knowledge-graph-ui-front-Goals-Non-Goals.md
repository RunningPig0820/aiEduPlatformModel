# Goals / Non-Goals
> summary: 目标：教材树逐级懒加载、React Flow 展示知识点关联、同步管理与系统统计面板；不做搜索过滤、图谱编辑与数据导出。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-Goals-Non-Goals.md
> 类别：项目介绍

> 检索摘要：目标：教材树逐级懒加载、React Flow 展示知识点关联、同步管理与系统统计面板；不做搜索过滤、图谱编辑与数据导出。

**Goals:**
- 实现教材树形导航，支持逐级懒加载（教材 → 学科 → 年级 → 单元 → 课时 → 知识点）
- 通过 React Flow 可视化展示「教材知识点 → 知识点」的关联关系
- 支持点击树节点或图谱节点查看节点详情
- 实现知识图谱同步管理（手动触发同步、查看同步状态和历史记录）
- 实现系统概览统计（教材/章节/知识点数量统计、难度分布、Neo4j 健康检查）
- 页面风格简洁专业，符合后台管理系统规范

**Non-Goals:**
- 不实现树节点的搜索/过滤功能
- 不实现图谱的编辑/拖拽连线功能（仅展示）
- 不实现图谱数据的持久化或导出

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§Goals / Non-Goals）
