# Risks / Trade-offs

> summary: 双数据源风险涵盖第三方库稳定性、跨库一致性、Mapper 注解遗漏、连接池翻倍、事务漏绑数据源，各有缓解措施。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-风险与权衡.md
> 类别：架构设计

---

### Risks / Trade-offs

> 检索摘要：双数据源风险涵盖第三方库稳定性、跨库一致性、Mapper 注解遗漏、连接池翻倍、事务漏绑数据源，各有缓解措施。

| 风险 | 缓解措施 |
|------|----------|
| `dynamic-datasource` 第三方库稳定性 | 该库是 MyBatis-Plus 生态中最流行的多数据源方案，GitHub 10k+ stars，Spring Boot 3 兼容 |
| 跨库数据一致性 | 知识图谱与业务表通过 URI 引用，无物理外键，应用层保证引用有效性 |
| Mapper 注解遗漏 | Code Review 时检查所有 edukg 包下的 Mapper 是否都加了 `@DS("kg")` |
| Flyway 双库管理复杂度 | 当前 Flyway 全部禁用，表结构手动创建；后续启用时按库独立配置 |
| 连接池资源占用 | 两个数据源共享 HikariCP 配置，最大连接数翻倍（20+20=40），MySQL 服务端需支持 |
| `@Transactional` 数据源绑定 | 默认绑定 primary 数据源，知识图谱 Service 需显式指定 `@Transactional("kg")`，漏加会导致写到错误的库 |

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§Risks / Trade-offs）
