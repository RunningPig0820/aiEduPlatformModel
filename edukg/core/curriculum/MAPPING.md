# 知识图谱元素与关系映射

## 元素类型与对应文件

| 元素类型 | 处理文件 | 类名 | 输出文件 | 说明 |
|---------|---------|------|---------|------|
| **Class** | `class_extractor.py` | `ClassExtractor` | `classes.json` | 概念类（如：数学概念、数学方法） |
| **Concept** | `concept_extractor.py` | `ConceptExtractor` | `concepts.json` | 知识点实体（如：凑十法、有理数） |
| **Statement** | `statement_extractor.py` | `StatementExtractor` | `statements.json` | 定义描述（如：凑十法的定义） |
| **Relation** | `relation_extractor.py` | `RelationExtractor` | `relations.json` | 关系（HAS_TYPE、RELATED_TO等） |

---

## 关系类型与处理位置

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           关系类型映射                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. HAS_TYPE (知识点 → 概念类)                                               │
│     ─────────────────────────────                                           │
│     处理文件: concept_extractor.py                                          │
│     处理类: ConceptExtractor                                                │
│     生成位置: generate_concept() 方法                                        │
│     格式: Concept.types 字段                                                │
│     示例:                                                                   │
│       凑十法 ──HAS_TYPE──▶ 数学方法                                          │
│                                                                             │
│  2. RELATED_TO (定义 → 知识点)                                               │
│     ─────────────────────────────                                           │
│     处理文件: relation_extractor.py                                         │
│     处理类: RelationExtractor                                               │
│     生成位置: generate_statement_concept_relations() 方法                   │
│     判断方式: 规则匹配（Statement标签去掉"的定义"）                            │
│     示例:                                                                   │
│       凑十法的定义 ──RELATED_TO──▶ 凑十法                                    │
│                                                                             │
│  3. PART_OF (部分 → 整体)                                                   │
│     ─────────────────────────────                                           │
│     处理文件: relation_extractor.py                                         │
│     处理类: RelationExtractor                                               │
│     生成位置: extract_concept_relations() 方法                              │
│     判断方式: LLM 分析                                                       │
│     示例:                                                                   │
│       20以内加法 ──PART_OF──▶ 加法                                           │
│                                                                             │
│  4. BELONGS_TO (子类 → 父类)                                                │
│     ─────────────────────────────                                           │
│     处理文件: relation_extractor.py                                         │
│     处理类: RelationExtractor                                               │
│     生成位置: extract_concept_relations() 方法                              │
│     判断方式: LLM 分析                                                       │
│     示例:                                                                   │
│       凑十法 ──BELONGS_TO──▶ 进位加法                                        │
│                                                                             │
│  5. SUB_CLASS_OF (概念类 → 父概念类)                                         │
│     ─────────────────────────────                                           │
│     处理文件: class_extractor.py                                            │
│     处理类: ClassExtractor                                                  │
│     生成位置: generate_class_definition() 方法                              │
│     格式: Class.parents 字段                                                │
│     示例:                                                                   │
│       小学数概念 ──SUB_CLASS_OF──▶ 数学概念                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 详细文件说明

### 1. class_extractor.py - Class 处理

```python
ClassExtractor:
    ├── existing_classes     # 38个现有Class列表
    ├── class_parents        # Class层级映射
    │
    ├── infer_type()         # LLM推断知识点类型
    │   └── 返回: ClassExtractionResult
    │       ├── class_label  # 匹配的Class名称
    │       ├── is_new_class # 是否新增Class
    │       └── parent_class # 父Class（新增时）
    │
    ├── generate_class_definition()  # 生成Class定义
    │   └── 输出: {
    │         "uri": "...",
    │         "label": "小学数概念",
    │         "parents": ["...数学概念URI..."],  # SUB_CLASS_OF
    │         "type": "owl:Class"
    │       }
    │
    └── 输出: classes.json
```

**处理的元素**: Class
**处理的关系**: SUB_CLASS_OF（通过 `parents` 字段）

---

### 2. concept_extractor.py - Concept 处理

```python
ConceptExtractor:
    ├── uri_generator        # URI生成器
    │
    ├── generate_concept(label, class_id)
    │   └── 输出: {
    │         "uri": "...",
    │         "label": "凑十法",
    │         "types": ["shuxuefangfa-xxx"]  # HAS_TYPE 关系
    │       }
    │
    └── 输出: concepts.json
```

**处理的元素**: Concept
**处理的关系**: HAS_TYPE（通过 `types` 字段）

---

### 3. statement_extractor.py - Statement 处理

