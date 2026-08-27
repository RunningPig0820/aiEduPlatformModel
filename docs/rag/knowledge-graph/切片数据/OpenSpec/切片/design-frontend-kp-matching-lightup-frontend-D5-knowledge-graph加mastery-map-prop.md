# KnowledgeGraph 加 masteryMap prop

> summary: KnowledgeGraph 组件加可选 masteryMap prop 叠加掌握度重着色，admin 图谱页不传保持零影响，拒绝复制学生版组件。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-D5-knowledge-graph加mastery-map-prop.md
> 类别：架构设计

---

### 5. KnowledgeGraph 加可选 `masteryMap` prop，admin 隔离

> 检索摘要：KnowledgeGraph 组件加可选 masteryMap prop 叠加掌握度重着色，admin 图谱页不传保持零影响，拒绝复制学生版组件。

给 `KnowledgeGraph.jsx` 加 `masteryMap` prop（`{ [kpKey]: { coverage, status } }`，覆盖度由题型派生而来）。传入时进入叠加模式，`textbook_kp`/`kp` 节点按派生覆盖度重着色；未传入时走既有类型配色。admin 图谱页不传该 prop，行为不变。

替代方案：单独复制一个学生版图谱组件。**拒绝**——重复维护 ReactFlow/dagre 逻辑，且双入口共享组件符合「复用」目标。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§5. KnowledgeGraph 加可选 masteryMap prop，admin 隔离）
