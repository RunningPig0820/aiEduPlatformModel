# core/rag/query.py 是图谱查询桥吗？它和 api/kg.py 什么关系？

> summary: 架构设计引导问题回答：不是——core/rag/query.py是AI答疑口述RAG检索编排(检索图谱文档切片)，图谱数据查询走api/kg.py+api/neo4j.py，两条链路独立
> 权威度: 1.0（合成问答答案切片，非原始证据）
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/引导问题/引导问题-43-架构设计-coreragquerypy是图谱查询桥.md
> 类别：架构设计

**核心结论**：不是——`core/rag/query.py` 是 AI 答疑**口述 RAG 检索编排**，检索的是图谱**文档切片**（按模块锚点召回进 RAG 池）；图谱数据查询走 `api/kg.py` + `api/neo4j.py`，两条链路独立，面试表述勿混。

## 分层展开
- **定位**：`core/rag/query.py` 是 AI 答疑 RAG 检索编排——`MODULE_ANCHORS` 四模块闭集包含 `knowledge-graph`（query.py:68），`MODULE_ANCHOR_RULES` 关键词"知识图谱/图谱/neo4j/知识点/概念/关系/节点"→ knowledge-graph 锚点（query.py:71-76）；检索的是图谱文档切片进 RAG 池，**不是 Neo4j 节点数据**。（依据：分析-01 / 完善文档 03）
- **检索流程**：`rag_query` → `intent`（LLM 结构化意图，失败回退关键词）→ `retrieve_dual`（全量池向量 + 切片池双向量 + BM25）→ `orchestrate`（RRF×authority×节锚定加权）→ `generate`（doubao 面试口述答案）；参数 RRF_K=60 / TOP_K=5 / BM25_K=10 / VEC_K=12。（依据：分析-01）
- **与 api/kg.py 的关系**：两条独立链路——`api/kg.py` 是图谱在线业务查询（/entities、/entity/{uri}、/link、/tree、/learning-path 等，面向前端/答疑）；`core/rag/query.py` 是文档语料检索（面向面试口述/引导问答回答）。图谱数据查询走 api/kg.py + api/neo4j.py，不是 query.py。（依据：分析-01 / 完善文档 03）
- **面试表述注意**：勿把"RAG 语料检索"说成"图谱数据查询"——query.py 检索的是图谱模块的文档切片（语料池），不是 Neo4j 里的 6757 个节点。（依据：分析-01）

## 追问防御
- **可能追问：那图谱数据查询走哪？** → api/kg.py（业务查询）+ api/neo4j.py（通用 CRUD，x-internal-token 鉴权）——这是图谱在线数据查询链路。（依据：分析-01 / 完善文档 03）
- **可能追问：query.py 检索的是什么？** → 图谱模块的文档切片（语料池），通过模块锚点 + 关键词规则召回，不是 Neo4j 节点/关系数据。（依据：分析-01）
- **可能追问：两条链路会混吗？** → 定位明确：query.py 管"关于图谱的问答回答"，api/kg.py 管"图谱数据的实时查询"，两者服务不同场景。（依据：分析-01 / 完善文档 03）

> 证据：详见 `3.代码/分析-01-知识图谱整体架构与数据链路.md` ｜ `4.完善文档/03-架构与三端分工.md`
