# D12.1：API 设计 - 同步相关

> summary: 同步API：POST /api/kg/sync/full触发全量同步（可带subject/phase/grade/textbookUri参数），查询同步状态与历史记录，当前不实现权限控制。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D12-1-api设计-同步相关.md
> 类别：架构设计

> 检索摘要：同步API：POST /api/kg/sync/full触发全量同步（可带subject/phase/grade/textbookUri参数），查询同步状态与历史记录，当前不实现权限控制。

```
POST /api/kg/sync/full              - 触发全量同步（可选参数：subject/phase/grade/textbookUri）
GET  /api/kg/sync/status            - 查询同步状态
GET  /api/kg/sync/records           - 同步历史记录
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D12.1：API 设计 - 同步相关）
