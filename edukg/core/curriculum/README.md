# 课标知识点提取模块

从课标 PDF 构建 Neo4j 知识图谱的完整流程。

---

## 快速开始

```bash
# 完整流程（从 OCR 结果生成 4 个 JSON 文件）
python -m edukg.core.curriculum.kg_main

# 分步执行
python -m edukg.core.curriculum.pdf_ocr --pdf-path 课标.pdf           # 步骤1: OCR
python -m edukg.core.curriculum.kp_extraction --ocr-result ocr.json   # 步骤2: 提取知识点
python -m edukg.core.curriculum.class_extractor --kps kps.json        # 步骤3: 类型推断
python -m edukg.core.curriculum.concept_extractor --kps kps.json      # 步骤4: 生成 Concept
python -m edukg.core.curriculum.statement_extractor --concepts c.json # 步骤5: 生成定义
python -m edukg.core.curriculum.relation_extractor --stmts s.json     # 步骤6: 提取关系
```

---

## 流程概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        输入: 课标 PDF                                │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  步骤1: PDF OCR (pdf_ocr.py)                                         │
│  ─────────────────────────────────────────────────────────────────  │
│  服务: BaiduOCRService                                               │
│  技术: 百度 OCR API（收费）                                           │
│  输出: ocr_result.json                                               │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  步骤2: 知识点提取 (kp_extraction.py)                                │
│  ─────────────────────────────────────────────────────────────────  │
│  服务: LLMExtractor                                                  │
│  技术: 智谱 glm-4-flash（免费）                                       │
│  功能: 从 OCR 文本提取结构化知识点                                     │
│  输出: curriculum_kps.json                                           │
│    └─ 学段 → 领域 → 知识点列表                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  步骤3: Class 类型推断 (class_extractor.py)                          │
│  ─────────────────────────────────────────────────────────────────  │
│  服务: ClassExtractor                                                │
│  技术: 智谱 glm-4-flash                                              │
│  功能: LLM 判断知识点属于哪个概念类                                    │
│  现有: 38 个 Class（数学概念、数学方法、数学定义...）                  │
│  输出: classes.json                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  步骤4: Concept 生成 (concept_extractor.py)                          │
│  ─────────────────────────────────────────────────────────────────  │
│  服务: ConceptExtractor                                              │
│  技术: pypinyin + hashlib（无 LLM）                                  │
│  功能: 生成知识点实体 URI，添加 HAS_TYPE 关系                         │
│  输出: concepts.json                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  步骤5: Statement 生成 (statement_extractor.py)                      │
│  ─────────────────────────────────────────────────────────────────  │
│  服务: StatementExtractor                                            │
│  技术: 智谱 glm-4-flash                                              │
│  功能: LLM 为每个知识点生成定义描述                                    │
│  输出: statements.json                                               │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  步骤6: Relation 提取 (relation_extractor.py)                        │
│  ─────────────────────────────────────────────────────────────────  │
│  服务: RelationExtractor                                             │
│  技术: 规则匹配 + 智谱 glm-4-flash                                    │
│  关系类型:                                                           │
│    - RELATED_TO: Statement → Concept（规则匹配）                     │
│    - PART_OF: Concept → Concept（LLM 分析，部分-整体）               │
│    - BELONGS_TO: Concept → Concept（LLM 分析，所属关系）             │
│  输出: relations.json                                                │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  输出: 4 个 JSON 文件（符合 Neo4j 导入格式）                          │
│    - classes.json                                                   │
│    - concepts.json                                                  │
│    - statements.json                                                │
│    - relations.json                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 数据流详解：从课标到知识点列表

