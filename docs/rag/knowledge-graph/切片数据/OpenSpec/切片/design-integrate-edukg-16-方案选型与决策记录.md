# 方案选型与决策记录

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-16-方案选型与决策记录.md
> 类别：架构设计

本文档（2026-03-28 集成 EduKG 设计稿）共记录 5 项关键决策 D1~D5。

## D1 图数据库选型 → Neo4j

- **原因**：成熟的企业级图数据库，社区版免费；原生支持 RDF/TTL 导入（n10s 插件）；Cypher 查询语言易学、文档完善；EDUKG 已提供 Neo4j 导入代码
- **备选**：rdflib 内存（开发快，但不支持持久化和并发）、Apache Jena（需要 Java 环境，运维复杂）、NebulaGraph（国产图数据库，但社区生态较小）

## D2 数据导入策略 → TTL + 批量导入

- **选择**：EDUKG TTL 文件经 `n10s.rdf.import` 批量导入 Neo4j
- **原因**：EDUKG 已提供 TTL 格式数据；n10s 插件原生支持 RDF 导入；批量导入性能优于逐条插入
- **流程**：graphconfig.init → nsprefixes.add → rdf.import.fetch

## D3 实体链接方案 → 结巴分词 + 内存词典

- **原因**：已验证效果良好；支持自定义词典；轻量级无需额外服务；内存占用仅约 20MB，远低于 Elasticsearch（1-2GB）
- **流程**：启动时加载实体词典到内存（约 4 万实体、约 10MB）→ 输入文本 → jieba.lcut() + 自定义词典 → 内存字典 O(1) 匹配 → 返回 [{label, uri, positions}]

## D4 API 设计风格 → RESTful + 分层架构

- **原因**：与现有 LLM Gateway 风格一致，便于扩展和维护
- **三层**：API Layer（api/kg.py）/ Service Layer（core/kg/service.py）/ Data Layer（core/kg/neo4j_client.py）

## D5 学生进度存储 → Neo4j 关系扩展

- **原因**：进度数据本质是图关系，便于查询学生的知识点邻居，避免引入额外数据库
- **模型**：新增 Student 节点与 LEARNED 关系，如 `(Student {id:"student_001"})-[:LEARNED {status:"mastered", score:95, timestamp:"2024-01-01"}]->(Entity {uri:"edukg:math:quadratic-equation"})`
