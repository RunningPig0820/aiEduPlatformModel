# 13.9 幂等性设计
> summary: Neo4j 导入用 MERGE 保证幂等：知识点按 uri 唯一，前置关系按端点和类型唯一，重复执行不产生重复数据。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-幂等性设计.md
> 类别：开发难点

> 检索摘要：Neo4j 导入用 MERGE 保证幂等：知识点按 uri 唯一，前置关系按端点和类型唯一，重复执行不产生重复数据。

Neo4j 导入使用 MERGE：
// 知识点节点（基于 uri 唯一）
MERGE (kp:KnowledgePoint {uri: $uri})
SET kp.name = $name,
    kp.subject = $subject,
    kp.grade = $grade,
    kp.type = $type

// 前置关系（基于端点和类型唯一）
MATCH (from:KnowledgePoint {uri: $from_uri})
MATCH (to:KnowledgePoint {uri: $to_uri})
MERGE (from)-[r:PREREQUISITE]->(to)
SET r.confidence = $confidence,
    r.source = $source,
    r.evidence_types = $evidence_types

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.9 幂等性设计）
