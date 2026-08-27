# D12.3：API 设计 - 导航相关

> summary: 导航API扩展6级：学科/年级/教材列表、教材章节树、小节知识点、知识点详情及图谱关系，支持逐级浏览。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D12-3-api设计-导航相关.md
> 类别：架构设计

> 检索摘要：导航API扩展6级：学科/年级/教材列表、教材章节树、小节知识点、知识点详情及图谱关系，支持逐级浏览。

```
GET  /api/kg/subjects               - 获取学科列表（导航树根节点）
GET  /api/kg/subjects/{subject}/grades - 获取学科下的年级列表
GET  /api/kg/grades/{grade}/textbooks  - 获取年级下的教材列表
GET  /api/kg/textbooks              - 获取教材列表
GET  /api/kg/textbooks/{uri}        - 获取教材详情
GET  /api/kg/textbooks/{uri}/chapters - 获取教材章节树
GET  /api/kg/sections/{uri}/points    - 获取小节知识点
GET  /api/kg/knowledge-points/{uri}   - 获取知识点详情（含 2 层父级）
GET  /api/kg/knowledge-points/{uri}/graph - 获取知识点图谱关系
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D12.3：API 设计 - 导航相关）
