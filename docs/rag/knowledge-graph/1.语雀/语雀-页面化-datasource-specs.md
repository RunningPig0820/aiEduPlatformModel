# 页面化-datasource-specs（语雀原稿）

> 来源：https://www.yuque.com/zhangmin-jrrer/iu9s4m/specs
> 字数：451 ｜ 下载：2026-08-24

## ADDED Requirements

### Requirement: Dual datasource configuration

The system SHALL support two MySQL datasources: `user` (default, `ai_edu_user`) and `kg` (`ai_edu_kg`). The system SHALL use `dynamic-datasource-spring-boot3-starter` for datasource routing. The `user` datasource SHALL be configured as the primary datasource.

#### Scenario: Default datasource routes to user database
- **WHEN** a MyBatis Mapper without `@DS` annotation is called
- **THEN** the query is routed to the `user` datasource (`ai_edu_user`)

#### Scenario: KG datasource routes to kg database
- **WHEN** a MyBatis Mapper with `@DS("kg")` annotation is called
- **THEN** the query is routed to the `kg` datasource (`ai_edu_kg`)

#### Scenario: Strict mode rejects unknown datasource
- **WHEN** a Mapper is annotated with `@DS("unknown")`
- **THEN** system throws a DataSourceNotFoundException at startup

### Requirement: KG Mapper annotation

All knowledge graph MyBatis Mappers SHALL be annotated with `@DS("kg")`. KG Mappers SHALL be placed under the package `com.ai.edu.infrastructure.persistence.edukg.mapper`.

#### Scenario: KgTextbookMapper routes to kg datasource
- **WHEN** `KgTextbookMapper.selectById()` is called
- **THEN** the query executes against `ai_edu_kg` database

#### Scenario: UserMapper routes to user datasource
- **WHEN** `UserMapper.selectByUsername()` is called
- **THEN** the query executes against `ai_edu_user` database (no `@DS` annotation needed, uses default)

### Requirement: Transaction management per datasource

The system SHALL support `@Transactional` binding to specific datasources. KG service methods SHALL use `@Transactional("kg")` to bind to the kg datasource. Cross-datasource transactions SHALL NOT be supported (no distributed transactions).

#### Scenario: KG service transaction uses kg datasource
- **WHEN** a service method annotated with `@Transactional("kg")` executes multiple mapper operations
- **THEN** all operations participate in the same `ai_edu_kg` transaction

#### Scenario: Default transaction uses user datasource
- **WHEN** a service method annotated with `@Transactional` (no datasource specified) executes mapper operations
- **THEN** all operations participate in the `ai_edu_user` transaction

#### Scenario: Cross-datasource operation
- **WHEN** a service method needs to write to both user and kg databases
- **THEN** the service method handles each datasource separately (no single transaction spans both), and compensates on failure at the application layer

### Requirement: Application.yml datasource configuration

The application.yml SHALL define datasources under `spring.datasource.dynamic` with `primary: user` and `strict: true`. Each datasource (user, kg) SHALL have its own url, username, password, and driver-class-name.

#### Scenario: Configuration loads both datasources
- **WHEN** application starts
- **THEN** both `user` and `kg` HikariCP connection pools are initialized

#### Scenario: Missing kg datasource configuration
- **WHEN** the `kg` datasource is missing from `application.yml`
- **THEN** application fails to start with a clear error message

### Requirement: MapperScan separation

The application SHALL configure two separate `@MapperScan` declarations: one for business mappers (`com.ai.edu.infrastructure.persistence.mapper`) and one for KG mappers (`com.ai.edu.infrastructure.persistence.edukg.mapper`).

#### Scenario: Business mappers scanned correctly
- **WHEN** application starts
- **THEN** all mappers under `com.ai.edu.infrastructure.persistence.mapper` are registered as Spring beans and route to `user` datasource

#### Scenario: KG mappers scanned correctly
- **WHEN** application starts
- **THEN** all mappers under `com.ai.edu.infrastructure.persistence.edukg.mapper` are registered as Spring beans and route to `kg` datasource