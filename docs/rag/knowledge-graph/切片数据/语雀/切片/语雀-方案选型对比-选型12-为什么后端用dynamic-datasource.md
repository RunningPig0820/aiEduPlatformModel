# 选型12 后端双数据源：dynamic-datasource vs AbstractRoutingDataSource/多套 Config
> summary: Java 双数据源怎么实现？dynamic-datasource-spring-boot3-starter + @DS("kg") + Mapper 包隔离，比手动路由/多套 Config 简洁。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型12-为什么后端用dynamic-datasource.md
> 类别：架构设计

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| dynamic-datasource + @DS("kg") | 注解简洁/Mapper 隔离/GitHub 10k+ stars | 三方依赖 | 采用 |
| AbstractRoutingDataSource | 无三方 | 手动路由复杂 | 否决 |
| 多套 MyBatis Config | 隔离彻底 | 配置量大 | 否决 |
| 证据 | 证据：语雀-页面化-datasource-design.md / design-backend-datasource Decision 1 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型12）
