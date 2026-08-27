# 1. 前端架构
> summary: 前端架构选 React SPA 独立部署，因已有 React 18 + react-router-dom 基础且 React Flow 集成成熟，Alpine.js 不适合复杂联动。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D1-前端架构.md
> 类别：架构设计

> 检索摘要：前端架构选 React SPA 独立部署，因已有 React 18 + react-router-dom 基础且 React Flow 集成成熟，Alpine.js 不适合复杂联动。

**选择：在 React SPA 项目中实现，独立部署**

原因：
- 项目已有 React 18 + react-router-dom 基础
- 知识图谱页面交互复杂（树 + 图谱 + 详情面板联动），Alpine.js 不适合
- React Flow 有成熟的 React 集成

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§1. 前端架构）
