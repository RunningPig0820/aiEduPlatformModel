# D12.2：API 设计 - 维度配置

> summary: 维度下拉API：/api/kg/dimensions/subjects|grades|phases|textbooks从枚举与MySQL读取，供前端下拉选择器使用，无需登录。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D12-2-api设计-维度配置.md
> 类别：架构设计

> 检索摘要：维度下拉API：/api/kg/dimensions/subjects|grades|phases|textbooks从枚举与MySQL读取，供前端下拉选择器使用，无需登录。

```
GET  /api/kg/dimensions/subjects    - 获取学科列表（前端下拉用，枚举）
GET  /api/kg/dimensions/grades      - 获取年级列表（前端下拉用，MySQL）
GET  /api/kg/dimensions/phases      - 获取学段列表（前端下拉用，枚举）
GET  /api/kg/dimensions/textbooks   - 获取教材列表（前端下拉用，枚举）
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D12.2：API 设计 - 维度配置）
