# 课标知识点提取模块

从课标 PDF 构建 Neo4j 知识图谱的完整流程。

---

## 设计思路

### 核心问题：教学知识点 vs 核心概念

课标中的知识点如"100以内数的认识"，不是纯粹的数学概念，而是：
- **核心概念**："数" - 数学概念本身
- **教学属性**："100以内"（范围）+ "认识"（教学动作）

**设计方案 C：保留完整信息，区分核心概念和教学属性**

```
教学知识点: "100以内数的认识"
    ↓ 解析
┌─────────────────────────────────────┐
│ 核心概念: "数"                        │
│   → 匹配 Neo4j 已存在的 Concept       │
│   → uri: instance/math#341 (0.1)    │
│                                      │
│ 教学属性:                             │
│   scope: "100以内"                   │
│   action: "认识"                     │
└─────────────────────────────────────┘
```

### URI 版本区分

| 版本 | 来源 | 说明 |
|------|------|------|
| **0.1** | EduKG 已有数据 | 匹配到已存在的概念，直接使用 |
| **0.2** | 我们新增数据 | 新创建的概念，需要推断 Class |

### 数据流向

```
课标 PDF
    ↓ OCR
OCR 文本
    ↓ LLM 提取 + 过滤
教学知识点列表
    ↓ LLM 解析
核心概念 + 教学属性
    ↓ 匹配 Neo4j
已存在(0.1) / 新增(0.2)
    ↓ 推断 Class
完整的 Concept 数据
    ↓ 生成 Statement/Relation
Neo4j 导入文件
```

---

## 流程概览

