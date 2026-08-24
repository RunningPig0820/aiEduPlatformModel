## Why

当前系统缺少以学校为核心的组织管理能力。需要建立学校组织作为权限管控的基础单元，所有后续功能（教职工管理、学生管理、学年学期等）都基于学校组织进行隔离和权限控制。

## What Changes

- 新增学校组织实体，支持学校名称、学校图标、学校类型、包含学段等属性
- 新增学校组织维度的权限管控能力，用户必须关联到具体学校才能访问学校下的功能
- 规划学校下的功能模块边界（本期仅搭建组织域骨架，具体功能后续迭代）：
  - 教职工管理（部门、岗位、学科、角色 — 之后开发）
  - 学生管理（行政班、非行政班、家校设置、毕业记录 — 部分之后开发/部分不开发）
  - 学年学期管理（新学期、校历、作息时间表等 — 之后开发/不开发）
  - 外部组织同步（钉钉、乐课网 — 不开发）

## Capabilities

### New Capabilities
- `school-organization`: 学校组织的 CRUD，包含名称、图标、类型、学段等属性
- `school-permission-scope`: 基于学校组织的权限管控，用户与学校的关联关系
- `org-domain-structure`: 组织域 DDD 骨架搭建（Repository、Aggregate、ValueObject）

### Modified Capabilities
<!-- 无现有能力修改 -->

## Impact

- 新增 bounded context: `com.ai.edu.domain.organization` 下的学校组织相关实体和聚合根
- 新增数据库表：`school`、`school_user` 等
- 组织域现有实体（School、Class、Grade 等）需调整以适配新的权限管控模型
- 用户域需新增与学校组织的关联关系
