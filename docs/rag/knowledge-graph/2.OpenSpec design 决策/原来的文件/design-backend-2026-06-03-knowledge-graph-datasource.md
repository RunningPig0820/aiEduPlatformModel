## Context

当前项目使用 Spring Boot 单数据源配置，所有 MyBatis-Plus Mapper 都连接到一个 MySQL 数据库 `ai_edu_user`。知识图谱（EduKG）需要独立数据库 `ai_edu_kg` 存储，实现物理隔离和独立扩展。项目使用 MyBatis-Plus 3.5.5 + Spring Boot 3.2.5，无 JPA/Hibernate，无自定义 DataSource 配置。

## Goals / Non-Goals

**Goals:**
- 实现双数据源架构：`ai_edu_user`（业务库）+ `ai_edu_kg`（知识图谱库）
- 知识图谱 Mapper 自动路由到 `ai_edu_kg`，业务 Mapper 继续使用 `ai_edu_user`
- 对现有业务代码零侵入，认证/授权流程不受影响
- Flyway 迁移脚本按库隔离管理

**Non-Goals:**
- 不做跨库 JOIN（知识图谱与业务表通过 URI 引用，不物理 JOIN）
- 不做分布式事务（`@Transactional` 按数据源隔离）
- 不做动态数据源切换（Mapper 级别固定路由，不需要运行时动态切换）

## Decisions

### 1. 双数据源方案：`dynamic-datasource-spring-boot3-starter`

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

### 2. 数据源路由策略：Mapper 包路径隔离

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

### 3. 事务管理：按数据源隔离

**决策**: `@Transactional` 默认绑定到 `user` 数据源。知识图谱的 Service 方法使用 `@Transactional("kg")` 指定数据源。跨库操作不使用分布式事务，通过应用层保证一致性。

```java
@Service
public class KgSyncAppService {
    @Resource
    private KgTextbookMapper kgTextbookMapper;

    @Transactional("kg")  // 绑定到 kg 数据源
    public void syncFull() { ... }
}
```

### 4. application.yml 配置结构

```yaml
spring:
  datasource:
    dynamic:
      primary: user          # 默认数据源
      strict: true           # 严格模式：未匹配的数据源抛异常
      datasource:
        user:
          url: jdbc:mysql://gz-cdb-e8peyaxv.sql.tencentcdb.com:23316/ai_edu_user?...
          username: dev
          password: dev2026+
          driver-class-name: com.mysql.cj.jdbc.Driver
        kg:
          url: jdbc:mysql://gz-cdb-e8peyaxv.sql.tencentcdb.com:23316/ai_edu_kg?...
          username: dev
          password: dev2026+
          driver-class-name: com.mysql.cj.jdbc.Driver
      hikari:
        minimum-idle: 5
        maximum-pool-size: 20
```

### 5. Mapper 扫描路径拆分

**决策**: `@MapperScan` 拆分为两个：
```java
@SpringBootApplication
@MapperScan(basePackages = "com.ai.edu.infrastructure.persistence.mapper", annotationClass = DS.class)
@MapperScan(basePackages = "com.ai.edu.infrastructure.persistence.edukg.mapper")
public class AiEduPlatformApplication { ... }
```

### 6. Flyway 迁移脚本按库分组

**决策**: 迁移脚本目录结构：
```
db/
├── migration/
│   ├── user/
│   │   └── V1__Init_Demo_Users.sql
│   └── kg/
│       └── V1__Init_Knowledge_Graph.sql
```

知识图谱的 Flyway 配置指定连接 `ai_edu_kg`：
```yaml
spring:
  flyway:
    enabled: false           # 用户库 Flyway（禁用）
    locations: classpath:db/migration/user

  flyway-kg:                 # 知识图谱 Flyway（自定义 Bean）
    enabled: false            # 当前禁用，手动执行
    locations: classpath:db/migration/kg
    url: ${KG_DB_URL}
```

由于 Spring Boot 仅支持一个原生 Flyway Bean，知识图谱的 Flyway 通过自定义配置类创建第二个 Bean。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| `dynamic-datasource` 第三方库稳定性 | 该库是 MyBatis-Plus 生态中最流行的多数据源方案，GitHub 10k+ stars，Spring Boot 3 兼容 |
| 跨库数据一致性 | 知识图谱与业务表通过 URI 引用，无物理外键，应用层保证引用有效性 |
| Mapper 注解遗漏 | Code Review 时检查所有 edukg 包下的 Mapper 是否都加了 `@DS("kg")` |
| Flyway 双库管理复杂度 | 当前 Flyway 全部禁用，表结构手动创建；后续启用时按库独立配置 |
| 连接池资源占用 | 两个数据源共享 HikariCP 配置，最大连接数翻倍（20+20=40），MySQL 服务端需支持 |
| `@Transactional` 数据源绑定 | 默认绑定 primary 数据源，知识图谱 Service 需显式指定 `@Transactional("kg")`，漏加会导致写到错误的库 |
