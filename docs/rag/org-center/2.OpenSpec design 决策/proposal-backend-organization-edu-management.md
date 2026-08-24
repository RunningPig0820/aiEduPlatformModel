## Why

当前组织域已有 `t_department` 实现通用部门树，但缺少对行政班（学段→年级→班级）这一常见 K12 教育场景的支持。行政班的层级结构天然适合复用 `t_department` 的树形能力，但学段、入学年份、年级编码等教育特有属性需要额外扩展。本期在已有 Department 实体基础上，通过类型区分和扩展表实现行政班管理。

## What Changes

- 在 `t_department` 表新增 `department_type` 字段，区分普通组织部门（`ORG`）和行政班节点（`ADMIN_CLASS`）
- 新增 `t_department_edu` 教育扩展属性表，存储学段、年制、年级编码、入学年份等行政班特有属性
- 新增 `DeptEduType` 枚举（学段/年级/班级三级节点类型）和 `StageYearCode` 年制枚举
- 新增 `DepartmentType` 值对象，区分部门类型
- 行政班 API 复用现有 `DepartmentController` 或新建管控器，支持学段→年级→班级的层级 CRUD
- 行政班节点使用 `t_department` 原生 `parent_id` + `department_path` 管理层级，不再额外建关系表

## Capabilities

### New Capabilities
- `admin-class-management`: 行政班管理 — 基于 `t_department` + `t_department_edu` 的学段/年级/班级树形管理，支持入学年份、学段编码、年级编码、年制等教育属性

### Modified Capabilities
- `org-domain-structure`: `t_department` 新增 `department_type` 字段区分行政班；新增 `t_department_edu` 教育扩展表；新增 `DepartmentType`、`DeptEduType`、`StageYearCode` 值对象

## Impact

- `t_department` 表结构变更（新增 `department_type` 列）→ Flyway 迁移
- 新增 `t_department_edu` 表 → Flyway 迁移
- 新增 Domain 层：`DepartmentType`、`DeptEduType`、`StageYearCode` 值对象，`DepartmentEdu` 实体
- 新增 Infrastructure 层：`DepartmentEduPO`、`DepartmentEduMapper`、`DepartmentEduRepositoryImpl`
- 新增 Application 层：`AdminClassAppService` 行政班应用服务
- 新增 Interface 层：`AdminClassController` REST API
- 现有 `Department` 实体新增 `departmentType` 字段（非侵入式，默认 `ORG` 向下兼容）
