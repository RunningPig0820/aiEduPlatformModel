# 数据模型 (Neo4j)
> summary: Neo4j 数据模型含 Entity 知识点/Class 学科分类/Student 学生节点，SUBCLASS_OF/INSTANCE_OF/RELATED_TO/LEARNED 等关系。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-数据模型-neo4j.md
> 类别：数据存储

> 检索摘要：Neo4j 数据模型含 Entity 知识点/Class 学科分类/Student 学生节点，SUBCLASS_OF/INSTANCE_OF/RELATED_TO/LEARNED 等关系。

**节点类型**:
```cypher
// 知识点实体
(:Entity {
  uri: "http://edukg.org/knowledge/3.0/instance/math#quadratic-equation-001",
  label: "一元二次方程",
  subject: "math",
  description: "..."
})

// 学科分类
(:Class {
  uri: "http://edukg.org/knowledge/3.0/class/math#main-C10",
  label: "方程与不等式"
})

// 学生
(:Student {
  id: "student_001",
  name: "张三"
})
```

**关系类型**:
```cypher
// 知识点层级关系
(:Entity)-[:SUBCLASS_OF]->(:Entity)
(:Entity)-[:INSTANCE_OF]->(:Class)
(:Class)-[:SUBCLASS_OF]->(:Class)

// 知识点关联关系
(:Entity)-[:RELATED_TO {predicate: "prerequisite"}]->(:Entity)
(:Entity)-[:HAS_PROPERTY]->(:Property)

// 学生学习进度
(:Student)-[:LEARNED {status, score, timestamp}]->(:Entity)
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§数据模型 (Neo4j)）
