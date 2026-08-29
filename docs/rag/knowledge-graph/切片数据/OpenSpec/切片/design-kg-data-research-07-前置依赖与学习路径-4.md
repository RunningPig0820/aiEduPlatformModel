# 前置依赖与学习路径：学习路径查询与业务应用

> summary: 前置依赖与学习路径（学习路径查询与业务应用）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-07-前置依赖与学习路径-4.md
> 类别：数据关联

---

> 检索摘要：学习路径怎么查、业务怎么用？多跳查询 [:PREREQUISITE*] 加深度限制 *..10 防慢查询，离线预计算 prerequisite_level 属性加速；典型查询模板：多跳前置依赖/教学前驱/知识缺陷计算(未掌握前置)/拓扑排序学习路径/候选前置(≥0.6)；业务优先级 P0 前置依赖查询。

**图谱查询性能优化（智谱建议，状态：）**：多跳查询 `[:PREREQUISITE*]` 在 5 万+节点图谱可能变慢。改进方案：
1. 深度限制防死循环/超长路径：`MATCH (target:KnowledgePoint {uri:$uri})<-[r:PREREQUISITE*..10]-(prereq) RETURN prereq, r`
2. 学习路径查询带深度限制：`MATCH (target:KnowledgePoint {uri:$target_uri}) MATCH path=(start)-[:PREREQUISITE*..10]->(target) RETURN path ORDER BY LENGTH(path) ASC`
3. 离线预计算（可选）：BFS 计算每个知识点最长前置路径深度，存入节点属性 prerequisite_level；查询改为 `WHERE prereq.prerequisite_level < kp.prerequisite_level` 按层级直接排序，避免多跳。

**典型业务查询模板（状态：）**
1. 获取知识点的所有前置依赖（多跳）：`MATCH (target:KnowledgePoint {uri:$uri})<-[r:PREREQUISITE*]-(prereq) RETURN prereq, r`
2. 获取知识点的直接教学顺序（前驱）：`MATCH (target:KnowledgePoint {uri:$uri})<-[r:TEACHES_BEFORE]-(prev) RETURN prev, r`
3. 基于知识点集合计算知识缺陷（未掌握的前置）：已掌握集合 $mastered_kps，多跳查 `WHERE NOT prereq IN mastered` 返回未掌握前置
4. 生成学习路径（拓扑排序）：`MATCH (target:KnowledgePoint {uri:$target_uri}) MATCH path=(start)-[:PREREQUISITE*]->(target) RETURN path ORDER BY LENGTH(path) ASC`
5. 查询候选前置关系（待验证）：`MATCH (kp:KnowledgePoint)-[r:PREREQUISITE_CANDIDATE]->(target) WHERE r.confidence >= 0.6 RETURN kp, target, r`

**业务优先级（围绕 AI 引导式答疑，状态：）**：P0 前置依赖查询（核心基础，方案核心目标）；P1 知识点识别、知识缺陷诊断（Demo 必实现，支撑核心功能闭环）；P2 学习路径推荐、年级/学科定位（可选迭代，核心跑通后补充）。

**Neo4j 部署配置（状态：）**：Neo4j 社区版 4.4.x、单机部署、内存 4G、存储 100G+、备份采用 CSV 文件全量备份。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§9.5 图谱查询性能优化、§9.6 典型业务查询模板、§9.7 Neo4j 部署配置）
