# EDUKG
EDUKG: a Heterogeneous Sustainable K-12 Educational Knowledge Graph

EduKG is proposed and maintained by the Knowledge Engineering Group of Tsinghua Univerisity. It is a heterogeneous, sustainable K-12 educational knowledge graph with an interdisciplinary and fine-grained ontology. This repository consists of **38** well-constructed knowledge graphs (more than **252 million** entities and **3.86 billion** triplets) under the ontology.

 In general, our contributions are summarized as follows:

1. An interdisciplinary, fine-grained ontology uniformly represents K-12 educational knowledge, resources, and heterogeneous data with 635 classes, 445 object properties, and 1314 datatype properties;

2. A large-scale, heterogeneous K-12 educational KG with more than 252 million entities and 3.86 billion triplets based on the data from massive educa- tional and external resources;

3. A flexible and sustainable construction and maintenance mechanism empowers EDUKG to evolve dynamically, where we design guiding schema of the construction methodology as hot-swappable, and we simultaneously monitor 32 different data sources for incrementally infusing heterogeneous data.

---

## 人教版数学知识图谱（本项目）

本项目基于 EduKG 本体，构建了**人教版 K12 数学知识图谱**，已完成教材到知识点的完整映射。

### 图谱概览

```
┌─────────────────────────────────────────────────────────┐
│           Neo4j 数学知识图谱                              │
├─────────────────────────────────────────────────────────┤
│ 节点: 6,757                                              │
│   Textbook (教材):        23                            │
│   Chapter (章节):        148                            │
│   Section (小节):        580                            │
│   TextbookKP (知识点):  1,740                            │
│   Concept (EduKG概念):  1,295                            │
│   Statement (定义):     2,932                            │
│   Class (概念类):         39                            │
│                                                          │
│ 关系: 20,887                                              │
│   CONTAINS (包含):        728                           │
│   IN_UNIT (归属):       1,740                           │
│   MATCHES_KG (匹配):    1,690                           │
│   HAS_TYPE (类型):       5,591                           │
│   RELATED_TO (关联):    10,183                           │
│   BELONGS_TO (属于):      619                           │
│   PART_OF (部分):         298                           │
│   SUB_CLASS_OF (子类):     38                           │
│                                                          │
│ 质量指标                                                  │
│   匹配率: 97.1% (1690/1740)                             │
│   置信度: 0.975                                         │
│   URI唯一: 100%                                         │
└─────────────────────────────────────────────────────────┘
```

### 数据模型与关系

#### 节点类型说明

| 类型 | 标签 | 含义 | 数量 | 核心属性 |
|------|------|------|------|----------|
| 教材 | Textbook | 人教版教材册次 | 23 | `label`(名称), `grade`(年级), `phase`(学段: primary/middle/high) |
| 章节 | Chapter | 教材中的章节 | 148 | `label`, `topic`(专题), `textbook_id` |
| 小节 | Section | 教材中的小节 | 580 | `label`, `chapter_id` |
| 教材知识点 | TextbookKP | 教材关联的知识点 | 1,740 | `label`, `section_id`, `textbook_id`, `difficulty`, `importance`, `cognitive_level` |
| EduKG概念 | Concept | 图谱知识点实体 | 1,295 | `label`, `uri`, `subject`(学科) |
| 概念类 | Class | 知识点分类 | 39 | `label`(如:数学定义、数学定理等) |
| 定义/定理 | Statement | 概念的具体描述 | 2,932 | `label`, `content`(完整内容) |

#### 关系说明

| 关系 | 方向 | 含义 | 数量 | 说明 |
|------|------|------|------|------|
| CONTAINS | Textbook → Chapter | 教材包含章节 | 728 | 结构关系 |
| CONTAINS | Chapter → Section | 章节包含小节 | | 结构关系 |
| IN_UNIT | TextbookKP → Section | 知识点归属小节 | 1,740 | 每个知识点归属一个Section |
| MATCHES_KG | TextbookKP → Concept | 教材知识点匹配EduKG概念 | 1,690 | 通过向量检索+LLM匹配，置信度≥0.5 |
| HAS_TYPE | Concept/Statement → Class | 概念/定义属于某个类型 | 5,591 | 分类关系 |
| RELATED_TO | Statement → Concept | 定义/定理关联到概念 | 10,183 | 内容关联 |
| BELONGS_TO | Class → Class | 类的归属 | 619 | 分类层级 |
| PART_OF | Concept → Concept | 概念的部分关系 | 298 | 组合关系 |
| SUB_CLASS_OF | Class → Class | 类的子类关系 | 38 | 继承关系 |

#### 全链路路径

