# Goals / Non-Goals

> summary: 目标是实现 ai_edu_user 与 ai_edu_kg 双数据源、知识图谱 Mapper 自动路由且业务零侵入；不做跨库 JOIN 与分布式事务。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-Goals-Non-Goals.md
> 类别：项目介绍

---

### Goals / Non-Goals

> 检索摘要：目标是实现 ai_edu_user 与 ai_edu_kg 双数据源、知识图谱 Mapper 自动路由且业务零侵入；不做跨库 JOIN 与分布式事务。

**Goals:**
- 实现双数据源架构：`ai_edu_user`（业务库）+ `ai_edu_kg`（知识图谱库）
- 知识图谱 Mapper 自动路由到 `ai_edu_kg`，业务 Mapper 继续使用 `ai_edu_user`
- 对现有业务代码零侵入，认证/授权流程不受影响
- Flyway 迁移脚本按库隔离管理

**Non-Goals:**
- 不做跨库 JOIN（知识图谱与业务表通过 URI 引用，不物理 JOIN）
- 不做分布式事务（`@Transactional` 按数据源隔离）
- 不做动态数据源切换（Mapper 级别固定路由，不需要运行时动态切换）

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§Goals / Non-Goals）
