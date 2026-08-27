# 派生层只存MySQL，权威图谱只读

> summary: 题型派生层 3 张表全放 ai_edu_learning，Neo4j 与 kg-sync 镜像只读，以 kp_uri 为钩子借权威结构，拒绝派生节点物化进 Neo4j。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D1-派生层只存mysql-权威图谱只读.md
> 类别：数据存储

> 检索摘要：题型派生层 3 张表全放 ai_edu_learning，Neo4j 与 kg-sync 镜像只读，以 kp_uri 为钩子借权威结构，拒绝派生节点物化进 Neo4j。

**决策**：题型派生层 3 张表全部放 `ai_edu_learning`，Neo4j 与 kg-sync 镜像只读。

**理由**：题型空间无限（鸡兔同笼、相遇、浓度…无穷），教材知识点有限（可数）。把无限挂到有限上会让图爆炸、污染权威结构。派生层以 `kp_uri` 为钩子"借"权威结构，图逻辑（兄弟/前置/关联）走现有 `KgNeo4jService` 只读展开。

**替代方案**：派生节点物化进 Neo4j 扩展命名空间（`ExtAlias` + `ALIAS_OF` 边）。**拒绝**：现阶段无图遍历需求（MySQL 键值够用），且增加权威图耦合；留待阶段 2 需图遍历时再评估。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D1 派生层只存MySQL，权威图谱只读）