```
Textbook ──CONTAINS──▶ Chapter ──CONTAINS──▶ Section
                                                   ◀──IN_UNIT── TextbookKP ──MATCHES_KG──▶ Concept
                                                                                              │
                                                                                    ┌──HAS_TYPE──▶ Class
                                                                                    │
                                                                                    └──RELATED_TO──▶ Statement
```

**关键约束**:
1. 每个 TextbookKP 有且仅有一个 `IN_UNIT` 关系指向 Section
2. TextbookKP 通过 `MATCHES_KG` 匹配到 EduKG Concept（97.1% 匹配率，50 个未匹配）
3. `RELATED_TO` 方向固定：Statement → Concept
4. `content` 属性在 **Statement** 节点上，不在 Concept 上
5. 所有关系均不可逆，页面化查询需注意方向

### URI 设计

所有节点使用统一 URI 前缀 `http://edukg.org/knowledge/`，版本区分数据来源：

| 版本 | 前缀 | 数据来源 |
|------|------|----------|
| v0.1 | `/0.1/instance/math#xxx` | EduKG 原始 Concept/Statement/Class |
| v0.2 | `/0.2/instance/math#xxx` | 小学新增数据 |
| v3.1 | `/3.1/textbook/xxx` | 人教版教材数据 (Textbook/Chapter/Section/TextbookKP) |

### Neo4j 连接

```
URI: bolt://81.71.130.57:7687
用户名: neo4j
密码: 见 ai-edu-ai-service/.env
```

---

## 知识图谱页面化 - 设计指南

本指南面向前端/页面化服务开发者，提供图谱查询和展示的关键信息。

### 常用查询示例

```cypher
-- 1. 查询某教材的完整结构 (Textbook → Chapter → Section)
MATCH (t:Textbook {label: '一年级上册'})-[:CONTAINS]->(c:Chapter)-[:CONTAINS]->(s:Section)
RETURN t, c, s

-- 2. 查询某小节的所有知识点
MATCH (s:Section {label: '10以内数的认识'})<-[:IN_UNIT]-(k:TextbookKP)
RETURN s, k

-- 3. 查询知识点匹配的EduKG概念
MATCH (k:TextbookKP {label: '10以内数的认识'})-[r:MATCHES_KG]->(c:Concept)
RETURN k, r.confidence as confidence, c

-- 4. 查询某概念的定义/定理
MATCH (c:Concept {label: '加法'})<-[:RELATED_TO]-(s:Statement)
RETURN c, s

-- 5. 查询某概念的分类
MATCH (c:Concept {label: '加法'})-[:HAS_TYPE]->(cl:Class)
RETURN c, cl

-- 6. 查询知识点的完整路径 (从教材到概念)
MATCH path = (t:Textbook)-[:CONTAINS*]->(s:Section)<-[:IN_UNIT]-(k:TextbookKP)-[:MATCHES_KG]->(c:Concept)
WHERE k.label = '混合运算'
RETURN path

-- 7. 查询某专题下的所有知识点
MATCH (c:Chapter {topic: '数与代数'})-[:CONTAINS]->(s:Section)<-[:IN_UNIT]-(k:TextbookKP)
RETURN c.topic, s.label, k.label, k.difficulty, k.importance
```

### 页面展示建议

#### 知识树视图
```
教材
├── 第一章
│   ├── 1.1 小节
│   │   ├── 知识点 A (difficulty: easy, importance: high)
│   │   │   └── EduKG Concept: xxx
│   │   └── 知识点 B
│   └── 1.2 小节
└── 第二章
```

#### 知识图谱关系视图
```
Concept ←── RELATED_TO ── Statement (定义内容)
  │
  │ MATCHES_KG (confidence: 0.95)
  │
TextbookKP ←── IN_UNIT ── Section ←── CONTAINS ── Chapter
```

### 数据文件位置

如需离线使用 JSON 数据：
- 教材数据: `edukg/data/edukg/math/5_教材目录(Textbook)/output/`
  - `textbooks.json` (23 条)
  - `chapters.json` (148 条)
  - `sections.json` (580 条)
  - `textbook_kps.json` (1,740 条)
  - `in_unit_relations.json` (1,740 条)
  - `matches_kg_relations.json` (1,690 条 matched, 50 条 unmatched)

### 项目总结

详细的项目历程见: `edukg/scripts/kg_data/PROJECT_SUMMARY.md`

---

## Updates
May.13rd:
- The first version of our repository is officially online!!!
- New heterogeneous database parsed and uploaded: NBSC, BioGRID

## Resources

[保留原始 EduKG 资源表格...]

## Toolkits

[保留原始 EduKG 工具包说明...]

## Reference

[保留原始引用...]