## Context

知识图谱数据整理项目需要一个统一的 Neo4j schema 来存储知识点和关系数据。当前状态：
- **无现有 schema**: Neo4j 数据库未初始化
- **数据源多样**: EduKG TTL 文件、教材信息、LLM 推断结果
- **多学科共用**: 9 个学科使用同一 schema 结构

设计约束：
- 使用 Neo4j 5.x 版本
- 支持中文节点名称和属性
- 需要支持快速查询（知识点名称、URI）

## Goals / Non-Goals

**Goals:**
- 创建标准化 schema，所有学科共用
- 定义清晰的节点标签和属性
- 建立必要的索引和约束，确保查询性能和数据完整性
- 提供验证脚本，确保 schema 正确创建

**Non-Goals:**
- 不导入任何数据（仅 schema）
- 不定义具体的关系内容（仅定义关系类型）
- 不处理跨源映射（后续 change 处理）

## Decisions

### D1: 节点标签设计

**决策**: 使用 6 种节点标签，层级结构清晰

```
Subject (学科)
  └── Stage (学段: 小学/初中/高中)
      └── Grade (年级)
          └── Textbook (教材)
              └── Chapter (章节)
                  └── KnowledgePoint (知识点)
```

**理由**:
- 层级清晰，便于查询和可视化
- 符合教育领域实际结构
- 支持按学科/年级快速过滤

**替代方案**: 扁平化设计（知识点直接包含学科/年级属性）
- **缺点**: 无法表达教材/章节层级，查询复杂

### D2: 知识点节点属性

**决策**: 使用以下核心属性

```cypher
(:KnowledgePoint {
  uri: STRING,           // 唯一标识，来自 EduKG
  external_id: STRING,   // 跨源映射 ID
  name: STRING,          // 知识点名称（中文）
  subject: STRING,       // 学科代码
  stage: STRING,         // 学段
  grade: STRING,         // 年级（推断或标注）
  chapter: STRING,       // 所属章节
  type: STRING,          // 类型: 定义/性质/定理/公式/方法
  difficulty: INTEGER,   // 难度等级 1-5
  description: STRING,   // 知识点描述
  source: STRING         // 数据来源: edukg/haoweilai/etc
})
```

**理由**:
- `uri` 作为全局唯一标识
- `external_id` 支持跨源映射
- `type` 分类支持按类型查询（定义优先学习）

### D3: 关系类型设计

**决策**: 定义 12 种关系类型

| 类型                     | 语义 | 用途 |
|------------------------|------|------|
| HAS_STAGE              | 学科→学段 | 层级结构 |
| HAS_GRADE              | 学段→年级 | 层级结构 |
| USE_TEXTBOOK           | 年级→教材 | 层级结构 |
| HAS_CHAPTER            | 教材→章节 | 层级结构 |
| HAS_KNOWLEDGE_POINT    | 章节→知识点 | 层级结构 |
| TEACHES_BEFORE         | 教学顺序 | 教学参考 |
| PREREQUISITE           | 学习依赖 | AI 答疑核心 |
| PREREQUISITE_ON        | EduKG 标准 | 互操作 |
| PREREQUISITE_CANDIDATE | 候选关系 | 后续验证 |
| RELATED_TO             | 知识关联 | 可视化 |
| SUB_CATEGORY           | 分类层级 | 分类导航 |

**理由**:
- 区分教学顺序 (TEACHES_BEFORE) 和学习依赖 (PREREQUISITE)
- 保留 TTL 原生关系 (RELATED_TO, SUB_CATEGORY)
- EduKG 标准关系支持互操作

### D4: 索引策略

**决策**: 创建以下索引

```cypher
// 节点属性索引
CREATE INDEX kp_name_idx FOR (n:KnowledgePoint) ON (n.name)
CREATE INDEX kp_uri_idx FOR (n:KnowledgePoint) ON (n.uri)
CREATE INDEX kp_subject_idx FOR (n:KnowledgePoint) ON (n.subject)
CREATE INDEX kp_grade_idx FOR (n:KnowledgePoint) ON (n.grade)

// 复合索引（常用查询组合）
CREATE INDEX kp_subject_grade_idx FOR (n:KnowledgePoint) ON (n.subject, n.grade)
```

**理由**:
- `name` 支持实体链接快速查找
- `uri` 支持跨源映射
- `subject + grade` 支持按学科年级过滤

### D5: 约束设计

**决策**: 创建唯一性约束

```cypher
// URI 必须唯一
CREATE CONSTRAINT kp_uri_unique FOR (n:KnowledgePoint) REQUIRE n.uri IS UNIQUE

// 学科代码唯一
CREATE CONSTRAINT subject_code_unique FOR (n:Subject) REQUIRE n.code IS UNIQUE
```

**理由**:
- 防止重复知识点导入
- 防止学科重复创建

## Risks / Trade-offs

### Risk 1: Schema 变更困难
**风险**: Neo4j schema 变更需要重建索引，可能影响已有数据
**缓解**: 设计阶段充分考虑扩展性，预留属性字段

### Risk 2: 中文编码问题
**风险**: 中文节点名称可能导致编码问题
**缓解**: 使用 UTF-8 编码，Neo4j 5.x 完全支持中文

### Risk 3: 索引过多影响写入性能
**风险**: 大量索引可能影响批量导入速度
**缓解**: 先创建必要索引，导入后根据查询需求补充

## Migration Plan

**部署步骤**:
1. 确保 Neo4j 服务运行
2. 执行 `create_neo4j_schema.py` 创建 schema
3. 执行 `validate_schema.py` 验证 schema
4. 验证通过后，后续 change 开始导入数据

**回滚策略**:
```cypher
// 删除所有索引和约束
DROP INDEX kp_name_idx IF EXISTS
DROP CONSTRAINT kp_uri_unique IF EXISTS
// ... 其他清理
```

## Open Questions

无（设计已确定）