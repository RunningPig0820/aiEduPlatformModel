# 3. 树形导航实现
> summary: 树形导航用自定义递归组件+懒加载，daisyUI Tree 不支持动态懒加载，6757 节点不能一次性渲染，逐级请求子节点。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D3-树形导航实现.md
> 类别：架构设计

> 检索摘要：树形导航用自定义递归组件+懒加载，daisyUI Tree 不支持动态懒加载，6757 节点不能一次性渲染，逐级请求子节点。

**选择：自定义递归组件 + 懒加载**

原因：
- daisyUI Tree 组件不支持动态懒加载
- 6757 个节点不适合一次性渲染
- 自定义递归组件配合逐级 API 请求，按需加载子节点

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§3. 树形导航实现）