```
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: PDF OCR                                                     │
│  模块: pdf_ocr.py                                                    │
│  输入: 课标 PDF                                                      │
│  输出: ocr_result.json                                               │
│  说明: 百度 OCR 识别（收费），一次性执行                              │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: 知识点提取 ✅ 已完成                                         │
│  模块: kp_extraction.py                                              │
│  输入: ocr_result.json                                               │
│  输出: curriculum_kps_v2.json                                        │
│  结果: 434 个知识点                                                  │
│                                                                      │
│  【设计思路】                                                         │
│  - 使用 LLM 从 OCR 文本提取结构化知识点                               │
│  - Prompt 中增加过滤规则，排除非核心内容：                            │
│    · 教学活动/主题活动（如"数学游戏分享"）                            │
│    · 教学故事/案例（如"曹冲称象的故事"）                              │
│    · 教学目标描述（如"形成量感、空间观念"）                           │
│    · 开篇话语/前言内容                                                │
│    · 跨学科应用场景（如"体育运动与心率"）                              │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: 教学知识点解析 ✅ 已完成                                     │
│  模块: teaching_kp_parser.py                                         │
│  输入: curriculum_kps_v2.json                                        │
│  输出: teaching_kps_parsed.json                                      │
│                                                                      │
│  【设计思路】                                                         │
│  - 将教学知识点解析为：核心概念 + 教学属性                            │
│  - 示例：                                                            │
│    "100以内数的认识" → 概念"数" + scope"100以内" + action"认识"       │
│    "三角形内角和" → 概念"三角形" + property"内角和"                   │
│    "20以内加法" → 概念"加法" + scope"20以内"                         │
│  - 使用 LLM 进行解析，提取 scope/action/property/method               │
│  - 匹配 Neo4j 已存在的 Concept                                        │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: 概念聚合 ✅ 已完成                                           │
│  模块: concept_aggregator.py                                         │
│  输入: teaching_kps_parsed.json                                      │
│  输出: concepts_v3.json                                              │
│  结果: 122 个概念（102 已存在 + 20 新增）                             │
│                                                                      │
│  【设计思路】                                                         │
│  - 按 URI 聚合核心概念，去重                                          │
│  - 区分已存在(0.1)和新增(0.2)概念                                     │
│  - 过滤非核心数学概念：                                               │
│    · 购物、招聘、营养、水、游戏、故事                                 │
│    · 活动、经验、意识、能力、素养                                     │
│    · 问题提出、问题抽象、图案设计、图案                               │
│  - 关联原始教学知识点，保留学段/领域信息                              │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Class 类型推断 ✅ 已完成                                     │
│  模块: class_inferrer.py                                             │
│  输入: concepts_v3.json (仅需处理新增的 20 个概念)                    │
│  输出: classes_v3.json, concepts_with_class.json                     │
│  结果: 19 个匹配已有 Class，1 个新建 Class（数学符号）                │
│                                                                      │
│  【设计思路】                                                         │
│  - 已有 38 个 Class：数学概念、几何概念、代数概念、统计概念...         │
│  - LLM 推断新增概念属于哪个 Class                                     │
│  - 如果匹配已有 Class，使用 0.1 版本 URI                              │
│  - 如果需要新 Class，使用 0.2 版本 URI，并指定父类                    │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: Statement 生成 ✅ 已完成                                     │
│  模块: statement_extractor.py                                        │
│  输入: concepts_with_class.json                                      │
│  输出: statements.json                                               │
│  结果: 122 个定义                                                    │
│                                                                      │
│  【设计思路】                                                         │
│  - LLM 为每个概念生成定义描述                                         │
│  - Statement 标签格式: "{概念}的定义"                                │
│  - types 固定为"数学定义"                                            │
│  - 添加 subject 属性                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 7: 关系提取 ✅ 已完成                                           │
│  模块: relation_extractor.py                                         │
│  输入: statements.json, concepts_with_class.json, classes_v3.json   │
│  输出: relations.json                                                │
│  结果: 312 个关系                                                    │
│                                                                      │
│  【设计思路】                                                         │
│  - 生成 5 种关系类型：                                               │
│    · relatedTo: Statement → Concept（定义关联）                      │
│    · partOf: Concept → Concept（部分-整体）                          │
│    · belongsTo: Concept → Concept（所属关系）                        │
│    · HAS_TYPE: Concept/Statement → Class（类型分类）                 │
│    · SUB_CLASS_OF: Class → Class（概念层级）                         │
│  - partOf/belongsTo 需要 LLM 推断，支持断点续传                      │
│  - HAS_TYPE/SUB_CLASS_OF 不需要 LLM，直接生成                        │
│  - 自动添加 subject 属性                                             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Step 8: 数据校验 ✅ 已完成                                           │
│  说明: 检查数据一致性和 Neo4j 冲突                                    │
│                                                                      │
│  【校验项】                                                           │
│  - 关系类型是否符合定义: ✅                                           │
│  - 三元组完整性: ✅                                                   │
│  - URI 格式正确性: ✅                                                 │
│  - 自环/重复/双向冲突: 0 ✅                                           │
│  - Neo4j 数据库冲突: 0 ✅                                             │
└─────────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────┐
│  最终输出: 4 个 JSON 文件                                             │
│  - classes_v3.json (概念类)                                          │
│  - concepts_with_class.json (知识点实体)                             │
│  - statements.json (定义描述)                                        │
│  - relations.json (关系)                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 当前执行状态

| 步骤 | 模块 | 状态 | 输出文件 | 结果 |
|------|------|------|----------|------|
| Step 1 | pdf_ocr.py | ✅ 完成 | ocr_result.json | 189 页 |
| Step 2 | kp_extraction.py | ✅ 完成 | curriculum_kps_v2.json | 434 个知识点 |
| Step 3 | teaching_kp_parser.py | ✅ 完成 | teaching_kps_parsed.json | 已解析 |
| Step 4 | concept_aggregator.py | ✅ 完成 | concepts_v3.json | 122 个概念 |
| Step 5 | class_inferrer.py | ✅ 完成 | classes_v3.json | 1 个新 Class |
| Step 6 | statement_extractor.py | ✅ 完成 | statements.json | 122 个定义 |
| Step 7 | relation_extractor.py | ✅ 完成 | relations.json | 312 个关系 |
| Step 8 | 数据校验 | ✅ 完成 | - | 无冲突 |

---

## 文件说明

### 输入文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 课标 PDF | `义务教育数学课程标准（2022年版）.pdf` | 原始课标文档 |
| OCR 结果 | `edukg/data/eduBureau/math/ocr_result.json` | PDF OCR 识别结果 |

### 中间文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 知识点列表 | `edukg/data/eduBureau/math/curriculum_kps_v2.json` | Step 2 输出，434 个知识点 |
| 解析结果 | `edukg/data/eduBureau/math/teaching_kps_parsed.json` | Step 3 输出，核心概念+属性 |
| 概念列表 | `edukg/data/eduBureau/math/concepts_v3.json` | Step 4 输出，122 个概念 |
| 带 Class 的概念 | `edukg/data/eduBureau/math/concepts_with_class.json` | Step 5 输出 |

### 最终输出

| 文件 | 路径 | 说明 |
|------|------|------|
| 概念类 | `edukg/data/eduBureau/math/classes_v3.json` | Step 5 输出，1 个新 Class |
| 知识点实体 | `edukg/data/eduBureau/math/concepts_with_class.json` | Step 5 输出 |
| 定义描述 | `edukg/data/eduBureau/math/statements.json` | Step 6 输出 |
| 关系 | `edukg/data/eduBureau/math/relations.json` | Step 7 输出 |

---

## 数据模型

### 教学知识点解析结果

```json
{
  "original_label": "100以内数的认识",
  "stage": "第一学段",
  "grade": "1-2年级",
  "domain": "数与代数",
  "core_concept": {
    "label": "数",
    "uri": "http://edukg.org/knowledge/0.1/instance/math#341",
    "is_existing": true,
    "types": ["shu-bec758cd6ac15f49e774b8c28ef31a74"]
  },
  "attributes": {
    "scope": "100以内",
    "action": "认识",
    "property": null,
    "method": null
  },
  "match_type": "exact",
  "confidence": 1.0
}
```

### 概念聚合结果

```json
{
  "label": "数",
  "uri": "http://edukg.org/knowledge/0.1/instance/math#341",
  "version": "0.1",
  "is_existing": true,
  "types": ["shu-bec758cd6ac15f49e774b8c28ef31a74"],
  "teaching_kps": ["100以内数的认识", "20以内数的认识", ...],
  "stages": ["第一学段", "第二学段"],
  "domains": ["数与代数"]
}
```

### 新增概念示例（带 Class）

```json
{
  "label": "估算",
  "uri": "http://edukg.org/knowledge/0.2/instance/math#gusuan-xxx",
  "version": "0.2",
  "is_existing": false,
  "inferred_class": "数学方法",
  "inferred_class_uri": "http://edukg.org/knowledge/0.1/class/math#shuxuefangfa-xxx",
  "is_new_class": false
}
```

### Statement 定义示例

```json
{
  "uri": "http://edukg.org/knowledge/0.2/statement/math#sanjiaoxingdedingyi-xxx",
  "label": "三角形的定义",
  "types": ["shuxuedingyi-b14b4ceb4747e9d5cc2534e9dc38faf1"],
  "content": "三角形是由三条线段首尾相连组成的封闭图形。"
}
```

### Relation 关系示例

```json
// Statement → Concept (relatedTo)
{
  "from": {
    "uri": "http://edukg.org/knowledge/0.2/statement/math#sanjiaoxingdedingyi-xxx",
    "label": "三角形的定义"
  },
  "relation": "relatedTo",
  "to": {
    "uri": "http://edukg.org/knowledge/0.1/instance/math#332",
    "label": "三角形"
  }
}

