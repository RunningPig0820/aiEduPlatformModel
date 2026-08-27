# 8. 组件间状态管理
> summary: 组件状态用父组件 state+props 传递，KnowledgeGraphPage 管理选中节点联动三栏，MVP 不引入 zustand 扩展时再考虑。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D8-组件间状态管理.md
> 类别：架构设计

> 检索摘要：组件状态用父组件 state+props 传递，KnowledgeGraphPage 管理选中节点联动三栏，MVP 不引入 zustand 扩展时再考虑。

**选择：父组件 state + props 传递（MVP 阶段）**

- 三栏联动通过父组件 `KnowledgeGraphPage` 管理选中节点状态
- MVP 阶段简单场景够用，避免引入额外依赖
- 未来若需从详情面板反向定位树节点等扩展功能，可引入 `zustand`

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§8. 组件间状态管理）
