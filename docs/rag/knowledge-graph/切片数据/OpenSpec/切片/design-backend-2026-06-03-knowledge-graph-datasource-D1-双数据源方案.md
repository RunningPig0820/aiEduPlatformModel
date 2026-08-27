# 双数据源方案

> summary: 双数据源选用 Baomidou dynamic-datasource-spring-boot3-starter 的 @DS("kg") 注解路由，与 MyBatis-Plus 官方推荐方案一致。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-D1-双数据源方案.md
> 类别：架构设计

---

### D1：双数据源方案

> 检索摘要：双数据源选用 Baomidou dynamic-datasource-spring-boot3-starter 的 @DS("kg") 注解路由，与 MyBatis-Plus 官方推荐方案一致。

**决策**: 引入 Baomidou 的 `dynamic-datasource-spring-boot3-starter`（4.x 版本），通过 `@DS("kg")` 注解实现数据源路由。

**替代方案对比**:

| 方案 | 复杂度 | 侵入性 | 适用场景 |
|------|--------|--------|----------|
| `@DS` 注解（推荐） | 低 | 低（仅在 Mapper/Service 加注解） | 固定数据源路由 |
| `AbstractRoutingDataSource` | 中 | 中（需自定义 ThreadContext + 拦截器） | 运行时动态切换 |
| 多套 MyBatis Config | 高 | 高（需手动配置 SqlSessionFactory） | 完全不同的 ORM 配置 |

选择 `@DS` 注解方案原因：
- 与 MyBatis-Plus 官方推荐方案一致，兼容性好
- Mapper 级别注解即可，无需改 Service 层
- 配置简单，`application.yml` 声明多个数据源即可

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§D1）
