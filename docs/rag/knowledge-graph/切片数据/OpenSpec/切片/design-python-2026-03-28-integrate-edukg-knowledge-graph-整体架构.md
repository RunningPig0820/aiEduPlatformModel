# 整体架构
> summary: 新增 kg 模块落 api/kg.py、core/kg（neo4j_client/entity_linker/graph_builder/service）与 models/kg.py，图数据存独立 Neo4j 服务器。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-整体架构.md
> 类别：架构设计

> 检索摘要：新增 kg 模块落 api/kg.py、core/kg（neo4j_client/entity_linker/graph_builder/service）与 models/kg.py，图数据存独立 Neo4j 服务器。

```
┌─────────────────────────────────────────────────────────────────┐
│                        ai-edu-ai-service                         │
├─────────────────────────────────────────────────────────────────┤
│  api/                                                            │
│  ├── chat.py          # LLM Chat API                            │
│  └── kg.py            # Knowledge Graph API (NEW)               │
├─────────────────────────────────────────────────────────────────┤
│  core/                                                           │
│  ├── gateway/         # LLM Gateway (现有)                       │
│  └── kg/              # Knowledge Graph (NEW)                   │
│      ├── neo4j_client.py    # Neo4j 连接管理                     │
│      ├── entity_linker.py   # 实体链接 (jieba + 内存词典)         │
│      ├── graph_builder.py   # 图谱构建工具                        │
│      └── service.py         # 业务服务层                          │
├─────────────────────────────────────────────────────────────────┤
│  models/                                                         │
│  ├── chat.py          # Chat 模型 (现有)                         │
│  └── kg.py            # KG 模型 (NEW)                           │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐
│   LLM Providers │          │       Neo4j         │
│  (智谱/DeepSeek) │          │   (独立服务器)       │
└─────────────────┘          │    │
                             └─────────────────────┘
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§整体架构）
