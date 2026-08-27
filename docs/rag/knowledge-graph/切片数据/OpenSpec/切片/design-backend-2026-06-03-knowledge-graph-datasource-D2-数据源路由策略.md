# 数据源路由策略

> summary: 数据源路由按 Mapper 包路径隔离：persistence.mapper 默认 user 库，edukg.mapper 加 @DS("kg") 注解。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-D2-数据源路由策略.md
> 类别：架构设计

---

### D2：数据源路由策略

> 检索摘要：数据源路由按 Mapper 包路径隔离：persistence.mapper 默认 user 库，edukg.mapper 加 @DS("kg") 注解。

**决策**: 通过包路径区分数据源：
- `com.ai.edu.infrastructure.persistence.mapper.*` → `@DS("user")`（默认）
- `com.ai.edu.infrastructure.persistence.edukg.mapper.*` → `@DS("kg")`

**实现方式**: 在 Mapper 接口上加 `@DS` 注解，或在 MyBatis 配置中按包扫描自动绑定。选择 Mapper 注解方式，简单直观，不影响现有代码。

```java
// 业务 Mapper - 不需要注解（默认 user 库）
@Mapper
public interface UserMapper extends BaseMapper<User> { ... }

// 知识图谱 Mapper - 加 @DS("kg")
@Mapper
@DS("kg")
public interface KgTextbookMapper extends BaseMapper<KgTextbook> { ... }
```

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§D2）
