# 服务接入（GraphRAG）

> summary: 服务接入(GraphRAG 学生提问→提取知识点→前置/考法/例题→引导式答疑; 掌握度薄弱根因诊断; api/kg.py 八端点 + api/neo4j.py 通用 CRUD x-internal-token)
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案总揽-10-服务接入GraphRAG.md
> 类别：操作流程

---

### 10. 服务接入（GraphRAG）

- **GraphRAG 工作流**：学生提问题目 → 提取核心知识点 → Neo4j 查该知识点的前置依赖/对应考法/典型例题 → 生成「前置知识点回顾→考点讲解→解题步骤引导→易错点提醒」引导式答疑；Cypher 用 `[:前置依赖*1..2]` 控制链路深度、`collect(DISTINCT pre)` 等。
- **与掌握度联动**：学生答题记录 → 错题对应知识点 → 查前置依赖链路 → 结合正确率/答题次数算每个知识点掌握度 → 定位薄弱根源（当前点没掌握 vs 前置没学好）。
- **与答疑闭环**：知识图谱作为 AI 对话助手"活文档"，「学生提问→知识图谱检索→引导式答疑→精准回复」，答疑记录回流支撑家长端薄弱点报表。
- **与题型分析**：题目"考察"知识点关系支撑 AI 组卷（按知识点全覆盖/难度梯度/题型占比）。
- **Python 服务 API**（`api/kg.py`，prefix `/api/kg`）：`/entities` 搜索、`/entity/{uri}` 详情、`/link` 实体识别、`/subject/{subject}/tree` 知识树（depth 默认3 最大5）、`/subject/{subject}/classes`、`/student/{id}/progress`、`/recommend`、`/learning-path`。
- **Neo4j 通用 API**（`api/neo4j.py`，prefix `/api/neo4j`，`x-internal-token` 鉴权）：`/health`、`/stats`、`/nodes/{label}`（+batch/search/count）、`/relationships`、`/query`（裸 Cypher，read_only 默认 true）。
- **实体链接**（`core/kg/entity_linker.py`）：jieba 分词 + 内存实体字典（从 `data/edukg/entities/*_entities.json` 加载，~40,000 实体约 10MB）做实体链接。

> 证据：详见 `1.语雀/语雀-方案总揽.md`（§10）