```python
StatementExtractor:
    ├── llm                  # LLM调用器
    │
    ├── generate_definition(knowledge_point)
    │   └── LLM生成知识点定义
    │
    ├── generate_statement(concept_label, concept_uri, definition)
    │   └── 输出: {
    │         "uri": "...",
    │         "label": "凑十法的定义",
    │         "types": ["shuxuedingyi-xxx"],
    │         "content": "凑十法是一种计算方法..."
    │       }
    │
    └── 输出: statements.json
```

**处理的元素**: Statement
**处理的关系**: 无（RELATED_TO 在 relation_extractor 中处理）

---

### 4. relation_extractor.py - Relation 处理

```python
RelationExtractor:
    │
    ├── generate_related_to_relation()      # RELATED_TO
    │   └── Statement → Concept
    │   └── 判断方式: 规则匹配
    │   └── 输出: {
    │         "from": {"uri": "...", "label": "凑十法的定义"},
    │         "relation": "relatedTo",
    │         "to": {"uri": "...", "label": "凑十法"}
    │       }
    │
    ├── generate_part_of_relation()         # PART_OF
    │   └── Concept → Concept (部分-整体)
    │   └── 判断方式: LLM分析
    │   └── 输出: {
    │         "from": {"uri": "...", "label": "20以内加法"},
    │         "relation": "partOf",
    │         "to": {"uri": "...", "label": "加法"}
    │       }
    │
    ├── generate_belongs_to_relation()      # BELONGS_TO
    │   └── Concept → Concept (所属关系)
    │   └── 判断方式: LLM分析
    │   └── 输出: {
    │         "from": {"uri": "...", "label": "凑十法"},
    │         "relation": "belongsTo",
    │         "to": {"uri": "...", "label": "进位加法"}
    │       }
    │
    ├── generate_statement_concept_relations()  # 批量生成RELATED_TO
    │   └── 遍历所有Statement，匹配对应Concept
    │
    ├── extract_concept_relations()             # LLM提取PART_OF/BELONGS_TO
    │   └── 调用LLM分析知识点之间的关系
    │
    └── 输出: relations.json
```

**处理的元素**: Relation
**处理的关系**: RELATED_TO、PART_OF、BELONGS_TO

---

## 关系类型汇总表

| 关系类型 | 起点 | 终点 | 处理文件 | 判断方式 | 存储位置 |
|---------|------|------|---------|---------|---------|
| **SUB_CLASS_OF** | Class | Class | `class_extractor.py` | 规则映射 | `classes.json` → `parents` 字段 |
| **HAS_TYPE** | Concept | Class | `concept_extractor.py` | LLM推断 | `concepts.json` → `types` 字段 |
| **RELATED_TO** | Statement | Concept | `relation_extractor.py` | 规则匹配 | `relations.json` |
| **PART_OF** | Concept | Concept | `relation_extractor.py` | LLM分析 | `relations.json` |
| **BELONGS_TO** | Concept | Concept | `relation_extractor.py` | LLM分析 | `relations.json` |

---

## 图谱结构示意

```
                    ┌──────────────┐
                    │    数学      │
                    │   (Class)    │
                    └──────┬───────┘
                           │ SUB_CLASS_OF
                    ┌──────▼───────┐
                    │  数学概念    │
                    │   (Class)    │
                    └──────┬───────┘
                           │ SUB_CLASS_OF
        ┌──────────────────┼──────────────────┐
        │                  │                  │
 ┌──────▼───────┐   ┌──────▼───────┐   ┌──────▼───────┐
 │  小学数概念  │   │   几何概念   │   │   代数概念   │
 │   (Class)    │   │   (Class)    │   │   (Class)    │
 └──────┬───────┘   └──────────────┘   └──────────────┘
        │ HAS_TYPE
 ┌──────▼───────┐
 │   有理数     │
 │  (Concept)   │────────────────────────────┐
 └──────────────┘                            │ BELONGS_TO
        │                                    │
        │ RELATED_TO                  ┌──────▼───────┐
 ┌──────▼───────────┐                 │   实数       │
 │ 有理数的定义     │                 │  (Concept)   │
 │   (Statement)    │                 └──────────────┘
 │ content: "..."   │
 └──────────────────┘
```

---

## 快速查找

### 我要处理 HAS_TYPE 关系？
→ `concept_extractor.py` → `ConceptExtractor.generate_concept()`

### 我要处理 RELATED_TO 关系？
→ `relation_extractor.py` → `RelationExtractor.generate_statement_concept_relations()`

### 我要处理 PART_OF 关系？
→ `relation_extractor.py` → `RelationExtractor.extract_concept_relations()` (LLM)

### 我要处理 BELONGS_TO 关系？
→ `relation_extractor.py` → `RelationExtractor.extract_concept_relations()` (LLM)

### 我要处理 SUB_CLASS_OF 关系？
→ `class_extractor.py` → `ClassExtractor.generate_class_definition()`