# 验证方案（续）
> summary: 验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-验证方案-4.md
> 类别：开发难点

---

### 九、验证方案（Demo 阶段务实策略）（续）

> 检索摘要：验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。

### 9.5 图谱查询性能优化（智谱建议）
> 检索摘要：多跳查询 [:PREREQUISITE*] 在5万+节点可能变慢，加深度限制(*..10)防死循环，可选离线预计算 prerequisite_level 加速。

问题：多跳查询 [:PREREQUISITE*] 在大规模图谱（5万+节点）时可能变慢。
改进方案：
// 1. 深度限制：防止死循环或超长路径
MATCH (target:KnowledgePoint {uri: $uri})<-[r:PREREQUISITE*..10]-(prereq)
RETURN prereq, r

// 2. 学习路径查询（带深度限制）
MATCH (target:KnowledgePoint {uri: $target_uri})
MATCH path = (start)-[:PREREQUISITE*..10]->(target)
RETURN path ORDER BY LENGTH(path) ASC

离线预计算方案（可选）：
def compute_prerequisite_levels(knowledge_points):
    """
    离线计算每个知识点的"前置层级"属性
    存入节点，便于快速查询
    """
    for kp in knowledge_points:
        # BFS 计算最长前置路径长度
        max_depth = bfs_max_depth(kp, 'PREREQUISITE')
        kp.prerequisite_level = max_depth
        # 存入 Neo4j
        update_node_property(kp.uri, 'prerequisite_level', max_depth)

预计算后查询：
// 快速查询：直接按层级排序
MATCH (kp:KnowledgePoint {uri: $target_uri})
MATCH (prereq:KnowledgePoint)
WHERE prereq.prerequisite_level < kp.prerequisite_level
RETURN prereq ORDER BY prereq.prerequisite_level ASC

### 9.5 抽样测试量化标准
> 检索摘要：抽样测试量化：随机抽100-200条 PREREQUISITE 覆盖不同年级类型，准确率目标≥70%，低于阈值调 Prompt/温度/置信度阈值。

抽样方法:
● 从数学学科随机抽取 100-200 条 PREREQUISITE 关系
● 覆盖不同年级、不同类型（定义/公式/方法）
● 由内部人员（或参照教材、课程标准）判断是否合理

评估标准:
准确率 = 合理关系数 / 抽样总数
目标: ≥70%

调整策略（若低于阈值）:
1. 调整 Prompt 设计（增加 Few-Shot 示例）
2. 降低 temperature（如 0.2）
3. 提高置信度阈值（如 0.85）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§九、验证方案（Demo 阶段务实策略）（续））
