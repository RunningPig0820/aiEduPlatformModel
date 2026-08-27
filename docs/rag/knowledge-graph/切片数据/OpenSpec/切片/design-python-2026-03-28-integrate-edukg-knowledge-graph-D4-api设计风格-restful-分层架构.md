# D4 API 设计风格 → RESTful + 分层架构
> summary: API 采用 RESTful 三层架构与现有 LLM Gateway 风格一致，分 API Layer/Service Layer/Data Layer 便于扩展维护。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-D4-api设计风格-restful-分层架构.md
> 类别：架构设计

> 检索摘要：API 采用 RESTful 三层架构与现有 LLM Gateway 风格一致，分 API Layer/Service Layer/Data Layer 便于扩展维护。

**选择**: RESTful API，三层架构
**原因**:
- 与现有 LLM Gateway 风格一致
- 便于扩展和维护

**架构层次**:
```
┌─────────────────────────────────────────┐
│           API Layer (api/kg.py)          │
│  - 请求验证、响应格式化                    │
├─────────────────────────────────────────┤
│       Service Layer (core/kg/service.py) │
│  - 业务逻辑、数据组装                      │
├─────────────────────────────────────────┤
│     Data Layer (core/kg/neo4j_client.py) │
│  - Neo4j 连接、Cypher 查询                │
└─────────────────────────────────────────┘
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§D4 API 设计风格 → RESTful + 分层架构）
