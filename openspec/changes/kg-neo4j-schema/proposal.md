> **执行顺序: 1/4** | **设计成本: 无** | **前置依赖: 无**

## Why

知识图谱数据整理项目需要 Neo4j 作为图数据库存储知识点和关系数据。在导入任何数据之前，必须先建立标准化的 schema（节点标签、属性、索引、约束），确保：

1. **数据一致性**：统一的节点标签和属性定义
2. **查询性能**：必要的索引支持快速查询
3. **数据完整性**：约束防止重复和无效数据
4. **复用性**：schema 设计一次，所有学科共用

这是整个知识图谱项目的**基础设施**，必须在数据导入之前完成。

## What Changes

1. 创建 Neo4j schema 初始化脚本
   - 定义节点标签：Subject, Stage, Grade, Textbook, Chapter, KnowledgePoint
   - 定义节点属性：标准化属性命名和类型
   - 创建索引：name, uri, external_id 等关键字段
   - 创建约束：确保唯一性

2. 定义关系类型（仅 schema，不导入数据）
   - 层级关系：HAS_STAGE, HAS_GRADE, USE_TEXTBOOK, HAS_CHAPTER, HAS_KNOWLEDGE_POINT
   - 学习依赖：PREREQUISITE, TEACHES_BEFORE, 先修_on, PREREQUISITE_CANDIDATE
   - 知识关联：RELATED_TO, SUB_CATEGORY

3. 编写 schema 验证脚本
   - 检查所有标签和索引是否正确创建
   - 检查约束是否生效

## Capabilities

### New Capabilities

- `neo4j-schema`: Neo4j 图数据库 schema 定义和初始化，支持知识图谱数据存储和高效查询
- `neo4j-schema-validation`: Schema 验证能力，确保 schema 正确创建并可投入使用

### Modified Capabilities

无（这是基础设施，不修改现有能力）

## Impact

- **新目录**: `ai-edu-ai-service/scripts/kg_construction/`
- **新脚本**: `create_neo4j_schema.py`, `validate_schema.py`
- **Neo4j**: 创建 6 个节点标签，15+ 索引，5+ 约束
- **后续依赖**: kg-math-knowledge-points change 依赖此 schema 存在