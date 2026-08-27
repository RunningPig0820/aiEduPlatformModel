# EDUKG 项目分析
> summary: EDUKG 提供 kg_handler.py/SPARQL 连接器/linking.py/ontology.owl 可复用组件，知识图谱处理器与实体链接复用程度高。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-edukg-项目分析.md
> 类别：数据关联

> 检索摘要：EDUKG 提供 kg_handler.py/SPARQL 连接器/linking.py/ontology.owl 可复用组件，知识图谱处理器与实体链接复用程度高。

EDUKG 提供了以下可复用组件：

| 模块 | 文件 | 功能 | 复用程度 |
|------|------|------|----------|
| 知识图谱处理器 | `kg_handler.py` | TTL 加载、SPARQL 查询 | 高 |
| SPARQL 连接器 | `sparql_query.py` | Jena/Neo4j 连接 | 中（需适配） |
| 实体链接 | `linking.py` | 文本→实体识别 | 高 |
| 本体定义 | `ontology.owl` | 类/属性定义 | 直接使用 |

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§EDUKG 项目分析）
