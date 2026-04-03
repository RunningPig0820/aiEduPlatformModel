# EduKG 知识图谱数据处理脚本

> 数学知识图谱数据下载与导入脚本

---

## 目录结构

```
edukg/scripts/kg_data/
├── import_math_classes.py     # 导入概念类到 Neo4j
├── import_math_entities.py    # 导入知识点实体到 Neo4j
├── import_math_relations.py   # 导入知识点关系到 Neo4j
├── import_partof_belongsto.py # 导入 partOf/belongsTo 关系
├── import_math_content.py     # 导入定义内容到 Entity
├── download_math_*.py         # 从 EduKG 下载数据
└── validate_edukg_data.py     # 验证数据完整性
```

---

## 导入脚本

### 1. import_math_classes.py

**用途**: 导入数学概念类（本体分类）

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `1_概念类(Class)/math_classes.json` | Class 节点 | 38 个 |
| | SUB_CLASS_OF 关系 | 37 个 |

**使用方法**:
```bash
python import_math_classes.py              # 导入
python import_math_classes.py --dry-run    # 仅打印语句
python import_math_classes.py --clear      # 清除后重新导入
python import_math_classes.py --stats      # 显示统计
```

---

### 2. import_math_entities.py

**用途**: 导入知识点实体

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `8_全部关联关系(Complete)/math_entities_complete.json` | Entity 节点 | 4,085 个 |
| | HAS_TYPE 关系 | 5,469 个 |

**使用方法**:
```bash
python import_math_entities.py              # 导入
python import_math_entities.py --dry-run    # 仅打印信息
python import_math_entities.py --stats      # 显示统计
```

---

### 3. import_math_relations.py

**用途**: 导入知识点关联关系

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `8_全部关联关系(Complete)/math_knowledge_relations.json` | RELATED_TO 关系 | 9,871 个 |

**使用方法**:
```bash
python import_math_relations.py              # 导入
python import_math_relations.py --dry-run    # 仅打印信息
python import_math_relations.py --stats      # 显示统计
```

---

### 4. import_partof_belongsto.py

**用途**: 导入部分-整体和所属关系

| 数据源 | 导入内容 | 数量 |
|--------|----------|------|
| `2_知识点实体(Instance)/知识点实例 _类型标签/math_instance.ttl` | PART_OF 关系 | 298 个 |
| | BELONGS_TO 关系 | 619 个 |

**使用方法**:
```bash
python import_partof_belongsto.py              # 导入
python import_partof_belongsto.py --dry-run    # 仅打印信息
python import_partof_belongsto.py --stats      # 显示统计
```

---

## 导入顺序

```bash
# 1. 先导入概念类
python import_math_classes.py

# 2. 再导入知识点实体
python import_math_entities.py

# 3. 导入关联关系
python import_math_relations.py

# 4. 导入 partOf/belongsTo 关系
python import_partof_belongsto.py

# 5. 导入定义内容
python import_math_content.py
```

---

## 重复导入处理

所有脚本使用 `MERGE` 语句，支持重复导入：

- **节点**: 重复导入 → 更新属性，不创建新节点
- **关系**: 重复导入 → 跳过，不创建新关系

---

## 数据文件对应关系

| 数据文件 | 用途 | 脚本 |
|----------|------|------|
| `1_概念类(Class)/math_classes.json` | 概念类定义 | `import_math_classes.py` |
| `8_.../math_entities_complete.json` | 知识点实体 | `import_math_entities.py` |
| `8_.../math_knowledge_relations.json` | 关联关系 | `import_math_relations.py` |
| `2_.../math_instance.ttl` | partOf/belongsTo | `import_partof_belongsto.py` |
| `3_.../math_statement.json` | 定义内容 | `import_math_content.py` |

---

## 导入结果

导入完成后 Neo4j 中的数据：

```
┌─────────────────────────────────────┐
│ Neo4j 数学知识图谱                   │
├─────────────────────────────────────┤
│ Class 节点:      38 个              │
│ Entity 节点:   4,085 个              │
│ SUB_CLASS_OF:     37 个              │
│ HAS_TYPE:      5,469 个              │
│ RELATED_TO:    9,871 个              │
│ PART_OF:         298 个              │
│ BELONGS_TO:      619 个              │
│ Entity.content: 2,808 个             │
└─────────────────────────────────────┘
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

-- 查看关联最多的实体
MATCH (e:Entity)-[:RELATED_TO]->()
RETURN e.label AS 实体, count(*) AS 关联数
ORDER BY 关联数 DESC
LIMIT 10

-- 查看知识点关联路径
MATCH path = (a:Entity)-[:RELATED_TO*1..3]->(b:Entity)
WHERE a.label = '一元一次方程'
RETURN [n IN nodes(path) | n.label] AS 路径
LIMIT 5
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

## 数据质量问题

### 1. 无类型的实体 (89个)

部分实体缺少 `types` 字段，无法关联到概念类。详见 `8_全部关联关系(Complete)/README.md`。

### 2. 小学知识点缺失

EduKG 数据主要覆盖初中和高中，缺少小学数学知识点。需要从人教版教材目录补充。

---

## 下一步

1. ✅ ~~导入知识点实体~~
2. ✅ ~~导入关联关系~~
3. ✅ ~~导入定义/定理内容~~
4. ✅ ~~导入 partOf/belongsTo 关系~~
5. 导入人教版教材知识点（补充小学）
6. 构建 prerequisite 先修关系