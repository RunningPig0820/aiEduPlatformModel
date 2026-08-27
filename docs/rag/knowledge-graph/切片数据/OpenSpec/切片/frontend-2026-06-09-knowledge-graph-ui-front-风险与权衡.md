# Risks / Trade-offs
> summary: 风险：图谱数据量大渲染性能、graph 接口未实现、React SPA 与现有项目集成、6757 节点 DOM 暴增，另有三个本期权衡取舍。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-风险与权衡.md
> 类别：架构设计

> 检索摘要：风险：图谱数据量大渲染性能、graph 接口未实现、React SPA 与现有项目集成、6757 节点 DOM 暴增，另有三个本期权衡取舍。

**[风险] 图谱数据量大导致渲染性能问题** → 后端限制返回节点数量（≤50），前端使用 `useNodesState/useEdgesState` 优化，提供简化视图降级

**[风险] 图谱关系 API 尚未实现** → 后端 `GET /api/auth/kg/knowledge-points/{uri}/graph` 未实现，需确认替代方案（补充 graph 接口或使用 `batchGetConceptRelations` 自建图谱）

**[风险] React SPA 与现有项目集成** → 当前 React SPA 为独立项目，需确认路由前缀、Nginx 转发、CORS 配置、构建输出方式

**[风险] 6757 节点展开后 DOM 暴增** → （可选）集成 `react-window` 虚拟滚动，切换教材根节点时清空缓存

**[权衡] 仅实现教材 Tab** → 学科 Tab 留到后续迭代，聚焦 MVP；同步 Tab 和统计面板本期实现

**[权衡] 不持久化选中状态** → 刷新页面后重置到初始状态，简化实现

**[权衡] 父组件 state 管理联动** → MVP 阶段避免引入 zustand 等额外依赖，扩展时再考虑

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§Risks / Trade-offs）
