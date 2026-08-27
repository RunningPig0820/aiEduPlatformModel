# 验证方案（续）
> summary: 验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-验证方案-5.md
> 类别：开发难点

---

### 九、验证方案（Demo 阶段务实策略）（续）

> 检索摘要：验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。

### 9.6 图谱质量指标
> 检索摘要：图谱质量指标含前置关系覆盖率≥30%、DAG合规率100%、平均前置链长度2-4跳、年级倒置率≤5%、高置信度占比≥60%。

指标	计算方法	目标值（demo）
前置关系覆盖率	有 PREREQUISITE 关系的知识点数 / 总知识点数	≥ 30%
DAG 合规率	无环的知识点比例（检测环的数量）	100%
平均前置链长度	所有知识点的最长前置路径长度的平均值	2~4 跳
年级倒置率	PREREQUISITE 关系出现高年级指向低年级的比例	≤ 5%（惩罚处理后）
置信度分布	高置信度（≥0.8）关系的占比	≥ 60%

### 9.7 Neo4j 部署配置
> 检索摘要：Neo4j 部署：社区版 4.4.x 单机、内存4G、存储100G+、CSV 全量备份。

配置项	值
版本	Neo4j 社区版 4.4.x
部署	单机部署
内存	4G
存储	100G+
备份	CSV 文件全量备份

### 9.6 典型业务查询模板
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

### 9.4 业务优先级（围绕 AI 引导式答疑）
> 检索摘要：业务优先级：P0前置依赖查询核心基础，P1知识点识别/知识缺陷诊断，P2学习路径推荐/年级学科定位可迭代。

优先级	业务场景	说明
P0	前置依赖查询	核心基础，方案核心目标
P1	知识点识别、知识缺陷诊断	Demo 必实现，支撑核心功能闭环
P2	学习路径推荐、年级/学科定位	可选迭代，核心跑通后补充

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§九、验证方案（Demo 阶段务实策略）（续））
