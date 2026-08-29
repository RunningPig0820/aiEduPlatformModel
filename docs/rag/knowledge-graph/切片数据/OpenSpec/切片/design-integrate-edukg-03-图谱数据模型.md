# 图谱数据模型

> summary: 图谱数据模型
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-03-图谱数据模型.md
> 类别：数据存储

本设计阶段（2026-03-28 设计稿）的 Neo4j 数据模型以知识点实体（Entity）为核心，支持学科分类（Class）与学生学习进度（Student + LEARNED）。与后续落地的完整模型相比，这是早期简化版设计。

## 节点类型

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

## 关系类型

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

## 模型要点

- Entity 为知识点实体，URI 含版本号（3.0）、学科（math）与实例 ID（quadratic-equation-001）
- Class 为学科分类节点（如"方程与不等式"），Class 之间可 SUBCLASS_OF 层级嵌套；Entity 通过 INSTANCE_OF 归属到 Class
- RELATED_TO 携带 predicate 属性区分关联语义（如 prerequisite 前置依赖），区别于 D5 的学习进度关系
- LEARNED 是学生→知识点的学习进度关系，携带 status（掌握状态）、score（得分）、timestamp（时间戳）属性（详见学生学习进度建模块）
