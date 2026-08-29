# 学生学习进度建模（LEARNED 关系）

> summary: 学生学习进度建模（LEARNED 关系）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-19-学生学习进度建模.md
> 类别：数据存储

## 设计动机

学生学习进度可视化是知识图谱三大业务场景之一（另两个：AI 答疑识别知识点、教师备课推荐）。进度数据本质是图关系，因此直接落 Neo4j 关系扩展，避免引入额外数据库（决策 D5）。

## 数据模型

在 Neo4j 中增加 Student 节点与 LEARNED 关系：

```cypher
(Student {id: "student_001"})
  -[:LEARNED {status: "mastered", score: 95, timestamp: "2024-01-01"}]-> 
(Entity {uri: "edukg:math:quadratic-equation"})
```

- **Student 节点**：id/name 属性，标识学生个体
- **LEARNED 关系**：携带 status（掌握状态，如 mastered）、score（得分）、timestamp（时间戳）属性，指向已学知识点 Entity
- **价值**：便于查询学生的知识点邻居（如学了一元二次方程后可关联其前置/相关知识点），支撑学习进度可视化

## 实施步骤（阶段四：学习进度）

1. 设计学生-知识点关系模型
2. 实现进度追踪 API
3. 集成测试

## 待决策

学生进度是否需要同步到 Java 后端数据库？（开放问题，待定）
