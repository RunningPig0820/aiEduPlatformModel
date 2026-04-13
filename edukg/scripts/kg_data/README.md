# EduKG 知识图谱数据处理脚本

> 数学知识图谱数据下载、处理与导入脚本

---

## 目录结构

```
kg_data/
├── import/          # Neo4j 导入脚本 (11)
│   ├── import_math_classes.py          # 导入概念类
│   ├── import_math_concepts.py         # 导入知识点实体
│   ├── import_math_statements.py       # 导入定义/定理内容
│   ├── import_math_relations.py        # 导入关联关系
│   ├── import_partof_belongsto.py      # 导入 partOf/belongsTo 关系
│   ├── import_textbooks.py             # 导入教材节点 (21)
│   ├── import_chapters.py              # 导入章节节点 + CONTAINS (135)
│   ├── import_sections.py              # 导入小节节点 + CONTAINS (549)
│   ├── import_textbook_kps.py          # 导入教材知识点 (1,350)
│   ├── import_in_unit_relations.py     # 导入 IN_UNIT 关系 (1,350)
│   └── import_matches_kg.py            # 导入 MATCHES_KG 关系 (1,042)
│
├── textbook/        # 教材处理脚本 (10)
│   ├── generate_textbook_data.py       # 生成教材节点数据
│   ├── clean_textbook_data.py          # 清洗教材数据
│   ├── enhance_chapters.py             # 增强章节 Topic
│   ├── enhance_kp_attributes.py        # 推断知识点属性
│   ├── infer_textbook_kp.py            # LLM 推断缺失知识点
│   ├── merge_inferred_kps.py           # 合并推断结果
│   ├── enhance_inferred_kps.py         # 增强推断知识点属性
│   ├── normalize_textbook_kp.py        # 标准化知识点名称
│   ├── build_vector_index.py           # 构建向量索引
│   └── match_textbook_kp.py            # 匹配教材知识点到图谱
│
├── download/        # 数据下载脚本 (8)
│   ├── download_all_concept.py
│   ├── download_all_subjects.py
│   ├── download_complete_edukg.py
│   ├── download_complete_math.py
│   ├── download_edukb_relations.py
│   ├── download_edukg_data.py
│   ├── download_extended_data.py
│   └── download_subject_meta.py
│
├── verify/          # 验证/统计脚本 (6)
│   ├── verify_import.py
│   ├── verify_relations.py
│   ├── validate_edukg_data.py
│   ├── validate_kg_data.py
│   ├── query_class_stats.py
│   └── analyze_textbook_matching.py
│
├── explore/         # 探索/调试脚本 (4)
│   ├── explore_edukg_relations.py
│   ├── explore_edukg_relations2.py
│   ├── check_compatibility.py
│   └── check_relations.py
│
├── tools/           # 工具脚本 (3)
│   ├── clear_neo4j.py
│   ├── fix_entity_labels.py
│   └── reimport_kg.py
│
└── README.md
```

---

## 快速开始：从零搭建数学知识图谱

### 前置条件

1. Neo4j 服务已启动
2. `ai-edu-ai-service/.env` 中配置了 Neo4j 连接信息
3. 已安装依赖：`pip install neo4j`

### 导入顺序

```bash
cd edukg/scripts/kg_data/

# 第一步：导入 EduKG 基础图谱
python import/import_math_classes.py
python import/import_math_concepts.py
python import/import_math_statements.py
python import/import_math_relations.py
python import/import_partof_belongsto.py

# 第二步：导入教材数据
python import/import_textbooks.py
python import/import_chapters.py
python import/import_sections.py
python import/import_textbook_kps.py
python import/import_in_unit_relations.py
python import/import_matches_kg.py
```

每个脚本支持：
- `--dry-run` — 预览 Cypher，不执行
- `--clear` — 清除已有数据
- `--stats` — 查看统计信息
- `--file PATH` — 指定数据文件路径

---

## 导入脚本详解

### 1. import/import_math_classes.py

**用途**: 导入数学概念类（本体分类）

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `1_概念类(Class)/math_classes.json` | Class 节点 | 38 个 |
| | SUB_CLASS_OF 关系 | 37 个 |

**使用方法**:
```bash
python import/import_math_classes.py              # 导入
python import/import_math_classes.py --dry-run    # 仅打印语句
python import/import_math_classes.py --clear      # 清除后重新导入
python import/import_math_classes.py --stats      # 显示统计
```

