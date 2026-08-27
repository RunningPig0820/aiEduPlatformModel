# D8：分层架构对齐现有模式

> summary: 决策：分层架构对齐现有模式：Domain/Infrastructure/Application/Interface四层，同步与导航分别由KgSyncAppService/KgNavigationAppService负责。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D8-分层架构对齐现有模式.md
> 类别：架构设计

> 检索摘要：决策：分层架构对齐现有模式：Domain/Infrastructure/Application/Interface四层，同步与导航分别由KgSyncAppService/KgNavigationAppService负责。

与现有代码保持一致：
- **Domain**: Entity + Value Object + Repository 接口
- **Infrastructure**: JPA Repository 实现 + Neo4j Sync Service（同步时使用）+ Neo4j Relation Query Service（图谱关系查询）
- **Application**: `KgSyncAppService`（同步）+ `KgNavigationAppService`（导航查询）
- **Interface**: `KnowledgeGraphController`（`/api/kg/**`）

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D8：分层架构对齐现有模式）
