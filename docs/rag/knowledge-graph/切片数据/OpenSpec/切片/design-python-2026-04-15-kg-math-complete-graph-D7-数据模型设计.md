# 数据模型设计

> summary: 数据模型：Textbook/Chapter/Section/TextbookKP节点与CONTAINS、IN_UNIT、MATCHES_KG关系，URI与id设唯一约束。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D7-数据模型设计.md
> 类别：数据存储

---

### D7：数据模型设计

> 检索摘要：数据模型：Textbook/Chapter/Section/TextbookKP节点与CONTAINS、IN_UNIT、MATCHES_KG关系，URI与id设唯一约束。

**节点设计**：

| 节点类型 | 约束 | 属性 |
|---------|------|------|
| Textbook | `uri UNIQUE`, `id UNIQUE` | uri, id, label, stage, grade, semester, publisher, edition |
| Chapter | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order |
| Section | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order, mark |
| TextbookKP | `uri UNIQUE` | uri, label, stage, grade |

**关系设计**：

| 关系类型 | 起点 → 终点 | 语义 | 来源 |
|---------|------------|------|------|
| **CONTAINS** | Textbook → Chapter → Section | 目录层级 | 数据解析 |
| **IN_UNIT** | TextbookKP → Section | 知识点所属单元 | 数据解析 |
| **MATCHES_KG** | TextbookKP → Concept | 匹配图谱 | LLM 推断 |

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D7：数据模型设计）