---

### 2. import/import_math_concepts.py

**用途**: 导入知识点实体

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `2_知识点实体(complete)/math_complete_statement.json` | Entity 节点 | 4,085 个 |
| | HAS_TYPE 关系 | 5,469 个 |

---

### 3. import/import_math_relations.py

**用途**: 导入知识点关联关系

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `4_知识点关联关系(Relation)/math_knowledge_relations.json` | RELATED_TO 关系 | 9,871 个 |

---

### 4. import/import_partof_belongsto.py

**用途**: 导入部分-整体和所属关系

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `2_知识点实体(complete)/知识点实例_类型标签/math_instance.ttl` | PART_OF 关系 | 298 个 |
| | BELONGS_TO 关系 | 619 个 |

---

### 5. import/import_textbooks.py

**用途**: 导入教材节点

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `5_教材目录(Textbook)/output/textbooks.json` | Textbook 节点 | 21 个 |

---

### 6. import/import_chapters.py

**用途**: 导入章节节点 + CONTAINS 关系（Textbook → Chapter）

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `5_教材目录(Textbook)/output/chapters_enhanced.json` | Chapter 节点 | 135 个 |
| | CONTAINS 关系 | 135 个 |

---

### 7. import/import_sections.py

**用途**: 导入小节节点 + CONTAINS 关系（Chapter → Section）

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `5_教材目录(Textbook)/output/sections.json` | Section 节点 | 549 个 |
| | CONTAINS 关系 | 549 个 |

---

### 8. import/import_textbook_kps.py

**用途**: 导入教材知识点节点

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `5_教材目录(Textbook)/output/textbook_kps.json` | TextbookKP 节点 | 1,350 个 |

---

### 9. import/import_in_unit_relations.py

**用途**: 导入知识点归属关系

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `5_教材目录(Textbook)/output/in_unit_relations.json` | IN_UNIT 关系 | 1,350 个 |

---

### 10. import/import_matches_kg.py

**用途**: 导入知识点匹配关系

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `5_教材目录(Textbook)/output/matches_kg_relations.json` | MATCHES_KG 关系 | 1,042 个（仅已匹配） |

---

## 重复导入处理

所有脚本使用 `MERGE` 语句，支持重复导入：

- **节点**: 重复导入 → 更新属性，不创建新节点
- **关系**: 重复导入 → 跳过，不创建新关系

---

## 数据文件对应关系

| 数据文件 | 用途 | 脚本 |
|----------|------|------|
| `1_概念类(Class)/math_classes.json` | 概念类定义 | `import/import_math_classes.py` |
| `2_知识点实体(complete)/math_complete_statement.json` | 知识点实体 | `import/import_math_concepts.py` |
| `4_知识点关联关系(Relation)/math_knowledge_relations.json` | 关联关系 | `import/import_math_relations.py` |
| `2_知识点实体(complete)/知识点实例_类型标签/math_instance.ttl` | partOf/belongsTo | `import/import_partof_belongsto.py` |
| `3_定义_定理(Statement)/math_statement.json` | 定义内容 | `import/import_math_statements.py` |
| `5_教材目录(Textbook)/output/textbooks.json` | 教材节点 | `import/import_textbooks.py` |
| `5_教材目录(Textbook)/output/chapters_enhanced.json` | 章节节点 | `import/import_chapters.py` |
| `5_教材目录(Textbook)/output/sections.json` | 小节节点 | `import/import_sections.py` |
| `5_教材目录(Textbook)/output/textbook_kps.json` | 教材知识点 | `import/import_textbook_kps.py` |
| `5_教材目录(Textbook)/output/in_unit_relations.json` | 归属关系 | `import/import_in_unit_relations.py` |
| `5_教材目录(Textbook)/output/matches_kg_relations.json` | 匹配关系 | `import/import_matches_kg.py` |

---

## 导入结果

导入完成后 Neo4j 中的数据：