// Concept → Concept (partOf)
{
  "from": {
    "uri": "http://edukg.org/knowledge/0.1/instance/math#332",
    "label": "三角形"
  },
  "relation": "partOf",
  "to": {
    "uri": "http://edukg.org/knowledge/0.1/instance/math#xxx",
    "label": "几何"
  }
}

// Concept → Concept (belongsTo)
{
  "from": {
    "uri": "http://edukg.org/knowledge/0.1/instance/math#xxx",
    "label": "圆"
  },
  "relation": "belongsTo",
  "to": {
    "uri": "http://edukg.org/knowledge/0.1/instance/math#xxx",
    "label": "图形"
  }
}
```

---

## 关键统计

### Step 2: 知识点提取

| 指标 | 数量 |
|------|------|
| 提取知识点 | 434 |
| 按学段分布 | 第一学段 116, 第二学段 119, 第三学段 125, 第四学段 74 |
| 按领域分布 | 数与代数 199, 图形与几何 153, 统计与概率 58, 综合与实践 24 |

### Step 3: 教学知识点解析

| 匹配类型 | 数量 |
|---------|------|
| 精确匹配 | 239 |
| 包含匹配 | 151 |
| 新增概念 | 44 |

### Step 4: 概念聚合

| 指标 | 数量 |
|------|------|
| 教学知识点总数 | 434 |
| 核心概念总数 | 122 |
| 已存在概念 | 102 (使用 0.1 URI) |
| 新增概念 | 20 (使用 0.2 URI) |
| 过滤掉非核心概念 | 15 |

### Step 5: Class 类型推断

| 指标 | 数量 |
|------|------|
| 新增概念 | 20 |
| 匹配已有 Class | 19 |
| 创建新 Class | 1（数学符号） |

### Step 6: Statement 生成

| 指标 | 数量 |
|------|------|
| 概念总数 | 122 |
| 生成定义 | 122 |
| LLM 调用 | 122（已缓存） |

### Step 7: 关系提取

| 指标 | 数量 |
|------|------|
| 总关系数 | 312 |
| Statement → Concept (relatedTo) | 122 |
| Concept → Concept (partOf) | 46 |
| Concept → Concept (belongsTo) | 1 |
| Concept/Statement → Class (HAS_TYPE) | 142 |
| Class → Class (SUB_CLASS_OF) | 1 |

---

## 数据校验

### relations.json 数据校验

在导入 Neo4j 之前，需要对 relations.json 进行以下校验：

#### 1. 关系类型校验

检查所有关系类型是否符合预定义：

| 关系类型 | 起点 | 终点 | 语义 |
|---------|------|------|------|
| relatedTo | Statement | Concept | 定义关联 |
| partOf | Concept | Concept | 部分-整体 |
| belongsTo | Concept | Concept | 所属关系 |
| HAS_TYPE | Concept/Statement | Class | 类型分类 |
| SUB_CLASS_OF | Class | Class | 概念层级 |

#### 2. 三元组完整性校验

每个关系必须包含完整的 `from`、`relation`、`to` 三元组：
- `from.uri`: 实体 URI
- `from.label`: 实体标签
- `relation`: 关系类型
- `to.uri`: 目标 URI
- `to.label`: 目标标签

#### 3. URI 格式校验

所有 URI 必须符合格式：`http://edukg.org/knowledge/{version}/{type}/math#{id}`

