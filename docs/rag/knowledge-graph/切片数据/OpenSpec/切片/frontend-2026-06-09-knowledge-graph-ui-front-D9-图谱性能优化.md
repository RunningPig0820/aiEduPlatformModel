# 9. 图谱性能优化
> summary: 图谱性能优化用 useNodesState/useEdgesState，优先后端返回力导向初始坐标，节点>50 提供简化视图只显示 Top10，无数据给空态文案。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D9-图谱性能优化.md
> 类别：开发难点

> 检索摘要：图谱性能优化用 useNodesState/useEdgesState，优先后端返回力导向初始坐标，节点>50 提供简化视图只显示 Top10，无数据给空态文案。

**React Flow 状态管理**

- 使用 `useNodesState` / `useEdgesState` 内置状态管理，减少重渲染
- 节点布局：优先让后端返回初始坐标（力导向迭代结果），前端直接展示
- 降级方案：节点 > 50 时提供"简化视图"开关，仅显示 Top 10 关联节点

**图谱空状态**

- 无关联图谱时显示"当前知识点暂无关联图谱数据"引导文案

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§9. 图谱性能优化）
