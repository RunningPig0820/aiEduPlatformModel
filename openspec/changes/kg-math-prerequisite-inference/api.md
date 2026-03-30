# 数学前置关系推断 CLI 文档

> 模块: kg_construction (知识图谱构建脚本)
>
> 更新日期: 2026-03-29

---

## 概述

本 change 是知识图谱项目的**核心设计成本部分**，通过多种证据来源推断学习依赖关系（PREREQUISITE）：

1. **教学顺序推断**（TEACHES_BEFORE）：基于教材章节顺序
2. **定义依赖抽取**：从定义文本匹配知识点名称
3. **LLM 多模型投票**：GLM-4-flash + DeepSeek

处理流程：
```
infer_teaches_before.py → extract_definition_deps.py → infer_prerequisites_llm.py → fuse_prerequisites.py → import_prereq_to_neo4j.py → validate_dag.py
```

---

## 1. 教学顺序推断脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/infer_teaches_before.py` |
| 执行方式 | `python infer_teaches_before.py [--options]` |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--kp-input` | String | 否 | `output/math_final_data.json` | 知识点 JSON 输入路径 |
| `--output` | String | 否 | `output/math_teaches_before.csv` | CSV 输出路径 |

### 执行示例

```bash
python infer_teaches_before.py
```

### 输出结果

```
INFO: Loading knowledge points: 4,490
INFO: Inferring TEACHES_BEFORE within chapters...
INFO: Total inferred: 1,200 (within 45 chapters)
SUCCESS: Output written to output/math_teaches_before.csv
```

---

## 2. 定义依赖抽取脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/extract_definition_deps.py` |
| 执行方式 | `python extract_definition_deps.py [--options]` |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--kp-input` | String | 否 | `output/math_final_data.json` | 知识点 JSON 输入路径 |
| `--output` | String | 否 | `output/math_definition_deps.csv` | CSV 输出路径 |

### 执行示例

```bash
python extract_definition_deps.py
```

### 输出结果

```
INFO: Loading knowledge points: 4,490
INFO: Extracting definition dependencies...
INFO: Matched knowledge point names: 850
INFO: Definition dependencies: 850
INFO: Coverage: 19.0%
SUCCESS: Output written to output/math_definition_deps.csv
```

---

## 3. LLM 前置关系推断脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/infer_prerequisites_llm.py` |
| 执行方式 | `python infer_prerequisites_llm.py [--options]` |
| **设计成本** | 约 8,980 次 LLM 调用（glm-4-flash 免费 + deepseek <1元） |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--kp-input` | String | 否 | `output/math_final_data.json` | 知识点 JSON 输入路径 |
| `--output` | String | 否 | `output/math_llm_prereq.csv` | CSV 输出路径 |
| `--batch-size` | Integer | 否 | 10 | 批量处理批次大小 |
| `--rate-limit` | Integer | 否 | 10 | 每分钟 API 调用限制 |
| `--dry-run` | Flag | 否 | False | 仅估算成本，不实际调用 LLM |

### 执行示例

**正常执行:**
```bash
python infer_prerequisites_llm.py
```

**Dry-run 模式（仅估算成本）:**
```bash
python infer_prerequisites_llm.py --dry-run
```

### 输出结果

```
INFO: Loading knowledge points: 4,490
INFO: LLM Gateway scene: prerequisite_inference
INFO: Processing in batches (size=10, rate_limit=10/min)
INFO: Calling GLM-4-flash and DeepSeek for each pair...
INFO: Progress: 100/4490 (2.2%)
INFO: Progress: 4490/4490 (100%)
INFO: Total LLM calls: 8,980 (glm-4-flash: 4,490, deepseek: 4,490)
INFO: Estimated cost: <1 RMB (glm-4-flash free, deepseek ~0.001/1k tokens)
INFO: PREREQUISITE relations: 2,800 (high confidence)
INFO: PREREQUISITE_CANDIDATE relations: 500 (low confidence)
INFO: Discarded (models disagree): 1,190
SUCCESS: Output written to output/math_llm_prereq.csv
```

---

## 4. 关系融合脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/fuse_prerequisites.py` |
| 执行方式 | `python fuse_prerequisites.py [--options]` |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--def-input` | String | 否 | `output/math_definition_deps.csv` | 定义依赖 CSV 输入路径 |
| `--llm-input` | String | 否 | `output/math_llm_prereq.csv` | LLM 推断 CSV 输入路径 |
| `--output` | String | 否 | `output/math_final_prereq.csv` | 最终 CSV 输出路径 |

### 执行示例

```bash
python fuse_prerequisites.py
```

### 输出结果

```
INFO: Loading definition dependencies: 850
INFO: Loading LLM inference results: 3,300 (PREREQUISITE: 2,800, CANDIDATE: 500)
INFO: Fusing multiple evidence sources...
INFO: Deduplicated relations: 50
INFO: Created PREREQUISITE_ON relations: 3,650 (EduKG standard)
INFO: Final relations:
  - PREREQUISITE: 3,650
  - PREREQUISITE_CANDIDATE: 500
