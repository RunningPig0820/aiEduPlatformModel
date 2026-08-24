## Context

当前系统的组织域（Organization bounded context）已存在于 `com.ai.edu.domain.organization`，但学校组织的管理和权限管控能力尚未完善。需要在现有组织域基础上，构建以学校为核心的权限管控体系。

## Goals / Non-Goals

**Goals:**
- 建立学校组织作为权限管控基础单元
- 定义清晰的数据模型：学校实体、学校-用户关联、学校属性（名称/图标/类型/学段）
- 搭建 DDD 四层层骨架：Domain 层聚合根 + Application 层用例 + Infrastructure 层持久化 + Interface 层 API
- 规划清楚功能模块边界，标注哪些本期开发、哪些之后开发、哪些不开发

**Non-Goals:**
- 本期不实现教职工管理、学生管理、学年学期管理等具体功能（仅搭建骨架）
- 不实现钉钉同步、乐课网同步等外部集成
- 不实现复杂的角色权限体系（之后开发）

## Decisions

1. **学校组织作为独立聚合根**
   - `SchoolAggregate` 作为组织域的核心聚合根，封装学校组织的所有业务规则
   - 学校内部包含学段（SchoolStage）作为值对象，不独立作为实体

2. **权限管控通过 School-User 关联表实现**
   - 新建 `school_user` 关联表，记录用户与学校的关联关系及角色
   - 用户登录后根据关联学校确定可访问的功能范围
   - 与现有 Spring Security 集成，在 SecurityContext 中注入学校 ID

3. **数据模型设计**
   - `school` 表：id, name, icon_url, type, stages(json), status, created_at, updated_at
   - `school_user` 表：id, school_id, user_id, role_type, created_at
   - 现有 `school`、`class`、`grade` 表可能需要 Flyway 迁移

4. **保持 DDD 领域纯净**
   - Domain 层仅定义聚合根、值对象、Repository 接口
   - Persistence 层通过 JPA + MyBatis-Plus 实现

## Risks / Trade-offs

- [数据迁移风险] 现有学校表结构可能与新模型冲突 → 通过 Flyway 脚本渐进式迁移
- [权限耦合风险] 学校权限与其他域权限模型可能不一致 → 定义统一的权限拦截器接口，各域通过 SPI 扩展
- [学段存储方式] JSON 存储 vs 关联表 → 本期选择 JSON（学段数量少、查询简单），后续如需按学段聚合查询再拆表

## Migration Plan

1. 创建 Flyway 迁移脚本：`V{version}__create_school_and_school_user.sql`
2. 部署新代码，Flyway 自动执行迁移
3. 回滚：保留旧表结构，仅通过软开关控制新逻辑

## Open Questions

- 学校类型枚举值需要与产品确认（公立/私立/培训机构等）
- 学段枚举值确认（小学/初中/高中/大学等）
- 是否需要支持一个用户关联多个学校
