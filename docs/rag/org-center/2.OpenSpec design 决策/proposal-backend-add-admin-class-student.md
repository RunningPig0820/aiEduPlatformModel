## Why

当前行政班树（学段→年级→班级）已完成节点管理，但缺少将学生添加到行政班班级节点的能力。行政班添加学生是一个跨域操作：需要在用户域创建/查询学生用户（含身份证加密存储），同时为每个学生绑定家长（通过手机号自动创建家长用户），最后在组织域创建学生与行政班班级节点的关联关系。

参考已完成 `add-org-teacher` 的跨域集成模式（Gateway ACL + findOrCreate），本次需求是对该模式的深化：从单一用户创建扩展到"学生+多家长"的关联用户创建，并引入身份证敏感数据的 AES 加密。

## What Changes

- **用户域 `t_user` 表**：新增 `id_card` 字段（AES 加密存储）
- **用户域新建 `t_parent_profile` 表**：存储家长-学生关联关系（student_user_id, parent_user_id, relationship）
- **通用层新建 `EncryptUtil`**：AES 对称加密/解密 + 身份证脱敏工具
- **组织域 Gateway 扩展**：`OrgUserGateway` 新增 `findOrCreateStudent()`、`findOrCreateParent()`、`bindStudentParents()` 方法
- **组织域 ACL 模型扩展**：新增 `StudentInfo`、`ParentInfo` 防腐层模型
- **组织域复用 `StudentClass` 实体**：学生与行政班班级节点（Department）的关联关系
- **新建 `AdminClassStudentAppService`**：编排跨域添加流程（验证班级节点 → 创建学生 → 创建家长 → 创建关联 → 绑定家长）
- **新建 `AdminClassStudentController`**：REST API 端点

## Capabilities

### New Capabilities

- `admin-class-student-management`: 行政班学生管理 — 将学生添加到行政班班级节点，支持多家长绑定，跨域编排学生/家长用户创建
- `user-id-card-encryption`: 用户身份证加密 — `t_user` 新增 `id_card` 字段，AES 加密存储，查询时脱敏返回
- `parent-profile-management`: 家长信息管理 — 基于 `t_parent_profile` 表的学生-家长关联关系管理

### Modified Capabilities

- `org-user-gateway`: `OrgUserGateway` 防腐层接口扩展，新增学生和家长相关方法

## Impact

- **用户域 (ai-edu-domain/user)**：User 实体新增 `idCard` 字段，`UserService.createUser` 支持角色参数和 idCard；新增 ParentProfile 实体 + 仓储接口
- **组织域 (ai-edu-domain/organization)**：新增 `StudentInfo`、`ParentInfo` ACL 模型；`OrgUserGateway` 接口扩展 3 个方法
- **通用层 (ai-edu-common)**：新建 `EncryptUtil` AES 加解密工具
- **基础设施 (ai-edu-infrastructure)**：Flyway 迁移 V7（t_user 加 id_card）、V8（t_parent_profile）；新增 ParentProfile 持久化层；`OrgUserGatewayImpl` / `UserDataProvider` 扩展
- **应用层 (ai-edu-application)**：新建 `AdminClassStudentAppService`、`CreateAdminClassStudentCommand`、`AdminClassStudentDTO`
- **接口层 (ai-edu-interface)**：新建 `AdminClassStudentController`
- **数据库**：`ai_edu_user` 库 `t_user` 表变更 + 新增 `t_parent_profile` 表
- **跨域依赖**：组织域 → 用户域（Gateway ACL 模式，与 OrgTeacher 一致）
