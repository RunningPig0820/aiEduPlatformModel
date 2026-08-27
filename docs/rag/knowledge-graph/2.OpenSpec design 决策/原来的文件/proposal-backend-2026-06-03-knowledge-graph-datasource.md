## Why

知识图谱（EduKG）需要将 MySQL 表存储到独立数据库 `ai_edu_kg` 中，与现有业务库 `ai_edu_user` 物理隔离。当前项目仅支持单数据源，需在 Spring Boot 中引入双数据源架构，确保知识图谱数据与用户/作业/题库等业务数据独立管理、独立扩展。

## What Changes

- 引入 `dynamic-datasource-spring-boot3-starter` 实现双数据源（`ai_edu_user` + `ai_edu_kg`）
- 知识图谱相关的 MyBatis Mapper 和 Repository 路由到 `ai_edu_kg` 数据源
- 现有业务 Mapper（User/School/Class 等）继续使用默认的 `ai_edu_user` 数据源
- Flyway 迁移脚本区分两个数据库（`db/migration/user/` + `db/migration/kg/`）
- 知识图谱 7 张表（4 张节点主表 + 3 张层级关联表 + 1 张同步记录表）部署到 `ai_edu_kg`
- `@Transactional` 事务按数据源隔离，跨库操作不支持分布式事务

## Capabilities

### New Capabilities

- `kg-datasource`: 双数据源配置，知识图谱 Mapper 路由到独立数据库 `ai_edu_kg`
- `kg-flyway`: 知识图谱数据库迁移脚本管理，独立于用户库

### Modified Capabilities

<!-- 无已有 Capability 修改 -->

## Impact

- **Infrastructure 层**: 新增 `DynamicDataSourceConfig` 配置类，Mapper 扫描路径拆分（`com.ai.edu.infrastructure.persistence.mapper` 走 user 库，`com.ai.edu.infrastructure.persistence.edukg.mapper` 走 kg 库）
- **Dependencies**: 新增 `dynamic-datasource-spring-boot3-starter` 依赖
- **配置变更**: `application.yml` 数据源配置从单节点改为 `spring.datasource.dynamic` 双数据源
- **Flyway**: 迁移脚本目录结构调整，按库分组
- **不受影响**: 现有业务逻辑、API 接口、认证流程完全不受影响
