# 图谱数据模型与两层结构

> summary: 图谱数据模型与两层结构
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-03-图谱数据模型与两层结构.md
> 类别：数据存储

---

> 检索摘要：图谱有哪些节点和关系？Textbook/Chapter/Section/TextbookKP 怎么设计？URI v3.1 命名规范？教材结构层与语义层怎么连？

## 节点设计（D7）

| 节点类型 | 约束 | 属性 |
|---------|------|------|
| Textbook | uri UNIQUE, id UNIQUE | uri, id, label, stage, grade, semester, publisher, edition |
| Chapter | uri UNIQUE, id UNIQUE | uri, id, label, order |
| Section | uri UNIQUE, id UNIQUE | uri, id, label, order, mark |
| TextbookKP | uri UNIQUE | uri, label, stage, grade |

## 关系设计（D7）

| 关系类型 | 起点→终点 | 语义 | 来源 |
|---------|-----------|------|------|
| CONTAINS | Textbook → Chapter → Section | 目录层级 | 数据解析 |
| IN_UNIT | TextbookKP → Section | 知识点所属单元 | 数据解析 |
| MATCHES_KG | TextbookKP → Concept | 匹配图谱 | LLM 推断 |

## URI 命名规范 v3.1（D8）

格式：`http://edukg.org/knowledge/3.1/{type}/math#{id}`

| 节点类型 | ID 格式 | 示例 |
|---------|---------|------|
| Textbook | {publisher}-{grade}{semester} | renjiao-g1s |
| Chapter | {textbook_id}-{order} | renjiao-g1s-1 |
| Section | {chapter_id}-{order} | renjiao-g1s-1-1 |
| TextbookKP | textbook-{stage}-{seq:05d} | textbook-primary-00001 |

## 两层结构说明

**教材结构层**：Textbook → Chapter → Section → TextbookKP，通过 CONTAINS（目录层级）与 IN_UNIT（知识点所属单元）关系表达教材目录结构。
**语义匹配层**：TextbookKP 通过 MATCHES_KG 关系软连接到 EduKG Concept，打通教材知识点与语义知识图谱（匹配是软连接而非合并，保留两端独立数据）。

匹配阈值（软连接强度）：≥0.9 建 MATCHES_KG 关系；0.7-0.9 建 MATCHES_KG_CANDIDATE 候选关系；<0.7 不匹配。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D7 / §D8 / §D4.1 阈值）
