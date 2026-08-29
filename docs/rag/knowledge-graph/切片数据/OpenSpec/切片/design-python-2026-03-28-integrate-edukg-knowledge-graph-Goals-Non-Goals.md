# Goals / Non-Goals
> summary: 目标集成 Neo4j 图数据库/TTL 导入工具/实体查询 API/实体链接服务/知识树可视化数据输出并预留向量接口；不做向量库集成、前端可视化与增量更新。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-Goals-Non-Goals.md
> 类别：项目介绍

> 检索摘要：目标集成 Neo4j 图数据库/TTL 导入工具/实体查询 API/实体链接服务/知识树可视化数据输出并预留向量接口；不做向量库集成、前端可视化与增量更新。

**Goals:**
1. 集成 Neo4j 图数据库，支持知识图谱存储和查询
2. 实现 TTL 文件导入 Neo4j 的工具
3. 提供知识点实体查询 API
4. 实现文本实体链接服务
5. 支持学科知识树可视化数据输出
6. 预留向量数据库接口

**Non-Goals:**
- 本期不实现向量数据库集成（下一阶段）
- 不实现前端可视化（仅提供 API）
- 不实现自定义知识点编辑（后续扩展）
- 不实现知识图谱增量更新（后续扩展）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§Goals / Non-Goals）