SUCCESS: Output written to output/math_final_prereq.csv
```

---

## 5. 前置关系导入脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/import_prereq_to_neo4j.py` |
| 执行方式 | `python import_prereq_to_neo4j.py [--options]` |
| 依赖 | kg-math-native-relations 已完成 |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--tb-input` | String | 否 | `output/math_teaches_before.csv` | TEACHES_BEFORE CSV 输入路径 |
| `--prereq-input` | String | 否 | `output/math_final_prereq.csv` | 最终关系 CSV 输入路径 |
| `--uri` | String | 否 | 从环境变量读取 | Neo4j 连接 URI |

### 执行示例

```bash
python import_prereq_to_neo4j.py
```

### 输出结果

```
INFO: Importing TEACHES_BEFORE relations: 1,200
INFO: Importing PREREQUISITE relations: 3,650
INFO: Importing PREREQUISITE_CANDIDATE relations: 500
INFO: Importing PREREQUISITE_ON relations: 3,650
SUCCESS: Import completed.
```

---

## 6. DAG 验证脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/validate_dag.py` |
| 执行方式 | `python validate_dag.py` |
| 退出码 | 0: 无环, 1: 有环 |

### 执行示例

```bash
python validate_dag.py
```

### 输出结果

**无环时:**
```
DAG VALIDATION REPORT
=====================
Cycle detection: 0 cycles ✓
Coverage rate: 81.3% ✓
Average chain length: 2.5 ✓
Confidence distribution:
  - High (≥0.8): 70%
  - Medium (0.5-0.8): 20%
  - Low (<0.5): 10%

All validations passed.
Exit code: 0
```

**有环时:**
```
DAG VALIDATION REPORT
=====================
Cycle detection: 5 cycles ✗
Involved knowledge points:
  - 一元二次方程 → 解方程 → 一元二次方程
  - ...
Cycle count: 5
Please fix cycles before proceeding.
Exit code: 1
```

---

## 7. 完整工作流程

```bash
# 1. 推断教学顺序
python infer_teaches_before.py

# 2. 抽取定义依赖
python extract_definition_deps.py

# 3. LLM 推断前置关系（设计成本核心）
python infer_prerequisites_llm.py

# 4. 融合多证据来源
python fuse_prerequisites.py

# 5. 导入 Neo4j
python import_prereq_to_neo4j.py

# 6. 验证 DAG
python validate_dag.py
```

---

## 重要区别

### TEACHES_BEFORE ≠ PREREQUISITE

- **TEACHES_BEFORE**：教材教学顺序（例：第一章 → 第二章）
- **PREREQUISITE**：学习依赖（例：加法 → 乘法）

教材先教A后教B，但学B不一定需要先学A。

---

*文档生成时间: 2026-03-29*