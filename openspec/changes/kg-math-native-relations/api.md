# 数学原生关系处理 CLI 文档

> 模块: kg_construction (知识图谱构建脚本)
>
> 更新日期: 2026-03-29

---

## 概述

本 change 处理数学学科的原生关系数据（relateTo, subCategory），这些关系来自 EduKG TTL 数据，语义与学习依赖（PREREQUISITE）完全不同。

处理流程：
```
extract_native_relations.py → import_native_relations_to_neo4j.py → validate_native_relations.py
```

---

## 1. 原生关系提取脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `edukg/scripts/kg_construction/extract_native_relations.py` |
| 执行方式 | `python extract_native_relations.py [--options]` |
| 依赖 | RDFLib |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | String | 否 | `relations/math_relations.ttl` | TTL 输入文件路径 |
| `--output` | String | 否 | `output/math_native_relations.csv` | CSV 输出文件路径 |
| `--verbose` | Flag | 否 | False | 显示详细日志 |

### 执行示例

```bash
python extract_native_relations.py
```

### 输出结果

执行成功时输出：
```
INFO: Parsing TTL file: relations/math_relations.ttl
INFO: Extracted relateTo relations: 9,870
INFO: Extracted subCategory relations: 328
INFO: Deduplicated bidirectional relations: 50
INFO: Total relations: 10,118
SUCCESS: Output written to output/math_native_relations.csv
```

---

## 2. 原生关系导入脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `edukg/scripts/kg_construction/import_native_relations_to_neo4j.py` |
| 执行方式 | `python import_native_relations_to_neo4j.py [--options]` |
| 依赖 | kg-math-knowledge-points 已完成 |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--input` | String | 否 | `output/math_native_relations.csv` | CSV 输入文件路径 |
| `--uri` | String | 否 | 从环境变量读取 | Neo4j 连接 URI |
| `--batch-size` | Integer | 否 | 100 | 批量导入批次大小 |

### 执行示例

```bash
python import_native_relations_to_neo4j.py
```

### 输出结果

执行成功时输出：
```
INFO: Loading relations: 10,118
INFO: Importing RELATED_TO relations...
INFO: Imported 9,820/9,870 (50 skipped - missing nodes)
INFO: Importing SUB_CATEGORY relations...
INFO: Imported 328/328 (0 skipped)
SUCCESS: Import completed. Statistics:
  - RELATED_TO: 9,820
  - SUB_CATEGORY: 328
  - Skipped (missing nodes): 50
```

---

## 3. 关系验证脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `edukg/scripts/kg_construction/validate_native_relations.py` |
| 执行方式 | `python validate_native_relations.py` |
| 退出码 | 0: 成功, 1: 失败 |

### 执行示例

```bash
python validate_native_relations.py
```

### 输出结果

**成功时:**
```
VALIDATION REPORT
==================
RELATED_TO relations: 9,820 ✓
SUB_CATEGORY relations: 328 ✓

All validations passed.
Exit code: 0
```

---

## 4. 完整工作流程

```bash
# 1. 提取原生关系
python extract_native_relations.py

# 2. 导入 Neo4j
python import_native_relations_to_neo4j.py

# 3. 验证导入
python validate_native_relations.py
```

---

## 重要说明

### relateTo ≠ PREREQUISITE

- **relateTo** → RELATED_TO：知识点横向关联（语义："相关"）
- **PREREQUISITE**：学习依赖（语义："不学A就学不懂B"）

两种关系语义完全不同，请勿混淆。

---

*文档生成时间: 2026-03-29*