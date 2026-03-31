# Knowledge Graph Construction Scripts

知识图谱构建脚本集，用于 EduKG 数据处理和 Neo4j schema 初始化。

## 脚本列表

| 脚本 | 功能 | 输入 | 输出 |
|-----|------|------|------|
| `split_main_ttl.py` | 按学科拆分 main.ttl | `main.ttl` (16MB) | 9 个 `main-{subject}.ttl` |
| `split_material_ttl.py` | 按学科拆分 material.ttl | `material.ttl` (3.5MB) | 10 个 `material-{subject}.ttl` |
| `create_neo4j_schema.py` | 创建 Neo4j schema | Neo4j 连接 | 3 个唯一性约束 |
| `validate_schema.py` | 验证 schema | Neo4j 连接 | 验证报告 |

## 使用方法

### 1. 拆分 main.ttl（知识点数据）

将 EduKG main.ttl 按学科拆分为独立文件：

```bash
# 使用默认路径
python scripts/kg_construction/split_main_ttl.py

# 自动发现学科
python scripts/kg_construction/split_main_ttl.py --auto-discover

# 指定学科
python scripts/kg_construction/split_main_ttl.py --subjects math,physics,chemistry
```

**输出文件**:
```
data/edukg/split/
├── main-biology.ttl    (20,611 triples)
├── main-chemistry.ttl  (19,999 triples)
├── main-chinese.ttl    (5,696 triples)
├── main-geo.ttl        (20,081 triples)
├── main-history.ttl    (12,546 triples)
├── main-math.ttl       (14,019 triples)
├── main-physics.ttl    (19,885 triples)
├── main-politics.ttl   (10,722 triples)
└── main-unknown.ttl    (159 triples)
```

### 2. 拆分 material.ttl（教材数据）

将 EduKG material.ttl 按学科拆分为独立文件：

```bash
# 使用默认路径
python scripts/kg_construction/split_material_ttl.py

# 自动发现学科
python scripts/kg_construction/split_material_ttl.py --auto-discover
```

**输出文件**:
```
data/edukg/split/
├── material-biology.ttl    (5,409 triples)
├── material-chemistry.ttl  (5,204 triples)
├── material-chinese.ttl    (1,555 triples)
├── material-english.ttl    (1,756 triples)
├── material-geo.ttl        (6,824 triples)
├── material-history.ttl    (5,241 triples)
├── material-math.ttl       (6,024 triples)
├── material-physics.ttl    (8,511 triples)
├── material-politics.ttl   (3,119 triples)
└── material-unknown.ttl    (14 triples)
```

**学科识别规则**:
- 从教材名称（P4 属性）中提取学科关键词
- 支持关键词：数学、物理、化学、生物/生物学、历史、地理、语文、英语、思想政治/政治
- 通过关系传播：教材 → 章节 → 子章节

### 3. 创建 Neo4j Schema

初始化知识图谱数据库 schema：

```bash
# 设置 Neo4j 密码
export NEO4J_PASSWORD="your_password"

# 执行 schema 创建
python scripts/kg_construction/create_neo4j_schema.py

# 仅查看 Cypher 语句（不执行）
python scripts/kg_construction/create_neo4j_schema.py --dry-run
```

**创建的约束**:
- `kp_uri_unique`: KnowledgePoint.uri 唯一
- `subject_code_unique`: Subject.code 唯一
- `textbook_isbn_unique`: Textbook.isbn 唯一

**注意**: 性能索引延迟到数据导入后创建（见 `kg-math-knowledge-points` change）。

### 4. 验证 Schema

验证 schema 是否正确创建：

```bash
export NEO4J_PASSWORD="your_password"
python scripts/kg_construction/validate_schema.py
```

**输出示例**:
```
VALIDATION REPORT
==================
Labels: 6/6 ✓
Constraints: 3/3 ✓

All schema elements are correctly created.
Exit code: 0
```

## 环境变量

| 变量 | 说明 | 默认值 |
|-----|------|-------|
| `NEO4J_URI` | Neo4j 连接 URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j 用户名 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 密码 | (必填) |

## 设计决策

### 为什么索引延迟创建？

由于数据量大（全学科约 56,000 知识点），先创建索引再批量插入会导致：
- 批量导入时间大幅增加（10x+）
- 索引碎片化

**正确流程**:
1. `kg-neo4j-schema`: 创建唯一性约束
2. `kg-math-knowledge-points`: 导入数据后创建性能索引

### 为什么 material.ttl 需要关系传播？

material.ttl 中的教材数据包含层级结构：
- 教材实体：有明确学科名称
- 章节实体：通过 P13/P2/P3/P5 关系连接到教材
- 子章节：通过 P5 关系连接到章节

通过 BFS 传播学科归属，确保所有相关实体正确分组。

## 测试

```bash
# 运行所有 kg_construction 测试
pytest tests/kg_construction/ -v

# 运行特定测试
pytest tests/kg_construction/test_split_material_ttl.py -v
```

## 相关 Changes

- `kg-neo4j-schema`: Schema 初始化（当前）
- `kg-math-knowledge-points`: 知识点数据导入
- `kg-math-native-relations`: 原生关系导入
- `kg-math-prerequisite-inference`: 前置关系推断