# 方案选型与决策记录：知识图谱双数据源方案

> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-datasource-16-方案选型与决策记录.md
> 类别：架构设计

## 决策内容

知识图谱（EduKG）需要独立数据库 ai_edu_kg 与业务库 ai_edu_user 物理隔离。决策引入 Baomidou 的 dynamic-datasource-spring-boot3-starter（4.x 版本），通过 @DS("kg") 注解实现数据源路由。该方案与 MyBatis-Plus 官方推荐方案一致，兼容性好。

## 替代方案对比

| 方案 | 复杂度 | 侵入性 | 适用场景 |
|------|--------|--------|----------|
| @DS 注解（推荐） | 低 | 低（仅在 Mapper/Service 加注解） | 固定数据源路由 |
| AbstractRoutingDataSource | 中 | 中（需自定义 ThreadContext + 拦截器） | 运行时动态切换 |
| 多套 MyBatis Config | 高 | 高（需手动配置 SqlSessionFactory） | 完全不同的 ORM 配置 |

## 选择 @DS 注解方案的原因

- 与 MyBatis-Plus 官方推荐方案一致，兼容性好
- Mapper 级别注解即可，无需改 Service 层
- 配置简单，application.yml 声明多个数据源即可

## 决策落地要点

- 路由策略：com.ai.edu.infrastructure.persistence.mapper.* 默认路由 user 库；com.ai.edu.infrastructure.persistence.edukg.mapper.* 加 @DS("kg") 路由 kg 库
- 事务：@Transactional 默认绑定 user 数据源，知识图谱 Service 用 @Transactional("kg") 显式指定；跨库操作不做分布式事务，应用层保证一致性
- 配置：application.yml 用 dynamic 多数据源声明 user 与 kg，primary=user、strict 严格模式开启（未匹配的数据源抛异常）
- MapperScan：拆分为两个 basePackages，edukg.mapper 路径通过 annotationClass 绑定 DS 注解
- Flyway：迁移脚本按库分组 db/migration/user 与 db/migration/kg，知识图谱用自定义配置类创建第二个 Flyway 实例（当前 Flyway 全部禁用，表结构手动创建）

## 非目标边界

- 不做跨库 JOIN（知识图谱与业务表通过 URI 引用，不物理 JOIN）
- 不做分布式事务
- 不做运行时动态数据源切换（Mapper 级别固定路由）

## 相关风险提示

- @Transactional 漏加数据源绑定会写到错误的库，知识图谱 Service 需显式指定 @Transactional("kg")
- 连接池最大连接数翻倍（20+20=40），MySQL 服务端需支持
- 跨库数据一致性依赖应用层保证，无物理外键
