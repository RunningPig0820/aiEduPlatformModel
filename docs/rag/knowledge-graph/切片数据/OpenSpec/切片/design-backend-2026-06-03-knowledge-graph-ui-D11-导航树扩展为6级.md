# D11：导航树扩展为 6 级

> summary: 决策：导航树从4级扩为6级（学科→年级→教材→章节→小节→知识点），新增subjects/grades/textbooks接口，数据均来自t_kg_textbook聚合查询。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D11-导航树扩展为6级.md
> 类别：业务流程

> 检索摘要：决策：导航树从4级扩为6级（学科→年级→教材→章节→小节→知识点），新增subjects/grades/textbooks接口，数据均来自t_kg_textbook聚合查询。

**决策**: 导航树从原有的 4 级（教材→章节→小节→知识点）扩展为 6 级（学科→年级→教材→章节→小节→知识点）。

**新增接口**:
- `GET /api/kg/subjects` — 根节点：学科列表（从 t_kg_textbook DISTINCT subject 查询）
- `GET /api/kg/subjects/{subject}/grades` — 学科下的年级列表（从 t_kg_textbook WHERE subject=? DISTINCT grade 查询）
- `GET /api/kg/grades/{grade}/textbooks` — 年级下的教材列表（从 t_kg_textbook WHERE grade=? 查询）

**数据来源**: 所有导航树层级数据均来自 `t_kg_textbook` 表聚合查询，不依赖额外配置表。

**前端导航流程**:
```
1. 用户进入知识图谱页面
2. GET /subjects -> 显示学科列表（数学、语文、英语...）
3. 用户点击"数学" -> GET /subjects/数学/grades -> 显示年级列表
4. 用户点击"一年级" -> GET /grades/一年级/textbooks -> 显示教材列表
5. 用户点击教材 -> GET /textbooks/{uri}/chapters -> 展开章节
6. 逐级展开 -> 小节 -> 知识点
7. 用户点击知识点 -> GET /knowledge-points/{uri}/graph -> 展示图谱关系
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D11：导航树扩展为 6 级）
