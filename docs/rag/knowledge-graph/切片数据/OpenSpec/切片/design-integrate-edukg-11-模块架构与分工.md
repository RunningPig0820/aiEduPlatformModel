# 模块架构与分工

> summary: 模块架构与分工
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-11-模块架构与分工.md
> 类别：架构设计

## API 设计风格（D4）：RESTful + 三层架构

选择 RESTful API、三层架构，与现有 LLM Gateway 风格一致，便于扩展和维护。

架构层次：
- **API Layer**（`api/kg.py`）：请求验证、响应格式化
- **Service Layer**（`core/kg/service.py`）：业务逻辑、数据组装
- **Data Layer**（`core/kg/neo4j_client.py`）：Neo4j 连接、Cypher 查询

## 整体架构（kg 模块落位）

在 ai-edu-ai-service 内新增 kg 模块：

```
api/kg.py              # Knowledge Graph API (NEW)
core/kg/
  ├── neo4j_client.py  # Neo4j 连接管理
  ├── entity_linker.py # 实体链接 (jieba + 内存词典)
  ├── graph_builder.py # 图谱构建工具
  └── service.py       # 业务服务层
models/kg.py           # KG 模型 (NEW)
```

分工边界：
- Python 服务端（ai-edu-ai-service）承载 API/服务/数据访问三层，实体链接与图谱查询均在服务内完成，不引入 Elasticsearch
- 图数据存独立 Neo4j 服务器（已有独立服务器，无需部署），Python 侧通过 neo4j_client 连接
- LLM Providers（智谱/DeepSeek）走既有 LLM Gateway，与 kg 模块解耦

## 基础设施搭建（阶段一）

1. 配置 Neo4j 连接（已有独立服务器）
2. 创建 `core/kg/` 模块结构
3. 实现 `neo4j_client.py` 连接管理
4. 实现 `entity_linker.py` 内存词典实体链接
