# 6. 同步管理实现
> summary: 同步管理用页面头部按钮触发+侧边弹窗/独立路由，status/full/records 三接口，支持按学科学段年级教材筛选，MVP 用 Modal。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D6-同步管理实现.md
> 类别：业务流程

> 检索摘要：同步管理用页面头部按钮触发+侧边弹窗/独立路由，status/full/records 三接口，支持按学科学段年级教材筛选，MVP 用 Modal。

**选择：页面头部按钮触发 + 侧边弹窗/独立路由展示**

- 同步状态通过 `GET /api/auth/kg/sync/status` 获取，页面加载时自动请求
- 手动同步通过按钮触发 `POST /api/auth/kg/sync/full`，支持按学科/学段/年级/教材筛选参数
- 同步记录通过 `GET /api/auth/kg/sync/records` 获取，以列表/表格形式展示
- MVP 阶段使用页面内 Modal 或侧边面板展示同步信息，避免新增路由

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§6. 同步管理实现）
