## Why

学校组织架构需要将教职工与行政部门关联，实现人事管理。当前已完成行政组织树（Department）的开发，现在需要在此基础上添加教职工管理功能，支持教职工与行政部门的关联关系。

教职工本质上是"用户与部门的关联关系"，用户基本信息（姓名、手机号）存储在用户域，组织域只存储关联关系。添加教职工时需要与用户域联动：通过手机号查询用户，如果不存在则自动创建用户，再创建组织关联关系。

## What Changes

- 新增教职工关联关系（OrgTeacher），只包含：用户ID、所属行政部门ID、所属学校ID
- 新增教职工与部门的多对一关联（一个教职工属于一个部门）
- 新增教职工添加接口，支持：
  - 提交用户基本信息：姓名、手机号
  - 与用户域联动：通过手机号查询用户域是否存在用户，不存在则自动创建用户
  - 用户域负责手机号唯一性校验
  - 选择所属行政部门
- 新增教职工查询接口（聚合查询）：按部门、按学校查询，返回完整信息（关联关系+用户基本信息）
- 新增教职工 CRUD 接口：
  - 添加：查询/创建用户 + 创建关联关系
  - 查询：聚合查询返回完整信息
  - 修改：只修改所属部门（用户信息在用户中心修改）
  - 删除：只删除关联关系，不删除用户域数据

## Capabilities

### New Capabilities

- `org-teacher-management`: 教职工组织架构管理，包括教职工的添加、查询、修改、删除，以及与行政部门的关联关系管理。通过聚合查询整合用户域基本信息，实现完整的教职工信息展示。

### Modified Capabilities

（无修改的现有能力）

## Impact

- **组织域 (ai-edu-domain/organization)**：新增 OrgTeacher 实体（只包含关联关系）、OrgTeacherRepository 接口
- **组织域基础设施 (ai-edu-infrastructure/organization)**：新增 OrgTeacherPO、OrgTeacherRepositoryImpl、数据库迁移脚本
- **组织域应用层 (ai-edu-application/org)**：新增 OrgTeacherAppService（包含聚合查询逻辑）、DTO 和 Command
- **组织域接口层 (ai-edu-interface/api/org)**：新增 OrgTeacherController
- **跨域依赖**：需要调用用户域接口：
  - 手机号查询用户（findByPhone）
  - 创建用户（createUser）
  - 批量查询用户基本信息（findByIds）
- **数据库**：ai_edu_org 新增 t_org_teacher 表（只存储关联关系）