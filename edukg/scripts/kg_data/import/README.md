# Neo4j 数据导入脚本

> 将处理后的 JSON 数据批量导入 Neo4j 知识图谱

---

## 导入顺序

数据之间存在依赖关系，**必须按以下顺序导入**：

```bash
# === 第一部分：EduKG 基础图谱 ===
1. import_math_classes.py          → 概念类（Class 节点 + SUB_CLASS_OF 关系）
2. import_math_concepts.py         → 知识点实体（Concept 节点 + HAS_TYPE 关系）
3. import_math_statements.py       → 定义/定理（Statement 节点 + RELATED_TO 关系）
4. import_math_relations.py        → 知识点关联（RELATED_TO 关系）
5. import_partof_belongsto.py      → 部分-整体/所属关系（PART_OF + BELONGS_TO）

# === 第二部分：人教版教材数据 ===
6. import_textbooks.py             → 教材节点（Textbook）
7. import_chapters.py              → 章节节点 + 目录关系（Chapter + CONTAINS）
8. import_sections.py              → 小节节点 + 目录关系（Section + CONTAINS）
9. import_textbook_kps.py          → 教材知识点（TextbookKP）
10. import_in_unit_relations.py    → 知识点归属关系（IN_UNIT）
11. import_matches_kg.py           → 知识点匹配关系（MATCHES_KG）
```

---

## 脚本详解

### 1. import_math_classes.py

| 项目 | 说明 |
|------|------|
| **数据源** | `1_概念类(Class)/math_classes.json` |
| **导入内容** | Class 节点（38 个） |
| **创建关系** | SUB_CLASS_OF（概念类层级） |
| **约束** | `Class.uri` 唯一, `Class.id` 唯一 |

### 2. import_math_concepts.py

| 项目 | 说明 |
|------|------|
| **数据源** | `2_知识点实体(complete)/math_complete_statement.json` |
| **导入内容** | Concept 节点（1,295 个） |
| **创建关系** | HAS_TYPE（Concept → Class） |
| **约束** | `Concept.uri` 唯一 |

### 3. import_math_statements.py

| 项目 | 说明 |
|------|------|
| **数据源** | `3_定义_定理(Statement)/math_statement.json` |
| **导入内容** | Statement 节点（2,932 个） |
| **创建关系** | RELATED_TO（Statement → Concept/Class） |

### 4. import_math_relations.py

| 项目 | 说明 |
|------|------|
| **数据源** | `4_知识点关联关系(Relation)/math_knowledge_relations.json` |
| **导入内容** | RELATED_TO 关系（9,871 个） |

### 5. import_partof_belongsto.py

| 项目 | 说明 |
|------|------|
| **数据源** | `2_知识点实体(complete)/知识点实例_类型标签/math_instance.ttl` |
| **导入内容** | PART_OF 关系（298 个）+ BELONGS_TO 关系（619 个） |

---

### 6. import_textbooks.py

| 项目 | 说明 |
|------|------|
| **数据源** | `5_教材目录(Textbook)/output/textbooks.json` |
| **导入内容** | Textbook 节点（21 册，小学 12 + 初中 6 + 高中 3） |
| **属性** | uri, id, label, stage, grade, semester, publisher, edition |
| **约束** | `Textbook.uri` 唯一, `Textbook.id` 唯一 |

### 7. import_chapters.py

| 项目 | 说明 |
|------|------|
| **数据源** | `5_教材目录(Textbook)/output/chapters_enhanced.json` |
| **导入内容** | Chapter 节点（135 个）+ CONTAINS 关系（Textbook → Chapter） |
| **属性** | uri, id, label, order, textbook_id, topic |
| **约束** | `Chapter.uri` 唯一, `Chapter.id` 唯一 |

### 8. import_sections.py

| 项目 | 说明 |
|------|------|
| **数据源** | `5_教材目录(Textbook)/output/sections.json` |
| **导入内容** | Section 节点（549 个）+ CONTAINS 关系（Chapter → Section） |
| **属性** | uri, id, label, order, chapter_id, mark |
| **约束** | `Section.uri` 唯一, `Section.id` 唯一 |

### 9. import_textbook_kps.py

| 项目 | 说明 |
|------|------|
| **数据源** | `5_教材目录(Textbook)/output/textbook_kps.json` |
| **导入内容** | TextbookKP 节点（1,350 个） |
| **属性** | uri, label, stage, grade, section_id, textbook_id, difficulty, importance, cognitive_level, topic |
| **约束** | `TextbookKP.uri` 唯一 |

### 10. import_in_unit_relations.py

| 项目 | 说明 |
|------|------|
| **数据源** | `5_教材目录(Textbook)/output/in_unit_relations.json` |
| **导入内容** | IN_UNIT 关系（1,350 个，TextbookKP → Section/Chapter） |
| **语义** | 知识点所属的教学章节 |

### 11. import_matches_kg.py

| 项目 | 说明 |
|------|------|
| **数据源** | `5_教材目录(Textbook)/output/matches_kg_relations.json` |
| **导入内容** | MATCHES_KG 关系（1,042 个，仅已匹配的记录） |
| **关系属性** | confidence（匹配置信度）, method（匹配方法） |
| **跳过** | 308 条未匹配记录（后续通过人工审核补充） |

---

## 使用方法

每个脚本支持相同的参数：

```bash
# 正常导入
python import/import_textbooks.py

# 预览模式（仅打印 Cypher，不执行）
python import/import_textbooks.py --dry-run

# 清除已有数据后重新导入
python import/import_textbooks.py --clear

# 仅查看统计信息
python import/import_textbooks.py --stats

# 指定数据文件路径
python import/import_textbooks.py --file /path/to/custom/file.json
```

## 重复导入

所有脚本使用 `MERGE` 语句，**支持安全重复导入**：

- 节点已存在 → 更新属性，不创建新节点
- 关系已存在 → 跳过，不创建新关系

## 导入结果概览

```
┌─────────────────────────────────────────────┐
│         Neo4j 数学知识图谱（导入后）           │
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
