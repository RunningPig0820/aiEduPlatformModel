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
| `2_知识点实体(complete)/math_complete_statement.json` | Entity 节点 | 4,085 个 |
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
| `4_知识点关联关系(Relation)/math_knowledge_relations.json` | RELATED_TO 关系 | 9,871 个 |

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
| `2_知识点实体(complete)/知识点实例_类型标签/math_instance.ttl` | PART_OF 关系 | 298 个 |
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
| `2_知识点实体(complete)/math_complete_statement.json` | 知识点实体 | `import_math_entities.py` |
| `4_知识点关联关系(Relation)/math_knowledge_relations.json` | 关联关系 | `import_math_relations.py` |
| `2_知识点实体(complete)/知识点实例_类型标签/math_instance.ttl` | partOf/belongsTo | `import_partof_belongsto.py` |
| `3_定义_定理(Statement)/math_statement.json` | 定义内容 | `import_math_content.py` |

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

部分实体缺少 `types` 字段，无法关联到概念类。

### 2. 小学知识点缺失

EduKG 数据主要覆盖初中和高中，缺少小学数学知识点。需要从人教版教材目录补充。

---

## 下一步

1. ✅ ~~导入知识点实体~~
2. ✅ ~~导入关联关系~~
3. ✅ ~~导入定义/定理内容~~
4. ✅ ~~导入 partOf/belongsTo 关系~~
5. ✅ ~~教材知识点标准化~~
6. **教材知识点匹配** → `match_textbook_kp.py`
7. 导入人教版教材知识点（补充小学）
8. 构建 prerequisite 先修关系

---

## 教材知识点匹配

### match_textbook_kp.py

**用途**: 匹配教材知识点到图谱知识点，生成 MATCHES_KG 关系

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

#### 模块依赖

```
match_textbook_kp.py
│
├── edukg/core/textbook/KPMatcher          # 知识点匹配器（主逻辑）
│   │   ├── get_best_match()               # 获取标准化名称
│   │   ├── exact_match()                  # 精确匹配
│   │   ├── _retrieve_candidates()         # 向量检索粗筛
│   │   ├── llm_match_with_cache()         # LLM双模型投票
│   │   └── match_all()                    # 批量匹配入口
│   │
│   └──── edukg/core/llm_inference/
│       │   ├── DualModelVoter             # 双模型投票
│       │   ├── prompt_templates           # 提示词模板
│       │   └── dual_model_voter.vote_with_retry()
│
├── edukg/core/textbook/config             # 路径配置
│   └── OUTPUT_DIR, OUTPUT_FILES, VECTOR_INDEX_DIR
│
├── edukg/core/neo4j/client                # Neo4j 客户端
│   └── load_kg_concepts()                 # 从 Neo4j 读取 Concept
│
└── edukg/config/settings                  # API Keys 配置
```

#### 数据文件依赖

| 文件 | 来源 | 用途 |
|------|------|------|
| `textbook_kps.json` | generate_textbook_data.py | 教材知识点列表 (~1350) |
| `normalized_kps_complete.json` | normalize_textbook_kp.py | 标准化结果 (KPMatcher 自动加载) |
| `vector_index/` | build_vector_index.py | 预构建向量索引（可选） |
| Neo4j Concept | import_math_entities.py | 图谱知识点 (~1295) |

#### 输出文件

| 文件 | 内容 |
|------|------|
| `matches_kg_relations.json` | 匹配结果（教材知识点 → 图谱知识点） |
| `llm_cache/` | LLM 调用缓存（断点续传） |
| `progress/match_kg.json` | 进度状态文件 |

#### 使用方法

```bash
# 运行匹配（默认使用向量检索 + 断点续传）
python match_textbook_kp.py

# 仅估算成本（不调用 LLM）
python match_textbook_kp.py --dry-run

# 显示已有结果统计
python match_textbook_kp.py --stats

# 使用预构建向量索引（加速启动）
python match_textbook_kp.py --use-prebuilt-index

# 强制重建向量索引后匹配
python match_textbook_kp.py --force-build-index

# 禁用向量检索（使用 difflib 字符匹配）
python match_textbook_kp.py --no-vector-retrieval

# 调整粗筛候选数量
python match_textbook_kp.py --candidate-top-n 30

# 从头开始（禁用断点续传）
python match_textbook_kp.py --no-resume
```

#### 前置条件

1. **Neo4j 有数据**: 已导入 EduKG Concept（约 1295 个）
2. **教材数据已生成**: `textbook_kps.json` 存在（约 1350 个）
3. **标准化已完成**: `normalized_kps_complete.json` 存在
4. **API Keys 配置**: `.env` 中有 `ZHIPU_API_KEY`, `DEEPSEEK_API_KEY`

#### 预估成本

| 项目 | 数量 | 说明 |
|------|------|------|
| 精确匹配 | ~200 | 名称完全匹配，无 LLM 调用 |
| LLM 匹配 | ~1150 | 需 LLM 投票判断 |
| 缓存命中 | ~30% | 断点续传复用已有结果 |
| 预估时间 | 10-20 分钟 | 5 并发，向量检索模式 |
| 预估成本 | < 1 元 | GLM-4-flash 免费，DeepSeek 低成本 |

#### 三阶段匹配流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          知识点匹配完整流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: 标准化预处理                                                        │
│  ├─ 输入: 教材知识点名称（1350条）                                             │
│  ├─ 操作: LLM 推断标准数学概念名称                                             │
│  ├─ 输出: normalized_kps_complete.json                                       │
│  │         {"original": "1-5的认识", "best_match": "自然数", ...}            │
│  └─ 效果: "秒的认识" → "秒"，直接匹配 EduKG ✓                                  │
│                                                                              │
│  Phase 2: 向量检索                                                            │
│  ├─ 输入: best_match 字段（标准化概念名）                                      │
│  ├─ 操作: 用 "自然数" 向量检索 EduKG（bge-small-zh-v1.5）                      │
│  ├─ 输出: top-20 候选概念（含相似度分数）                                      │
│  └─ 缓存: vector_index/（预构建索引）                                         │
│                                                                              │
│  Phase 3: LLM双模型投票                                                        │
│  ├─ 输入: 教材知识点 + top-20候选                                              │
│  ├─ 操作: GLM-4-flash + DeepSeek 双模型投票                                   │
│  ├─ 输出: 是否匹配 + 置信度                                                   │
│  ├─ 缓存: llm_cache/（断点续传）                                              │
│  └─ 优化: 早停 + 阈值过滤 + 调用限制（50x提速）                                 │
│                                                                              │
│  Phase 4: 输出结果                                                             │
│  ├─ 输出: matches_kg_relations.json                                          │
│  │         {"textbook_kp": "...", "kg_kp": "自然数", "matched": true}        │
│  └─ 用于: Neo4j MATCHES_KG 关系导入                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 相关教材脚本

| 脚本 | 用途 | 输出 |
|------|------|------|
| `generate_textbook_data.py` | 生成教材节点数据 | `textbooks.json`, `textbook_kps.json` |
| `normalize_textbook_kp.py` | 标准化知识点名称 | `normalized_kps_complete.json` |
| `build_vector_index.py` | 构建向量索引 | `vector_index/` |
| `match_textbook_kp.py` | 匹配到图谱知识点 | `matches_kg_relations.json` |
| `infer_textbook_kp.py` | 推断知识点属性 | `textbook_kps_inferred.json` |