| 版本 | 说明 |
|------|------|
| 0.1 | EduKG 已有数据 |
| 0.2 | 新增数据 |

#### 4. 自环关系校验

**规则**：`from.uri` 不能等于 `to.uri`

自环关系会导致数据逻辑错误，必须删除。

#### 5. 重复关系校验

**规则**：相同的 `(from.uri, relation, to.uri)` 三元组只能出现一次

重复关系会导致 Neo4j 导入时创建多余边。

#### 6. 双向冲突校验

**规则**：如果存在 `A -> partOf -> B`，则不能存在 `B -> belongsTo -> A`

双向冲突会导致语义矛盾，需要判断方向是否正确并保留一个。

### Neo4j 数据库冲突校验

#### 1. Concept→Concept 关系冲突

检查生成的 `partOf`/`belongsTo` 关系是否已存在于 Neo4j：

```cypher
MATCH (from:Concept)-[rel]->(to:Concept)
WHERE from.label = $from_label AND to.label = $to_label
RETURN type(rel) as rel_type
```

**处理规则**：
- 如果数据库中已存在相同关系，跳过生成
- 如果数据库中存在不同类型的关系（如 BELONGS_TO vs partOf），删除生成的，保留数据库中已有的

#### 2. HAS_TYPE 关系冲突

