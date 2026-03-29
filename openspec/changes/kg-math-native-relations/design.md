## Context

数学学科是唯一有原生关系数据（relateTo, subCategory）的学科。这些关系来自 EduKG TTL 数据，语义与学习依赖（PREREQUISITE）完全不同，必须正确处理和保留。

当前状态：
- **数据源**: `relations/math_relations.ttl`
- **relateTo**: 9,870 条（知识点关联）
- **subCategory**: 328 条（分类层级）
- **Neo4j 知识点**: 已由 `kg-math-knowledge-points` change 导入

设计约束：
- relateTo → RELATED_TO（保留语义）
- subCategory → SUB_CATEGORY（保留语义）
- 不转换为 PREREQUISITE（语义完全不同）

## Goals / Non-Goals

**Goals:**
- 提取数学原生关系数据
- 正确导入 Neo4j（RELATED_TO, SUB_CATEGORY）
- 验证关系数量

**Non-Goals:**
- 不推断学习依赖关系（PREREQUISITE 在后续 change 处理）
- 不推断教学顺序（TEACHES_BEFORE 在后续 change 处理）
- 不处理其他学科的关系数据

## Decisions

### D1: 关系类型映射

**决策**: 使用以下映射规则

| TTL 关系 | Neo4j 关系 | 语义 |
|---------|-----------|------|
| relateTo | RELATED_TO | 知识点关联（横向） |
| subCategory | SUB_CATEGORY | 分类层级（纵向） |

**理由**:
- 保留 TTL 原生语义
- 不混淆关联关系与学习依赖
- 支持知识图谱可视化

### D2: 关系提取策略

**决策**: 使用 RDFLib 解析 TTL 关系文件

```python
# 关系提取
RELATION_PREDICATES = {
    "http://edukg.org/ontology#relateTo": "RELATED_TO",
    "http://edukg.org/ontology#subCategory": "SUB_CATEGORY",
}
```

**理由**: RDFLib 支持标准的 RDF 三元组解析

### D3: 节点存在性验证

**决策**: 导入前验证目标节点存在

```cypher
// 导入前检查
MATCH (source:KnowledgePoint {uri: $source_uri})
MATCH (target:KnowledgePoint {uri: $target_uri})
CREATE (source)-[:RELATED_TO]->(target)
```

**理由**:
- 防止关系指向不存在节点
- 利用 Neo4j 约束自动验证

### D4: CSV 输出格式

**决策**: 输出 CSV 格式中间文件

```
source_uri,target_uri,relation_type
http://edukg.org/knowledge/0.1/instance/math#516,http://edukg.org/knowledge/0.1/instance/math#520,RELATED_TO
```

**理由**:
- CSV 格式适合关系数据
- 便于人工检查和调试
- 支持批量导入

### D5: 双向关系处理

**决策**: relateTo 是双向关系，只保留单向

```python
# 去重双向关系
if (source_uri, target_uri) in relations or (target_uri, source_uri) in relations:
    continue  # 跳过，避免重复
```

**理由**:
- RELATED_TO 是双向语义，但 Neo4j 只需单向关系
- 减少存储和查询复杂度

## Risks / Trade-offs

### Risk 1: 关系指向不存在节点
**风险**: TTL 数据可能包含指向已删除知识点的 URI
**缓解**: 导入时使用 MATCH 确保目标节点存在，不存在则跳过并记录日志

### Risk 2: 关系数量不一致
**风险**: 导入后关系数量与 TTL 数据不一致
**缓解**: 统计导入前后数量，差异超过 5% 则报警

## Migration Plan

**执行步骤**:
1. 运行 `extract_native_relations.py` → 输出 `math_native_relations.csv`
2. 人工检查 CSV 文件（抽查 10-20 条）
3. 运行 `import_native_relations_to_neo4j.py` → 导入 Neo4j
4. 运行验证脚本 → 确认关系数量

**回滚策略**:
```cypher
// 删除所有原生关系
MATCH ()-[r:RELATED_TO]->() DELETE r
MATCH ()-[r:SUB_CATEGORY]->() DELETE r
```

## Open Questions

无（设计已确定）