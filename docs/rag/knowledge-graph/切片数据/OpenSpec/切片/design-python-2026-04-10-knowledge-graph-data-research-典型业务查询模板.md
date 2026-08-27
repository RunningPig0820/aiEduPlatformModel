# 9.6 典型业务查询模板
> summary: 典型业务查询模板：多跳前置依赖、教学前驱、知识缺陷计算(未掌握前置)、拓扑排序学习路径、候选前置查询。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-典型业务查询模板.md
> 类别：数据关联

> 检索摘要：典型业务查询模板：多跳前置依赖、教学前驱、知识缺陷计算(未掌握前置)、拓扑排序学习路径、候选前置查询。

// 1. 获取知识点的所有前置依赖（多跳）
MATCH (target:KnowledgePoint {uri: $uri})<-[r:PREREQUISITE*]-(prereq)
RETURN prereq, r

// 2. 获取知识点的直接教学顺序（前驱）
MATCH (target:KnowledgePoint {uri: $uri})<-[r:TEACHES_BEFORE]-(prev)
RETURN prev, r

// 3. 基于知识点集合，计算知识缺陷（未掌握的前置）
MATCH (kp:KnowledgePoint) WHERE kp.uri IN $mastered_kps
WITH COLLECT(kp) AS mastered
MATCH (target:KnowledgePoint {uri: $target_uri})<-[r:PREREQUISITE*]-(prereq)
WHERE NOT prereq IN mastered
RETURN prereq, r

// 4. 生成学习路径（拓扑排序）
MATCH (target:KnowledgePoint {uri: $target_uri})
MATCH path = (start)-[:PREREQUISITE*]->(target)
RETURN path ORDER BY LENGTH(path) ASC

// 5. 查询候选前置关系（待验证）
MATCH (kp:KnowledgePoint)-[r:PREREQUISITE_CANDIDATE]->(target)
WHERE r.confidence >= 0.6
RETURN kp, target, r

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§9.6 典型业务查询模板）
