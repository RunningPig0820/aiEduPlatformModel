# 数学知识点数据清洗 CLI 文档

> 模块: kg_construction (知识图谱构建脚本)
>
> 更新日期: 2026-03-29

---

## 概述

本 change 不提供 HTTP API 接口，而是提供**命令行脚本**用于数学数据清洗、教材信息提取和 Neo4j 导入。这些脚本供开发人员使用，处理流程为：

```
clean_math_data.py → extract_textbook_info.py → merge_math_data.py → import_math_kp_to_neo4j.py → validate_math_import.py
```

---

## 1. TTL 数据清洗脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/clean_math_data.py` |
| 执行方式 | `python clean_math_data.py [--options]` |
| 依赖 | RDFLib, 环境变量配置 |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | String | 否 | `ttl/math.ttl` | TTL 输入文件路径 |
| `--output` | String | 否 | `output/math_knowledge_points.json` | JSON 输出文件路径 |
| `--verbose` | Flag | 否 | False | 显示详细日志 |

### 执行示例

**正常执行:**
```bash
cd ai-edu-ai-service/scripts/kg_construction
python clean_math_data.py
```

**指定输入输出路径:**
```bash
python clean_math_data.py --input ../ttl/math.ttl --output ../output/math_knowledge_points.json
```

### 输出结果

执行成功时输出：
```
INFO: Parsing TTL file: ttl/math.ttl
INFO: Extracted 4,490 knowledge points
INFO: Removed 15 duplicate entities
INFO: Filtered 23 invalid entities (missing required fields)
INFO: Type coverage: 75.2%
SUCCESS: Output written to output/math_knowledge_points.json
```

### 输出文件结构

`math_knowledge_points.json` 格式：
```json
[
  {
    "uri": "http://edukg.org/knowledge/0.1/instance/math#516",
    "name": "一元二次方程",
    "subject": "math",
    "type": "定义",
    "description": "只含有一个未知数..."
  }
]
```

---

## 2. 教材信息提取脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/extract_textbook_info.py` |
| 执行方式 | `python extract_textbook_info.py [--options]` |
| 依赖 | RDFLib, 数学知识点 JSON |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--kp-input` | String | 否 | `output/math_knowledge_points.json` | 知识点 JSON 输入路径 |
| `--ttl-input` | String | 否 | `ttl/main.ttl` | 教材 TTL 输入路径 |
| `--output` | String | 否 | `output/math_textbook_mapping.json` | 映射 JSON 输出路径 |
| `--verbose` | Flag | 否 | False | 显示详细日志 |

### 执行示例

```bash
python extract_textbook_info.py
```

### 输出结果

执行成功时输出：
```
INFO: Loading knowledge points: 4,490 entities
INFO: Parsing textbook TTL: ttl/main.ttl
INFO: Extracted 12 textbooks
INFO: Extracted 45 chapters
INFO: Matched 3,850 knowledge points (86.1% coverage)
INFO: Unmatched knowledge points marked as "年级未知": 640
SUCCESS: Output written to output/math_textbook_mapping.json
```

---

## 3. 数据合并脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/merge_math_data.py` |
| 执行方式 | `python merge_math_data.py [--options]` |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--kp-input` | String | 否 | `output/math_knowledge_points.json` | 知识点 JSON 输入路径 |
| `--mapping-input` | String | 否 | `output/math_textbook_mapping.json` | 映射 JSON 输入路径 |
| `--output` | String | 否 | `output/math_final_data.json` | 最终数据输出路径 |

### 执行示例

```bash
python merge_math_data.py
```

### 输出结果

执行成功时输出：
```
INFO: Loading knowledge points: 4,490 entities
INFO: Loading textbook mapping: 3,850 records
INFO: Merged 3,850 knowledge points with grade/chapter info
INFO: 640 knowledge points remain without grade info
SUCCESS: Output written to output/math_final_data.json
```

---

## 4. Neo4j 导入脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/import_math_kp_to_neo4j.py` |
| 执行方式 | `python import_math_kp_to_neo4j.py [--options]` |
| 依赖 | Neo4j Python driver, kg-neo4j-schema 已执行 |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | String | 否 | `output/math_final_data.json` | 最终数据输入路径 |
| `--uri` | String | 否 | 从环境变量读取 | Neo4j 连接 URI |
| `--user` | String | 否 | 从环境变量读取 | Neo4j 用户名 |
| `--password` | String | 否 | 从环境变量读取 | Neo4j 密码 |
| `--batch-size` | Integer | 否 | 100 | 批量导入批次大小 |
| `--dry-run` | Flag | 否 | False | 仅打印 Cypher，不执行 |

### 执行示例

```bash
python import_math_kp_to_neo4j.py
```

### 输出结果

执行成功时输出：
```
INFO: Loading final data: 4,490 knowledge points
INFO: Creating hierarchy nodes...
INFO: Created Subject: math
INFO: Created Stage: 高中
INFO: Created Grade: 高一, 高二, 高三
INFO: Created Textbooks: 12
INFO: Created Chapters: 45
INFO: Importing knowledge points in batches (batch_size=100)...
INFO: Imported 100/4490 (2.2%)
INFO: Imported 4490/4490 (100%)
INFO: Creating HAS_KNOWLEDGE_POINT relationships...
INFO: Created 4,490 relationships
SUCCESS: Import completed. Statistics:
  - Subject nodes: 1
  - Stage nodes: 1
  - Grade nodes: 3
  - Textbook nodes: 12
  - Chapter nodes: 45
  - KnowledgePoint nodes: 4,490
  - HAS_KNOWLEDGE_POINT relationships: 4,490
```

---

## 5. 数据验证脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/validate_math_import.py` |
| 执行方式 | `python validate_math_import.py [--options]` |
| 退出码 | 0: 成功, 1: 失败 |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--uri` | String | 否 | 从环境变量读取 | Neo4j 连接 URI |
| `--expected-count` | Integer | 否 | 4490 | 预期知识点数量 |
| `--verbose` | Flag | 否 | False | 显示详细信息 |

### 执行示例

```bash
python validate_math_import.py
```

### 输出结果

**成功时:**
```
VALIDATION REPORT
==================
KnowledgePoint nodes: 4490/4490 ✓
URI uniqueness: 100% ✓
Name not null: 100% ✓
Type coverage: 75.2% ✓

All validations passed.
Exit code: 0
```

**失败时:**
```
VALIDATION REPORT
==================
KnowledgePoint nodes: 4200/4490 ✗ (Missing: 290)
URI uniqueness: 99.5% ✗ (Duplicates found: 22)

Validation failed. Please check import script.
Exit code: 1
```

---

## 6. 完整工作流程

### 执行顺序

```bash
# 1. 清洗 TTL 数据
python clean_math_data.py

# 2. 提取教材信息
python extract_textbook_info.py

# 3. 合并数据
python merge_math_data.py

# 4. 导入 Neo4j
python import_math_kp_to_neo4j.py

# 5. 验证导入
python validate_math_import.py
```

### 人工检查点

在步骤 3 和步骤 4 之间，建议人工检查 `math_final_data.json`：
- 抽查 10-20 条数据
- 确认年级推断是否合理
- 确认类型分类是否准确

---

## 环境变量配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `NEO4J_URI` | Neo4j 连接 URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j 用户名 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 密码 | `your_password` |

---

*文档生成时间: 2026-03-29*