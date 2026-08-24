## Context

当前组织域已有 `t_department` 表实现通用部门树（parent_id + department_path），但 K12 教育场景下的行政班（学段→年级→班级）虽然层级结构类似，却需要额外的教育业务属性（学段编码、年制、年级编码、入学年份等）。本设计在最小化变更的前提下，复用 `t_department` 管理行政班树形结构，新增 `t_department_edu` 扩展表存储教育属性。

## Goals / Non-Goals

**Goals:**
- `t_department` 新增 `department_type` 字段，区分 `ORG`（普通部门）和 `ADMIN_CLASS`（行政班节点）
- 新增 `t_department_edu` 表，以 `dept_id` 反向关联 `t_department`，存储学段、年制、年级编码、入学年份
- 行政班层级（学段→年级→班级）复用 `t_department.parent_id`，不新建层级表
- 新增 `DepartmentType`、`DeptEduType`、`StageYearCode` 值对象
- 基于讨论确认了 `t_department_edu` 的字段子集和填充规则

**Non-Goals:**
- 不修改现有 Class/Grade 实体的行为（它们是单独的领域概念，不影响行政班方案）
- 不引入 `class_type`（当前无此业务需求）
- 不引入 `layer_type`（教学分层太复杂，后续视需要再加）
- 不引入新表管理行政班层级（直接复用 parent_id）

## Decisions

### 1. 复用 t_department 而非新建 t_admin_class 表

**选择**: 在 `t_department` 加 `department_type` 字段 + 新建 `t_department_edu` 扩展表。

**原因**: 行政班的学段→年级→班级树形结构与部门树完全一致，`parent_id` + `department_path` 已覆盖全部层级需求。新建独立表反而导致代码重复和不一致风险。

**备选方案**: 新建 `t_admin_class` 独立表 — 需重新实现整套树逻辑（路径计算、父子查询、排序），代价太大。

### 2. 教育属性用扩展表 (department_id 反向关联)

**选择**: `t_department_edu.dept_id` 指向 `t_department.id`，由业务表持有关联（反向关联）。

**原因**: 
- 不侵入 `t_department` 表结构（仅加一个类型字段）
- 学段/年级/班级三级节点共用同一张扩展表，减少表数量
- 不同节点类型按 `dept_type` 区分，字段填充遵循明确的规则
- 查询灵活：先查 department 树，再按需 JOIN 扩展属性

### 3. 学段/年级/班级三种类型用同一张扩展表

**选择**: `dept_type` 区分 3(学段)/4(年级)/5(班级)，各字段按类型选择性填充。

| dept_type | 含义 | 填充字段 | 空字段 |
|-----------|------|---------|--------|
| 3 | 学段节点 | stage_code, stage_year_code | grade_code, enrollment_year |
| 4 | 年级节点 | stage_code, stage_year_code, grade_code, enrollment_year | — |
| 5 | 班级节点 | stage_code, stage_year_code, grade_code, enrollment_year | — |

### 4. grade_code 直接复用现有 GradeLevel (1-12)

**选择**: `t_department_edu.grade_code` 存储 1-12 数字编码，与现有 `GradeLevel` 值对象一致。

**原因**: 项目已有完整的 GradeLevel 体系（1-6 小学，7-9 初中，10-12 高中），不需要再造一套编码。前端展示「一年级」时由 GradeLevel 推算。

### 5. stage_year_code 定义

**选择**: 精简版年制编码，仅覆盖 K12：

| 编码 | 含义 | 年数 |
|------|------|------|
| 4 | 小学六年制 | 6 |
| 5 | 初中三年制 | 3 |
| 7 | 高中三年制 | 3 |

不引入 1(小小班)、2(小班) 等学前教育编码。

## Risks / Trade-offs

- [字段稀疏] 同表三类型导致部分字段为空 → 业务上通过 dept_type 明确区分填充规则，QueryDSL/MyBatis 查询时按类型过滤
- [行政班与现有 Class 实体概念重叠] 现有 Class 实体有 GradeLevel、SchoolYear，行政班 t_department_edu 也有 grade_code、enrollment_year → 本期互不影响，后续若需关联可加 dept_id 桥接
- [department_path 计算] 新增行政班类型后，路径计算逻辑不变（仍按父ID拼接），但需确保所有节点使用相同规则

## Migration Plan

1. Flyway 脚本 `V5__alter_t_department_add_type.sql`: ALTER TABLE t_department ADD COLUMN department_type
2. Flyway 脚本 `V6__create_t_department_edu.sql`: CREATE TABLE t_department_edu
3. 现有 `t_department` 记录的 `department_type` 默认值 `ORG`，不影响已有功能
4. 回滚：删除 `t_department_edu` 表 + 删除 `department_type` 列，现有代码不受影响（Department 实体会适配新字段但向下兼容）

## Open Questions

- 行政班 API 的 school 级别查询是否需要额外索引？（待性能测试确认）
