> **执行顺序: 3/5** | **设计成本: 无** | **前置依赖: kg-math-knowledge-points**

## Why

数学学科是**唯一有原生关系数据**的学科（relateTo: 9,870 条，subCategory: 328 条）。这些原生关系来自 EduKG TTL 数据，是知识图谱的重要组成部分，必须保留并正确导入 Neo4j。

**重要区别**：
- **relateTo ≠ PREREQUISITE**：relateTo 是知识点关联，语义是"相关"，不是学习依赖
- **subCategory ≠ PREREQUISITE**：subCategory 是分类层级，语义是"子分类"

这些原生关系支持：
- 知识点横向关联查询（RELATED_TO）
- 分类导航（SUB_CATEGORY）
- 知识图谱可视化

## What Changes

1. **原生关系提取脚本**
   - 解析 `relations/math_relations.ttl`
   - 提取 relateTo 关系 (9,870 条)
   - 提取 subCategory 关系 (328 条)
   - 输出 CSV 中间文件

2. **关系导入脚本**
   - 导入 relateTo → RELATED_TO 关系
   - 导入 subCategory → SUB_CATEGORY 关系
   - 验证关系数量

## Capabilities

### New Capabilities

- `native-relation-extractor`: 原生关系提取能力，支持 TTL 格式的 relateTo 和 subCategory 关系解析
- `native-relation-importer`: 原生关系导入 Neo4j 能力，保留 TTL 数据语义

### Modified Capabilities

无（这是新能力，不修改现有能力）

## Impact

- **新脚本**: `extract_native_relations.py`, `import_native_relations_to_neo4j.py`
- **中间文件**: `math_native_relations.csv`
- **Neo4j**: 新增 10,198 条关系（RELATED_TO: 9,870, SUB_CATEGORY: 328）
- **依赖**: 依赖 `kg-math-knowledge-points` change 完成并测试通过（知识点节点必须先存在）