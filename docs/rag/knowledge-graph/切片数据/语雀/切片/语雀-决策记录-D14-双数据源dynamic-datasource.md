# 双数据源 dynamic-datasource + @DS("kg")（ai_edu_kg 物理隔离）

> summary: 知识图谱数据源怎么隔离？dynamic-datasource-spring-boot3-starter + @DS("kg") 注解，ai_edu_kg 与业务库 ai_edu_user 物理隔离。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D14-双数据源dynamic-datasource.md
> 类别：操作流程

---

### D14 双数据源 dynamic-datasource + @DS("kg")（ai_edu_kg 物理隔离）
> 检索摘要：知识图谱数据源怎么隔离？dynamic-datasource-spring-boot3-starter + @DS("kg") 注解，ai_edu_kg 与业务库 ai_edu_user 物理隔离。

| 属性 | 内容 |
|---|---|
| 背景 | Spring Boot 单数据源连 ai_edu_user；知识图谱需独立库物理隔离 + 独立扩展 |
| 演进 | 早期单数据源 → 双数据源 |
| 拍板理由 | Mapper 包路径隔离（persistence.edukg.mapper.* → kg）；备选 AbstractRoutingDataSource/多套 MyBatis Config 被否（复杂度高）；HikariCP 每源 5-20 连接 |
| 系统影响 | @Transactional("kg") 事务；Flyway 按库分组（当前全禁用，表手动创建）；/api/kg/** → ai_edu_kg |
| 证据 | 证据：语雀-页面化-datasource-design.md / design-backend-2026-06-03-knowledge-graph-datasource.md Decision 1/2 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D14）
