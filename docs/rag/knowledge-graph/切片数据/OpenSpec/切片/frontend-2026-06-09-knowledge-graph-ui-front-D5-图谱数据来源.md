# 5. 图谱数据来源
> summary: 图谱数据来源待确认：后端 graph 接口未实现，替代方案为后端补接口、前端用 batchGetConceptRelations 自建或用其他接口组合。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/frontend-2026-06-09-knowledge-graph-ui-front-D5-图谱数据来源.md
> 类别：数据关联

> 检索摘要：图谱数据来源待确认：后端 graph 接口未实现，替代方案为后端补接口、前端用 batchGetConceptRelations 自建或用其他接口组合。

**后端提供关系图谱 API（待确认）**

前端原计划通过 `GET /api/auth/kg/knowledge-points/{uri}/graph` 获取图谱数据，但后端当前未实现此接口。需与后端确认以下替代方案：
1. 后端补充 `graph` 接口
2. 前端使用 `batchGetConceptRelations` + 已知知识点自行构建图谱
3. 前端使用其他已有接口组合实现

> 证据：详见 `2.OpenSpec design 决策/design-frontend-2026-06-09-knowledge-graph-ui-front.md`（§5. 图谱数据来源）