检查生成的 Concept/Statement 是否已有 HAS_TYPE 关系：

```cypher
MATCH (from)-[:HAS_TYPE]->(to:Class)
WHERE from.label = $from_label AND to.label = $to_label
RETURN count(*) as count
```

**处理规则**：
- 新增概念(0.2)：需要生成 HAS_TYPE 关系
- 已存在概念(0.1)：Neo4j 中可能已有 HAS_TYPE，需要检查后决定是否新增

#### 3. relatedTo 关系冲突

检查生成的 Statement 是否已有 RELATED_TO 关系：

```cypher
MATCH (from:Statement)-[:RELATED_TO]->(to:Concept)
WHERE from.label = $from_label
RETURN count(*) as count
```

**处理规则**：
- 新生成的 Statement 需要建立 RELATED_TO 关系
- 如果 Statement 已存在于 Neo4j，需要检查是否重复

### 校验脚本

```python
# 完整校验流程
import json
from neo4j import GraphDatabase

def validate_relations(relations_path, neo4j_uri, neo4j_user, neo4j_password):
    """
    校验 relations.json 数据

    Returns:
        dict: 校验结果
    """
    with open(relations_path) as f:
        data = json.load(f)
    relations = data['relations']

    results = {
        'relation_types': True,      # 关系类型符合定义
        'completeness': True,        # 三元组完整
        'uri_format': True,          # URI 格式正确
        'self_loops': 0,             # 自环数量
        'duplicates': 0,             # 重复数量
        'bidirectional_conflicts': 0, # 双向冲突数量
        'db_conflicts': [],          # 数据库冲突
    }

    # 1. 检查自环
    for r in relations:
        if r['from']['uri'] == r['to']['uri']:
            results['self_loops'] += 1

    # 2. 检查重复
    keys = set()
    for r in relations:
        key = (r['from']['uri'], r['relation'], r['to']['uri'])
        if key in keys:
            results['duplicates'] += 1
        keys.add(key)

    # 3. 检查数据库冲突
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    with driver.session() as session:
        for r in relations:
            if r['relation'] in ['partOf', 'belongsTo']:
                result = session.execute_read(lambda tx: tx.run('''
                    MATCH (from:Concept)-[rel]->(to:Concept)
                    WHERE from.label = $from_label AND to.label = $to_label
                    RETURN type(rel) as rel_type
                ''', from_label=r['from']['label'], to_label=r['to']['label']).data())

                if result:
                    results['db_conflicts'].append({
                        'from': r['from']['label'],
                        'to': r['to']['label'],
                        'generated': r['relation'],
                        'existing': result[0]['rel_type']
                    })

    driver.close()
    return results
```

### 校验结果示例

```
=== relations.json 数据校验 ===
关系类型符合定义: ✅
三元组完整性: ✅
URI 格式正确: ✅
自环关系: 0 ✅
重复关系: 0 ✅
双向冲突: 0 ✅

=== Neo4j 数据库冲突校验 ===
Concept→Concept 关系冲突: 0 ✅
HAS_TYPE 新增: 98 个
relatedTo 新增: 78 个
```

---

## 快速开始

### 查看状态

```bash
python -m edukg.core.curriculum.kp_extraction --status
python -m edukg.core.curriculum.class_inferrer --status
```

### 继续执行

