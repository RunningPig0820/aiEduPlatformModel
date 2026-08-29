# 页面化与服务化：KnowledgeGraph 掌握度叠加与着色

> summary: KnowledgeGraph 掌握度叠加与着色
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-frontend-10-页面化与服务化-3.md
> 类别：操作流程

> 检索摘要：KnowledgeGraph 组件加可选 masteryMap prop（{[kpKey]: {coverage, status}}）叠加掌握度重着色，admin 图谱页不传保持零影响，拒绝复制学生版组件；掌握度离散四档着色（0 中性灰/25 红待巩固/50 黄练习中/75 绿已掌握），PENDING 低置信虚线边框，挂起项只落待确认清单不上图。

**KnowledgeGraph 加可选 `masteryMap` prop，admin 隔离**
给 `KnowledgeGraph.jsx` 加 `masteryMap` prop（`{ [kpKey]: { coverage, status } }`，覆盖度由题型派生而来）。传入时进入叠加模式，`textbook_kp`/`kp` 节点按派生覆盖度重着色；未传入时走既有类型配色。admin 图谱页不传该 prop，行为不变。替代方案：单独复制一个学生版图谱组件。拒绝——重复维护 ReactFlow/dagre 逻辑，且双入口共享组件符合「复用」目标。

**掌握度离散四档着色 + 疑似态**
后端确认 `mastery_level` 取值仅 `{0, 25, 50, 75}`，前端按 `==` 精确匹配（题型掌握度沿用此档位；知识点派生覆盖度映射到同一四档着色）：

| masteryLevel | 语义 | 视觉 |
|---|---|---|
| 0 | 未开始 | 中性灰 |
| 25 | 入门/薄弱 | 红 + badge「待巩固」 |
| 50 | 进阶/练习中 | 黄 + badge「练习中」 |
| 75 | 高级/掌握 | 绿 + badge「已掌握」 |
| 低置信 / status=PENDING | 待确认 | 虚线边框 + 「待确认」角标 |
| 无记录 | — | 中性灰 |

结构节点（教材/章节/小节）在叠加模式下保持类型色但降透明度作背景，让掌握度节点突出。

**关键约束**：PENDING 挂起项匹配不到任何图谱节点，无法上图——只能落在学习报告的「待确认清单」列表里（数据源 `pending-kps`）。图上虚线只覆盖「已解析但低置信」的节点。两者不混。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§5 KnowledgeGraph 加 masteryMap prop/§6 掌握度离散四档着色）
