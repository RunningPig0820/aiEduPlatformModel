# 页面化-datasource-tasks（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/tasks
> 字数：445 ｜ 下载：2026-08-24

## 1. 依赖与配置

- [x] 1.1 在父 pom.xml 中添加 `dynamic-datasource-spring-boot3-starter` 依赖管理（版本 4.x）
- [x] 1.2 在 `ai-edu-infrastructure/pom.xml` 引入 `dynamic-datasource-spring-boot3-starter` 依赖
- [x] 1.3 修改 `application.yml`：将 `spring.datasource` 改为 `spring.datasource.dynamic` 双数据源结构（user + kg）
- [x] 1.4 修改 `application-integration.yml`：同步双数据源配置
- [x] 1.5 修改 `application-test.yml`：使用 H2 单库测试（测试环境不需要双数据源）

## 2. 数据源配置类

- [ ] 2.1 创建 `infrastructure/config/DynamicDataSourceConfig.java` 配置类
- [ ] 2.2 配置主数据源 `user`（默认）
- [ ] 2.3 配置知识图谱数据源 `kg`
- [ ] 2.4 配置 HikariCP 连接池参数（两个数据源各 5-20 连接）

## 3. Mapper 拆分与注解

- [ ] 3.1 创建 `infrastructure/persistence/edukg/mapper/` 目录
- [ ] 3.2 将知识图谱 Mapper 放入 `edukg/mapper/` 包下（KgTextbookMapper, KgChapterMapper, KgSectionMapper, KgKnowledgePointMapper, KgTextbookChapterMapper, KgChapterSectionMapper, KgSectionKPMapper, KgSyncRecordMapper）
- [ ] 3.3 为所有 edukg Mapper 添加 `@DS("kg")` 注解
- [ ] 3.4 修改 `AiEduPlatformApplication.java`：拆分 `@MapperScan` 为两个（business + edukg）

## 4. Repository 事务适配

- [ ] 4.1 为 `KgSyncAppService` 的 `syncFull()` 方法添加 `@Transactional("kg")`
- [ ] 4.2 为 `KgNavigationAppService` 的查询方法添加 `@Transactional("kg")`（只读事务）
- [ ] 4.3 为 `KgKnowledgeSystemAppService` 的查询方法添加 `@Transactional("kg")`
- [ ] 4.4 为 `KgNeo4jService` 添加缓存配置（Redis 不受数据源影响）

## 5. Flyway 迁移

- [ ] 5.1 创建 `db/migration/user/` 目录，将现有 `V1__Init_Demo_Users.sql` 移入
- [ ] 5.2 创建 `db/migration/kg/` 目录
- [ ] 5.3 创建 `V1__Init_Knowledge_Graph.sql`（7 张表 + 索引）
- [ ] 5.4 创建 `FlywayKgConfig.java`：第二个 Flyway Bean，连接 `ai_edu_kg`
- [ ] 5.5 在 `application.yml` 中配置 `spring.flyway-kg` 参数

## 6. 验证与测试

- [ ] 6.1 编写双数据源启动测试（验证两个 HikariCP 池都初始化）
- [ ] 6.2 编写 Mapper 路由测试（验证 UserMapper 走 user 库，KgTextbookMapper 走 kg 库）
- [ ] 6.3 编写事务隔离测试（验证 `@Transactional("kg")` 正确绑定 kg 数据源）
- [ ] 6.4 编写 Flyway 迁移测试（验证 kg 库表创建成功）
- [ ] 6.5 端到端验证：启动应用 → 触发同步 → 验证数据写入 `ai_edu_kg`