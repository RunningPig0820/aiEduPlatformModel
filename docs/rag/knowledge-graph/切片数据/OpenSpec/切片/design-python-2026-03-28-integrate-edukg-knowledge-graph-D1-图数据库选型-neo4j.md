# D1 图数据库选型 → Neo4j
> summary: 图数据库选型 Neo4j：企业级成熟、社区版免费、n10s 原生支持 RDF/TTL 导入、Cypher 易学；备选 rdflib/Jena/NebulaGraph 各有短板。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-D1-图数据库选型-neo4j.md
> 类别：架构设计

> 检索摘要：图数据库选型 Neo4j：企业级成熟、社区版免费、n10s 原生支持 RDF/TTL 导入、Cypher 易学；备选 rdflib/Jena/NebulaGraph 各有短板。

**选择**: Neo4j
**原因**:
- 成熟的企业级图数据库，社区版免费
- 原生支持 RDF/TTL 导入（n10s 插件）
- Cypher 查询语言易学，文档完善
- EDUKG 已提供 Neo4j 导入代码

**备选方案**:
- **rdflib 内存**: 开发快，但不支持持久化和并发
- **Apache Jena**: 需要 Java 环境，运维复杂
- **NebulaGraph**: 国产图数据库，但社区生态较小

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§D1 图数据库选型 → Neo4j）
