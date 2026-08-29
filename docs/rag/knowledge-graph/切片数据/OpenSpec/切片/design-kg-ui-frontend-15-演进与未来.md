# 演进与未来

> summary: 演进与未来
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-frontend-15-演进与未来.md
> 类别：未来演进

---

> 检索摘要：知识图谱前端后续怎么演进？学科 Tab 什么时候做？图谱关系接口未实现怎么办？未来状态管理和虚拟滚动等扩展方向是什么？

## 本期范围与后续迭代

- 教材 Tab 先行：本期仅实现教材 Tab，聚焦 MVP；学科 Tab 留到后续迭代。同步管理 Tab 与系统统计面板在本期实现。

## 图谱数据来源（待确认）

后端 GET /api/auth/kg/knowledge-points/{uri}/graph 接口尚未实现，图谱模块联调受阻。需与后端确认替代方案：后端补充 graph 接口 / 前端使用 batchGetConceptRelations + 已知知识点自建图谱 / 使用其他已有接口组合实现。确认后才能完成图谱模块联调。

## 未来扩展方向

- 状态管理：未来若需从详情面板反向定位树节点等扩展功能，可引入 zustand
- 大图谱渲染：（可选）集成 react-window 虚拟滚动，应对 6757 节点展开后 DOM 暴增；切换教材根节点时清空缓存
- 选中状态记忆：当前不持久化选中状态（刷新页面后重置到初始状态，简化实现），后续如需记忆用户浏览位置可扩展