```bash
# Step 6: Statement 生成
python -m edukg.core.curriculum.statement_extractor \
  --concepts edukg/data/eduBureau/math/concepts_with_class.json \
  --output edukg/data/eduBureau/math/statements.json \
  --verbose

# Step 7: 关系提取（包含所有 5 种关系类型）
python -m edukg.core.curriculum.relation_extractor \
  --statements edukg/data/eduBureau/math/statements.json \
  --concepts edukg/data/eduBureau/math/concepts_with_class.json \
  --classes edukg/data/eduBureau/math/classes_v3.json \
  --output edukg/data/eduBureau/math/relations.json \
  --verbose
```

---

## 模块说明

| 文件 | 功能 | LLM |
|------|------|-----|
| `pdf_ocr.py` | PDF OCR | ❌ |
| `kp_extraction.py` | Step 2: 知识点提取 + 过滤 | ✅ |
| `teaching_kp_parser.py` | Step 3: 解析核心概念+属性 | ✅ |
| `concept_aggregator.py` | Step 4: 概念聚合+过滤 | ❌ |
| `class_inferrer.py` | Step 5: Class 类型推断 | ✅ |
| `statement_extractor.py` | Step 6: Statement 生成 | ✅ |
| `relation_extractor.py` | Step 7: 关系提取 | ✅ |
| `kg_builder.py` | URI 生成 | ❌ |
| `config.py` | 配置管理 | ❌ |

---

## 目录结构

```
edukg/
├── cache/                              # LLM 缓存
├── state/                              # 任务状态
├── core/
│   ├── curriculum/
│   │   ├── config.py                   # 配置
│   │   ├── kg_builder.py               # URI 生成
│   │   ├── pdf_ocr.py                  # Step 1: OCR
│   │   ├── kp_extraction.py            # Step 2: 知识点提取
│   │   ├── teaching_kp_parser.py       # Step 3: 教学知识点解析
│   │   ├── concept_aggregator.py       # Step 4: 概念聚合
│   │   ├── class_inferrer.py           # Step 5: Class 推断
│   │   ├── statement_extractor.py      # Step 6: Statement 生成
│   │   ├── relation_extractor.py       # Step 7: 关系提取
│   │   └── README.md
│   └── llmTaskLock/
│       ├── llm_cache.py                # LLM 缓存
│       └── state_manager.py            # 任务状态管理
└── data/
    └── eduBureau/math/
        ├── ocr_result.json              # OCR 结果
        ├── curriculum_kps_v2.json       # Step 2: 知识点列表
        ├── teaching_kps_parsed.json     # Step 3: 解析结果
        ├── concepts_v3.json             # Step 4: 概念列表
        ├── classes_v3.json              # Step 5: Class 类型
        ├── concepts_with_class.json     # Step 5: 带 Class 的概念
        ├── statements.json              # Step 6: 定义描述
        └── relations.json               # Step 7: 关系
```

---

## 配置

环境变量（在 `ai-edu-ai-service/.env` 中配置）:

| 变量 | 说明 |
|------|------|
| `NEO4J_URI` | Neo4j 连接地址 |
| `NEO4J_USER` | Neo4j 用户名 |
| `NEO4J_PASSWORD` | Neo4j 密码 |
| `BAIDU_OCR_API_KEY` | 百度 OCR API Key（收费） |
| `BAIDU_OCR_SECRET_KEY` | 百度 OCR Secret Key |
| `ZHIPU_API_KEY` | 智谱 API Key（glm-4-flash 免费） |

---

## 依赖

```bash
pip install langchain-community pypinyin httpx fitz neo4j
```

---

## 导入 Neo4j

```bash
python edukg/scripts/kg_data/import_kg.py \
  --classes edukg/data/eduBureau/math/classes_v3.json \
  --concepts edukg/data/eduBureau/math/concepts_with_class.json \
  --statements edukg/data/eduBureau/math/statements.json \
  --relations edukg/data/eduBureau/math/relations.json
```