# 方案选型与决策记录

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-frontend-16-方案选型与决策记录.md
> 类别：架构设计

---

> 检索摘要：知识图谱前端做了哪些关键选型？为什么选 React SPA 而不是 Alpine.js？为什么选 React Flow 而不是 D3/ECharts？树导航为什么自定义而不是 daisyUI？状态管理为什么不用 zustand？本期有哪些权衡取舍？

本文档（design-frontend-2026-06-09-knowledge-graph-ui-front）在设计阶段的关键选型与决策记录：

1. 前端架构：选 React SPA 独立部署（对比 Alpine.js）。原因：项目已有 React 18 + react-router-dom 基础；知识图谱页面交互复杂（树 + 图谱 + 详情面板联动），Alpine.js 不适合；React Flow 有成熟的 React 集成。

2. 关系图谱库：选 React Flow（对比 D3.js、ECharts）。原因：React 原生支持、API 简洁；力导向图布局内置支持；节点点击、缩放、拖拽等交互开箱即用；相比 D3.js 集成成本更低，相比 ECharts 更符合 React 范式。

3. 树形导航：选自定义递归组件 + 懒加载（对比 daisyUI Tree）。原因：daisyUI Tree 组件不支持动态懒加载；6757 个节点不适合一次性渲染；自定义递归组件配合逐级 API 请求按需加载子节点。

4. 数据加载策略：选逐级懒加载 + 状态缓存。树节点展开时请求子节点列表，已展开节点缓存子节点数据；切换教材根节点时清空缓存避免陈旧数据；详情数据在节点选中时实时请求、不缓存（保证数据一致性）。

5. 同步管理展示：选页面头部按钮触发 + 侧边弹窗/独立路由。同步状态接口页面加载时自动请求；手动同步按钮触发全量同步接口（支持按学科/学段/年级/教材筛选参数）；同步记录以列表/表格展示；MVP 阶段用页面内 Modal 或侧边面板展示，避免新增路由。

6. 系统统计展示：选页面顶部概览栏。页面头部下方横条（统计卡片）展示教材/章节/小节/知识点数量、难度分布与 Neo4j 健康状态。

7. 组件间状态管理：选父组件 state + props 传递（对比 zustand）。三栏联动通过父组件 KnowledgeGraphPage 管理选中节点状态；MVP 阶段简单场景够用，避免引入额外依赖；未来若需从详情面板反向定位树节点等扩展功能，可引入 zustand。

8. 图谱性能优化：选 useNodesState / useEdgesState + 后端初始坐标。内置状态管理减少重渲染；节点布局优先让后端返回力导向初始坐标，前端直接展示；节点 > 50 时提供「简化视图」开关，仅显示 Top 10 关联节点。

9. 图谱数据来源（待决）：原计划 GET /api/auth/kg/knowledge-points/{uri}/graph，后端未实现；替代方案待确认（后端补充 graph 接口 / 前端用 batchGetConceptRelations + 已知知识点自建 / 其他接口组合）。

10. 错误处理方案：树展开与图谱加载失败提供「重试」按钮；图谱渲染异常由全局 Error Boundary 捕获；未登录或无权限时 API 层统一拦截跳转登录。

本期权衡取舍：
- 仅实现教材 Tab，学科 Tab 留到后续迭代（聚焦 MVP）
- 不持久化选中状态，刷新页面后重置到初始状态（简化实现）
- 父组件 state 管理联动，避免引入 zustand 等额外依赖