### 原始数据来源

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        原始数据: 课标 PDF                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│  文件: 义务教育数学课程标准（2022年版）.pdf                                  │
│  页数: 189 页                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                              百度 OCR 识别
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ocr_result.json (OCR 识别结果)                           │
│  ─────────────────────────────────────────────────────────────────────────  │
│  {                                                                          │
│    "total_pages": 189,                                                      │
│    "pages": [                                                               │
│      {                                                                      │
│        "page_num": 19,                                                      │
│        "text": "1.第一学段(1~2年级)\n经历简单的数的抽象过程..."               │
│      },                                                                     │
│      {                                                                      │
│        "page_num": 25,                                                      │
│        "text": "第一学段（1~2年级)\n【内容要求】\n1.数与运算..."              │
│      }                                                                      │
│    ]                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 课标原文结构示例（第25页）

```
第一学段（1~2年级)

【内容要求】
1.数与运算
  (1)在实际情境中感悟并理解万以内数的意义...
  (2)了解符号<，=，>的含义，会比较万以内数的大小...
  (3)在具体情境中，了解四则运算的意义...
  (4)探索加法和减法的算理与算法，会整数加减法。
  (5)探索乘法和除法的算理与算法，会简单的整数乘除法。

2.数量关系
  ...
```

### LLM 提取过程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LLM Prompt (kp_extraction.py)                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  你是一个教育专家，专门从课程标准中提取知识点。                               │
│                                                                             │
│  请从以下课标文本中提取所有知识点，按照学段和领域进行组织。                   │
│                                                                             │
│  输出格式要求（JSON）：                                                     │
│  {                                                                          │
│    "stages": [                                                              │
│      {                                                                      │
│        "stage": "第一学段",      ← 从原文提取                               │
│        "grades": "1-2年级",      ← 从原文提取                               │
│        "domains": [                                                         │
│          {                                                                  │
│            "domain": "数与代数", ← 从原文提取                               │
│            "knowledge_points": ["20以内数的认识", "加减法", ...]            │
│          }                                                                  │
│        ]                                                                    │
│      }                                                                      │
│    ]                                                                        │
│  }                                                                          │
│                                                                             │
│  注意事项：                                                                 │
│  1. 学段包括：第一学段(1-2年级)、第二学段(3-4年级)...                       │
│  2. 领域包括：数与代数、图形与几何、统计与概率、综合与实践                   │
│  3. 知识点要具体、准确，使用课标中的原话                                     │
│                                                                             │
│  课标文本：                                                                 │
│  {OCR识别的原文}                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                              LLM 处理 (glm-4-flash)
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                   curriculum_kps.json (LLM 输出)                            │
│  ─────────────────────────────────────────────────────────────────────────  │
│  {                                                                          │
│    "stages": [                                                              │
│      {                                                                      │
│        "stage": "第一学段",                                                 │
│        "grades": "1-2年级",                                                 │
│        "domains": [                                                         │
│          {                                                                  │
│            "domain": "数与代数",                                            │
│            "knowledge_points": [                                            │
│              "万以内数的认识",                                              │
│              "数的大小比较",                                                │
│              "四则运算的意义",                                              │
│              "整数加减法",                                                  │
│              "整数乘除法"                                                   │
│            ]                                                                │
│          }                                                                  │
│        ]                                                                    │
│      },                                                                     │
│      { "stage": "第二学段", ... },                                          │
│      { "stage": "第三学段", ... },                                          │
│      { "stage": "第四学段", ... }                                           │
│    ]                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 为什么有 stage/domain 结构？

| 字段 | 来源 | 说明 |
|------|------|------|
| **stage（学段）** | 课标原文章节结构 | 第一学段(1-2年级)、第二学段(3-4年级)、第三学段(5-6年级)、第四学段(7-9年级) |
| **domain（领域）** | 课标原文分类 | 数与代数、图形与几何、统计与概率、综合与实践 |
| **knowledge_points** | LLM 从原文提取 | 具体的知识点名称 |

### 数据流总结

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   课标 PDF    │ ──▶ │  百度 OCR    │ ──▶ │  LLM 提取    │ ──▶ │ curriculum_  │
│  (189页)      │     │ ocr_result   │     │ glm-4-flash  │     │ kps.json     │
│              │     │   .json      │     │              │     │              │
│ 原始文档      │     │ 原始文本      │     │ 结构化提取    │     │ 知识点列表   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
                                         按 stage/domain
                                         组织知识点
```

**LLM 的作用**：理解课标原文结构，提取知识点名称，按学段/领域组织成 JSON。

---

## 模块说明

| 文件 | 类 | 功能 | LLM | 输入 | 输出 |
|------|-----|------|-----|------|------|
| `pdf_ocr.py` | `BaiduOCRService` | PDF OCR 识别 | ❌ | PDF 文件 | ocr_result.json |
| `kp_extraction.py` | `LLMExtractor` | 提取知识点 | ✅ | OCR JSON | curriculum_kps.json |
| `class_extractor.py` | `ClassExtractor` | 类型推断 | ✅ | 知识点列表 | classes.json |
| `concept_extractor.py` | `ConceptExtractor` | 生成 Concept | ❌ | 知识点+类型 | concepts.json |
| `statement_extractor.py` | `StatementExtractor` | 生成定义 | ✅ | Concepts | statements.json |
| `relation_extractor.py` | `RelationExtractor` | 提取关系 | ✅ | Statements+Concepts | relations.json |
| `kg_builder.py` | `KGBuilder`, `URIGenerator` | 基础设施 | ❌ | - | - |
| `kg_main.py` | `build_knowledge_graph()` | 主流程 | ✅ | OCR JSON | 4个JSON |
| `kp_comparison.py` | `ConceptComparator` | 对比分析 | ❌ | 知识点列表 | 对比报告 |
| `ttl_generator.py` | `TTLGenerator` | TTL 生成 | ❌ | 知识点列表 | .ttl 文件 |
| `config.py` | `Settings` | 配置管理 | ❌ | - | - |

---

## 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           config.py                                      │
│                        (配置: API Keys)                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│ kp_extraction │           │ kg_builder.py │           │               │
│     .py       │           │ (URI生成器)    │           │               │
│               │           │               │           │               │
│ LLMExtractor  │           │ URIGenerator  │           │               │
└───────────────┘           │ KGConfig      │           │               │
                            └───────┬───────┘           │
                                    │                   │
        ┌───────────────────────────┼───────────────────┘
        │                           │
        │     ┌─────────────────────┼─────────────────────┐
        │     │                     │                     │
        ▼     ▼                     ▼                     ▼
┌───────────────┐           ┌───────────────┐     ┌───────────────┐
│class_extractor│           │concept_       │     │statement_     │
│     .py       │           │extractor.py   │     │extractor.py   │
│               │           │               │     │               │
│ClassExtractor │           │ConceptExtractor│    │StatementExtractor│
└───────────────┘           └───────────────┘     └───────────────┘
        │                           │                     │
        │                           │                     │
        └───────────────────────────┼─────────────────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │relation_      │
                            │extractor.py   │
                            │               │
                            │RelationExtractor│
                            └───────────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │  kg_main.py   │
                            │               │
                            │ 整合所有模块   │
                            │build_knowledge│
                            │_graph()       │
                            └───────────────┘
```

### 依赖关系表

| 文件 | 依赖模块 | 说明 |
|------|---------|------|
| `config.py` | 无 | 基础配置 |
| `kg_builder.py` | `config` | URI生成基础设施 |
| `kp_extraction.py` | `config` | **独立**，只从OCR提取知识点列表 |
| `class_extractor.py` | `config`, `kg_builder` | 使用URIGenerator |
| `concept_extractor.py` | `kg_builder` | 使用URIGenerator |
| `statement_extractor.py` | `config`, `kg_builder` | 使用URIGenerator |
| `relation_extractor.py` | `config`, `kg_builder` | 使用URIGenerator |
| `kg_main.py` | **所有模块** | 整合流程 |

### 元素与关系映射

| 文件 | 处理元素 | 处理关系 | 判断方式 |
|------|---------|---------|---------|
| `class_extractor.py` | **Class** | SUB_CLASS_OF | 规则映射（`parents`字段） |
| `concept_extractor.py` | **Concept** | HAS_TYPE | LLM推断后存入（`types`字段） |
| `statement_extractor.py` | **Statement** | - | - |
| `relation_extractor.py` | **Relation** | RELATED_TO, PART_OF, BELONGS_TO | 规则匹配 + LLM分析 |

> 详细映射关系见 [MAPPING.md](./MAPPING.md)

---

## URI 命名规范

```
URI 格式: http://edukg.org/knowledge/{version}/{type}/math#{id}

┌─────────────────────────────────────────────────────────────────┐
│ version: 0.2 (区分 EduKG 的 0.1)                                │
│ type: class | instance | statement                              │
│ id: {pinyin}-{md5}                                              │
│                                                                  │
│ 生成方式:                                                        │
│   pinyin = "".join(pypinyin.lazy_pinyin(label))                 │
│   md5 = hashlib.md5(label.encode("utf-8")).hexdigest()          │
└─────────────────────────────────────────────────────────────────┘

示例:
  知识点: "凑十法"
  pinyin: "coushifa"
  md5: "8ecd7cb3e9b575bbd7c2009542d8edf8"
  URI: "http://edukg.org/knowledge/0.2/instance/math#coushifa-8ecd7cb3..."
```

---

## 关系判断方法

### 1. RELATED_TO（规则匹配，无需 LLM）

```python
# Statement 标签格式: "{概念}的定义"
statement_label = "凑十法的定义"
concept_label = statement_label[:-3]  # 去掉"的定义" → "凑十法"

# 自动生成关系
relation = {
    "from": {"uri": statement_uri, "label": statement_label},
    "relation": "relatedTo",
    "to": {"uri": concept_uri, "label": concept_label}
}
```

### 2. PART_OF / BELONGS_TO（LLM 分析）

```python
# Prompt 示例
"""
知识点列表: 凑十法, 进位加法, 20以内加法, 加法

请分析这些知识点之间的关系:
1. partOf: 部分与整体（如"20以内加法" → "加法"）
2. belongsTo: 所属关系（如"凑十法" → "进位加法"）

输出 JSON:
{
  "relations": [
    {"from": "凑十法", "relation": "belongsTo", "to": "进位加法", "confidence": 0.85}
  ]
}
"""
```

---

## 输出文件格式

### classes.json
```json
{
  "subject": "math",
  "subject_name": "数学",
  "class_count": 1,
  "classes": [
    {
      "uri": "http://edukg.org/knowledge/0.2/class/math#xiaoxueshugainian-xxx",
      "id": "xiaoxueshugainian-xxx",
      "subject": "math",
      "label": "小学数概念",
      "description": "小学数概念",
      "parents": ["http://edukg.org/knowledge/0.1/class/math#shuxuegainian-xxx"],
      "type": "owl:Class"
    }
  ]
}
```

### concepts.json
```json
[
  {
    "uri": "http://edukg.org/knowledge/0.2/instance/math#coushifa-xxx",
    "label": "凑十法",
    "types": ["shuxuefangfa-xxx"]
  }
]
```

### statements.json
```json
[
  {
    "uri": "http://edukg.org/knowledge/0.2/statement/math#coushifadedingyi-xxx",
    "label": "凑十法的定义",
    "types": ["shuxuedingyi-xxx"],
    "content": "凑十法是一种计算方法，将一个数拆分成10和另一部分..."
  }
]
```

### relations.json
```json
{
  "metadata": {
    "total_relations": 100,
    "description": "数学知识点关联关系"
  },
  "relations": [
    {
      "from": {"uri": "statement#xxx", "label": "凑十法的定义"},
      "relation": "relatedTo",
      "to": {"uri": "instance#xxx", "label": "凑十法"}
    },
    {
      "from": {"uri": "instance#xxx", "label": "凑十法"},
      "relation": "belongsTo",
      "to": {"uri": "instance#yyy", "label": "进位加法"}
    }
  ]
}
```

---

## 配置

环境变量（在 `ai-edu-ai-service/.env` 中配置）:

| 变量 | 必填 | 说明 |
|------|------|------|
| `NEO4J_URI` | 是 | Neo4j 连接地址 |
| `NEO4J_USER` | 是 | Neo4j 用户名 |
| `NEO4J_PASSWORD` | 是 | Neo4j 密码 |
| `BAIDU_OCR_API_KEY` | 是 | 百度 OCR API Key（收费） |
| `BAIDU_OCR_SECRET_KEY` | 是 | 百度 OCR Secret Key（收费） |
| `ZHIPU_API_KEY` | 是 | 智谱 API Key（glm-4-flash 免费） |

---

## 依赖

```bash
pip install langchain-community pypinyin httpx fitz  # PyMuPDF
```

---

## 测试

```bash
# 运行所有测试
pytest edukg/tests/curriculum/ -v

# 运行单个测试
pytest edukg/tests/curriculum/test_kg_builder.py -v
```

---

## 导入 Neo4j

生成 JSON 文件后，使用导入脚本：

```bash
python edukg/scripts/kg_data/import_kg.py \
  --classes edukg/data/eduBureau/math/classes.json \
  --concepts edukg/data/eduBureau/math/concepts.json \
  --statements edukg/data/eduBureau/math/statements.json \
  --relations edukg/data/eduBureau/math/relations.json
```