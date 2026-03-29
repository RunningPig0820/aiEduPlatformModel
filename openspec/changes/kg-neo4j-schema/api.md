# Neo4j Schema 管理 CLI 文档

> 模块: kg_construction (知识图谱构建脚本)
>
> 更新日期: 2026-03-29

---

## 概述

本 change 不提供 HTTP API 接口，而是提供**命令行脚本**用于 Neo4j schema 初始化和验证。这些脚本供运维人员和开发人员使用。

---

## 1. Schema 初始化脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/create_neo4j_schema.py` |
| 执行方式 | `python create_neo4j_schema.py [--options]` |
| 依赖 | Neo4j Python driver, 环境变量配置 |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--dry-run` | Flag | 否 | False | 仅打印 Cypher 语句，不执行 |
| `--uri` | String | 否 | 从环境变量读取 | Neo4j 连接 URI |
| `--user` | String | 否 | 从环境变量读取 | Neo4j 用户名 |
| `--password` | String | 否 | 从环境变量读取 | Neo4j 密码 |

### 执行示例

**正常执行:**
```bash
cd ai-edu-ai-service/scripts/kg_construction
python create_neo4j_schema.py
```

**Dry-run 模式（查看 Cypher 语句）:**
```bash
python create_neo4j_schema.py --dry-run
```

**手动指定连接参数:**
```bash
python create_neo4j_schema.py --uri bolt://localhost:7687 --user neo4j --password your_password
```

### 输出结果

执行成功时输出：
```
INFO: Creating node labels...
INFO: Created label: Subject
INFO: Created label: Stage
INFO: Created label: Grade
INFO: Created label: Textbook
INFO: Created label: Chapter
INFO: Created label: KnowledgePoint
INFO: Creating indexes...
INFO: Created index: kp_name_idx
INFO: Created index: kp_uri_idx
INFO: Created index: kp_subject_idx
INFO: Created index: kp_grade_idx
INFO: Created index: kp_subject_grade_idx
INFO: Creating constraints...
INFO: Created constraint: kp_uri_unique
INFO: Created constraint: subject_code_unique
SUCCESS: Schema initialization completed
```

### 错误处理

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| 连接失败 | Neo4j 服务未启动或连接参数错误 | 检查 Neo4j 服务状态，确认环境变量配置 |
| 认证失败 | 用户名或密码错误 | 检查 NEO4J_USER 和 NEO4J_PASSWORD 环境变量 |
| Schema 已存在 | 索引或约束已创建 | 脚本会跳过已存在的元素，不会报错 |

---

## 2. Schema 验证脚本

### 基本信息

| 项目 | 值 |
|------|-----|
| 脚本路径 | `ai-edu-ai-service/scripts/kg_construction/validate_schema.py` |
| 执行方式 | `python validate_schema.py [--options]` |
| 退出码 | 0: 成功, 1: 失败 |

### 命令行参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--verbose` | Flag | 否 | False | 显示详细信息 |
| `--uri` | String | 否 | 从环境变量读取 | Neo4j 连接 URI |
| `--user` | String | 否 | 从环境变量读取 | Neo4j 用户名 |
| `--password` | String | 否 | 从环境变量读取 | Neo4j 密码 |

### 执行示例

**正常验证:**
```bash
python validate_schema.py
```

**详细模式:**
```bash
python validate_schema.py --verbose
```

### 输出结果

**成功时:**
```
VALIDATION REPORT
==================
Labels: 6/6 ✓
Indexes: 5/5 ✓
Constraints: 2/2 ✓

All schema elements are correctly created.
Exit code: 0
```

**失败时:**
```
VALIDATION REPORT
==================
Labels: 5/6 ✗ (Missing: Textbook)
Indexes: 3/5 ✗ (Missing: kp_grade_idx, kp_subject_grade_idx)
Constraints: 2/2 ✓

Missing schema elements detected. Please run create_neo4j_schema.py
Exit code: 1
```

---

## 3. 环境变量配置

Schema 脚本依赖以下环境变量（在 `.env` 文件中配置）：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `NEO4J_URI` | Neo4j 连接 URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j 用户名 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 密码 | `your_password` |
| `NEO4J_DATABASE` | Neo4j 数据库名 | `neo4j` (默认) |

---

## 前端调用注意事项

**本模块无 HTTP API**，前端不直接调用这些脚本。

如果需要通过 API 管理 Neo4j schema，可由后端开发人员封装为 HTTP 接口（后续 change 中实现）。

---

*文档生成时间: 2026-03-29*