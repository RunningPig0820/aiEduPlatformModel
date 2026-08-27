## Why

当前 AI 教育平台缺少知识图谱能力，无法构建学科知识点体系，导致：
1. AI 答疑时无法精准识别问题涉及的知识点
2. 学生学习进度无法基于知识点体系进行追踪和可视化
3. 教师备课缺少知识点关联推荐支持

EDUKG 是清华大学开源的 K-12 教育知识图谱，包含 2.52 亿实体、38.6 亿三元组，覆盖 9 大学科（语文、数学、英语、物理、化学、生物、历史、地理、政治），为本项目提供了优质的知识基础。

## What Changes

### 新增功能
- **知识图谱存储层** - Neo4j 图数据库集成，支持 TTL 文件导入
- **知识点查询服务** - SPARQL/Cypher 查询实体、属性、关系
- **实体链接服务** - 从文本中识别知识点实体，支持 AI 答疑场景
- **知识点可视化 API** - 支持前端渲染知识图谱/知识树
- **学生学习进度追踪** - 学生-知识点关联，支持"点亮"知识体系
- **教师备课推荐** - 基于知识点关联的备课内容推荐

### 技术整合
- 复用 EDUKG 的 `kg_handler.py` (RDFLib 图谱处理)
- 复用 EDUKG 的 `linking.py` (实体链接)
- 引入 Neo4j 作为图数据库
- 预留向量数据库接口（Milvus）用于后续 RAG 场景

## Capabilities

### New Capabilities

- `knowledge-graph-core`: 知识图谱核心模块 - Neo4j 连接、数据导入、基础查询
- `entity-linking`: 实体链接服务 - 从文本识别知识点，支持 AI 答疑
- `knowledge-visualization`: 知识点可视化 - 知识树/图谱展示，学生进度追踪
- `teacher-lesson-prep`: 教师备课辅助 - 知识点关联推荐

### Modified Capabilities

无现有 capability 需要修改。

## Impact

### 新增依赖
```
neo4j>=5.0.0          # Neo4j Python 驱动
rdflib>=7.0.0         # RDF 图谱处理
SPARQLWrapper>=2.0.0  # SPARQL 查询
jieba>=0.42.1         # 中文分词
networkx>=3.0         # 图网络分析
```

### 架构变更
```
ai-edu-ai-service/
├── core/
│   ├── gateway/          # 现有 LLM Gateway
│   ├── kg/               # 新增：知识图谱模块
│   │   ├── neo4j_client.py    # Neo4j 连接
│   │   ├── kg_handler.py      # 图谱处理器（复用 EDUKG）
│   │   ├── entity_linker.py   # 实体链接（复用 EDUKG）
│   │   └── graph_builder.py   # 图谱构建工具
│   └── tools/            # 现有工具定义
├── api/
│   ├── chat.py           # 现有 Chat API
│   └── kg.py             # 新增：知识图谱 API
└── models/
    ├── chat.py           # 现有 Chat 模型
    └── kg.py             # 新增：知识图谱模型
```

### 数据存储
- **Neo4j**: 知识图谱存储（实体、关系、属性）
- **TTL 文件**: EDUKG 原始数据导入源
- **向量数据库 (后续)**: 知识点向量索引，支持语义检索

### API 端点
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/kg/entities` | GET | 查询知识点实体 |
| `/api/kg/entity/{uri}` | GET | 获取实体详情 |
| `/api/kg/link` | POST | 文本实体链接 |
| `/api/kg/subject/{subject}/tree` | GET | 获取学科知识树 |
| `/api/kg/student/{student_id}/progress` | GET/POST | 学生知识点进度 |