# 学生端图谱页

> summary: 复用 KnowledgeGraph.jsx 新增学生端图谱页，mastery.kpKey==node.id 按档位着色，疑似节点从 obs PENDING 列表渲染虚线+角标。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D7-学生端图谱页.md
> 类别：操作流程

> 检索摘要：复用 KnowledgeGraph.jsx 新增学生端图谱页，mastery.kpKey==node.id 按档位着色，疑似节点从 obs PENDING 列表渲染虚线+角标。

- 复用 `KnowledgeGraph.jsx` 组件，新增学生路由 + 页面（当前学生端无图谱页，仅 admin 有）。
- 取图：现有 `POST /api/auth/kg/knowledge-points/graph`（节点带 uri）。取掌握度：增强后 `GET /api/students/{id}/mastery`。
- 匹配：`mastery.kpKey == node.id` → 按档位着色。疑似节点从 obs PENDING 列表渲染虚线 + 角标。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D7 学生端图谱页）
