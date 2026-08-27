# D5 学生进度存储 → Neo4j 关系扩展
> summary: 学生进度在 Neo4j 增加 Student 节点与 LEARNED 关系，进度数据本质是图关系便于查询知识点邻居，避免引入额外数据库。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-D5-学生进度存储-neo4j-关系扩展.md
> 类别：数据存储

> 检索摘要：学生进度在 Neo4j 增加 Student 节点与 LEARNED 关系，进度数据本质是图关系便于查询知识点邻居，避免引入额外数据库。

**选择**: 在 Neo4j 中增加 Student 节点和 LEARNED 关系
**原因**:
- 进度数据本质是图关系
- 便于查询学生的知识点邻居
- 避免引入额外数据库

**数据模型**:
```cypher
(Student {id: "student_001"})
  -[:LEARNED {status: "mastered", score: 95, timestamp: "2024-01-01"}]->
(Entity {uri: "edukg:math:quadratic-equation"})
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§D5 学生进度存储 → Neo4j 关系扩展）
