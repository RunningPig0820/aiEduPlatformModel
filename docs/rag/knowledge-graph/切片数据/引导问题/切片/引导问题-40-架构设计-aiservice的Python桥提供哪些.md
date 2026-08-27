# ai-service 的 Python 桥提供哪些能力？业务查询和通用 CRUD 怎么分？

> summary: 架构设计引导问题回答：Python桥分两层——api/kg.py业务查询(10路由)+api/neo4j.py通用CRUD(12路由,x-internal-token鉴权)，core/rag/query.py是RAG检索编排不是图谱桥
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-40-架构设计-aiservice的Python桥提供哪些.md
> 类别：架构设计

**核心结论**：Python 桥分两层——`api/kg.py` 业务查询（10 路由）面向前端/答疑，`api/neo4j.py` 通用 CRUD（12 路由，x-internal-token 鉴权）面向 Java 做任意操作；`core/rag/query.py` 是 AI 答疑 RAG 检索编排，不是图谱查询桥。

## 分层展开
- **api/kg.py 业务查询**（prefix /api/kg）：实为 10 个路由——`/entities`（按 label 搜索实体）、`/entity/{uri}`（详情）、`/link`（文本实体识别）、`/subject/{subject}/tree`（知识树）、`/classes`（学科分类）、`/student/{id}/progress` GET/POST、`/statistics`（进度统计）、`/recommend`（知识点推荐）、`/learning-path`（学习路径）。方案总揽称"八端点"少算（实 10 路由含 progress 两态）。（依据：分析-01 / 完善文档 03）
- **api/neo4j.py 通用 CRUD**（prefix /api/neo4j）：12 个路由全部走 `x-internal-token` 鉴权（verify_internal_token 比对 settings.INTERNAL_TOKEN，不符 401）——`/health`、`/stats`、`/nodes/{label}` 建/查/改/删/批量/搜索/计数、`/relationships` 建/查、`/query` 裸 Cypher（read_only 默认 true 但调用方可关）。Java 经此桥调 Neo4j。（依据：分析-01 / 完善文档 03）
- **分工原则**：业务查询（api/kg.py）面向前端/答疑，通用 CRUD（api/neo4j.py）面向 Java 做任意操作；通用层用 token 保护并暴露裸查询，方便 Java 侧扩展但风险自担。（依据：分析-01 / 完善文档 03）
- **⚠️ 简化桩**：`get_knowledge_tree`/`get_learning_path`/`get_recommendations` 是简化实现——知识树取该学科前 100 实体平铺两层、学习路径只返回目标实体自身、推荐只看一跳邻居；页面化真层级走 Java 同步 MySQL 侧，别从 Python 桥期待完整图谱能力。（依据：分析-01 / 完善文档 03）
- **接口坑**：`/api/neo4j` 默认 `id_property="id"`，但 edukg 节点主键是 `uri`，Java 调用需显式传 `id_property=uri` 否则查不到。（依据：分析-01）

## 追问防御
- **可能追问：Java 怎么调 Neo4j？** → 经 Python 桥调——api/neo4j.py 通用 CRUD 带 x-internal-token；裸 `/query` 是后门，read_only 默认 true，生产需确保 token 不泄露。（依据：分析-01）
- **可能追问：core/rag/query.py 是图谱桥吗？** → 不是——它是 AI 答疑口述 RAG 检索编排（检索图谱文档切片按模块锚点召回），图谱数据查询走 api/kg.py + api/neo4j.py，两条链路独立，面试表述勿混。（依据：分析-01 / 完善文档 03）
- **可能追问：Python 桥能力够用吗？** → 知识树/学习路径/推荐是简化桩，页面化真层级走 Java 同步 MySQL 侧，别从 Python 桥期待完整图谱能力。（依据：分析-01）

> 证据：详见 `3.代码/分析-01-知识图谱整体架构与数据链路.md` ｜ `4.完善文档/03-架构与三端分工.md`