```
┌─────────────────────────────────────────────┐
│           Neo4j 数学知识图谱                  │
├─────────────────────────────────────────────┤
│ 节点                                         │
│   Class:              38                    │
│   Concept:         1,295                    │
│   Statement:       2,932                    │
│   Textbook:           21                    │
│   Chapter:           135                    │
│   Section:           549                    │
│   TextbookKP:      1,350                    │
│                                              │
│ 关系                                         │
│   SUB_CLASS_OF:       38                    │
│   HAS_TYPE:        ~5,600                    │
│   RELATED_TO:      9,871                    │
│   PART_OF:           298                    │
│   BELONGS_TO:        619                    │
│   CONTAINS:          684 (135+549)          │
│   IN_UNIT:         1,350                    │
│   MATCHES_KG:      1,042                    │
└─────────────────────────────────────────────┘
```

---

## Neo4j 验证查询

```cypher
-- 查看概念类层级
MATCH (c:Class)-[:SUB_CLASS_OF]->(parent:Class)
RETURN c.label AS 子概念, parent.label AS 父概念
ORDER BY parent.label, c.label

-- 查看实体类型分布
MATCH (e:Entity)-[:HAS_TYPE]->(c:Class)
RETURN c.label AS 类型, count(e) AS 实体数
ORDER BY 实体数 DESC

-- 查看教材知识点分布
MATCH (k:TextbookKP)
RETURN k.stage AS 学段, k.grade AS 年级, count(k) AS 数量
ORDER BY 学段, 年级

-- 查看匹配到 EduKG 的知识点
MATCH (kp:TextbookKP)-[r:MATCHES_KG]->(c:Concept)
WHERE r.confidence >= 0.8
RETURN kp.label AS 教材知识点, c.label AS 图谱知识点, r.confidence AS 置信度
LIMIT 10

-- 查看未匹配的知识点
MATCH (kp:TextbookKP)
WHERE NOT (kp)-[:MATCHES_KG]->()
RETURN kp.label, kp.stage
```

---

## 前置要求

### 1. Neo4j 服务启动

```bash
# Docker 方式
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# 本地安装
brew services start neo4j
```

### 2. 配置连接信息

在 `ai-edu-ai-service/.env` 中配置：

```env
NEO4J_URI=bolt://your_host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 3. 安装依赖

```bash
pip install neo4j
```

---

## 教材知识点匹配

### match_textbook_kp.py

**用途**: 匹配教材知识点到图谱知识点，生成 MATCHES_KG 关系

**路径**: `textbook/match_textbook_kp.py`

#### 调用流程

```
match_textbook_kp.py
    │
    ├─ 加载教材知识点 (textbook_kps.json)
    │
    ├─ 从 Neo4j 加载图谱 Concept
    │   └── Neo4jClient → MATCH (c:Concept)
    │
    ├─ KPMatcher.match_all()
    │   │
    │   ├─ 加载标准化结果 (normalized_kps_complete.json)
    │   │   └── get_best_match("1-5的认识") → "自然数"
    │   │
    │   ├─ 向量检索（使用 best_match）
    │   │   └── bge-small-zh-v1.5 → top-20 候选
    │   │
    │   ├─ LLM 双模型投票
    │   │   ├── GLM-4-flash（主模型）
    │   │   └── DeepSeek（辅模型）
    │   │   └── 缓存检查 → llm_cache/
    │   │
    │   └─ 输出结果 → matches_kg_relations.json
    │
    └─ 保存进度 → progress/match_kg.json
```

#### 使用方法

```bash
cd textbook/

# 运行匹配（默认使用向量检索 + 断点续传）
python match_textbook_kp.py

# 仅估算成本（不调用 LLM）
python match_textbook_kp.py --dry-run

# 显示已有结果统计
python match_textbook_kp.py --stats
```

#### 输出结果

| 项目 | 数量 | 说明 |
|------|------|------|
| 教材知识点总数 | 1,350 | 小学数学 |
| 已匹配 | 1,042 | 精确匹配 + LLM 语义匹配 |
| 未匹配 | 308 | 需人工审核/图谱补充 |
| 匹配率 | **77.2%** | |

---

## 下一步

1. ✅ ~~导入知识点实体~~
2. ✅ ~~导入关联关系~~
3. ✅ ~~导入定义/定理内容~~
4. ✅ ~~导入 partOf/belongsTo 关系~~
5. ✅ ~~教材知识点标准化~~
6. ✅ ~~教材知识点匹配~~
7. **导入人教版教材数据到 Neo4j** → `import/` 下 6 个脚本
8. 构建 prerequisite 先修关系
9. 未匹配知识点人工审核 (308) → kp-match-review-system
