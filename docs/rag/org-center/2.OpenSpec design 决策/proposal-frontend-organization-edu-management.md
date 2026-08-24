## Why

当前组织中心已有部门管理和教职工管理功能，但缺少对 K12 教育场景下「行政班」（学段→年级→班级）的支持。后端已完成行政班 API（`/api/admin-classes`），提供基于 `t_department` + `t_department_edu` 的学段/年级/班级树形管理能力。前端需对接此 API，在学校工作台中新增「行政班管理」页面。

## What Changes

- 激活学校工作台侧边栏「学生行政班」菜单项（当前为 pending 状态）
- 新增行政班管理页面，左右分栏布局：左侧树 + 右侧节点详情
- 左侧行政班树，节点只显示名称，hover 显示操作按钮（新增子节点/编辑/删除）
- 右侧节点详情卡片：展示节点属性 + 操作按钮（新增子节点/编辑/删除）
- 新增抽屉表单（AdminClassDrawer），**只显示当前节点类型可编辑的字段**，继承字段不展示
- 学段编码、年制、年级编码下拉数据优先从后端枚举接口获取，API 未就绪时用本地常量降级
- 在 organizationApi 中新增行政班 API 方法（对接 `/api/admin-classes`）
- 新增路由 `/admin/organizations/schools/:id/admin-classes`
- 学生列表本期不做，行政班结构管理完成后处理

## Capabilities

### New Capabilities
- `admin-class-management`: 行政班管理前端页面 — 在学校工作台中基于后端行政班 API 的学段/年级/班级树形管理界面，左右分栏布局，支持树形展示、节点 CRUD、抽屉表单（仅展示可编辑字段）

### Modified Capabilities
<!-- None -->

## Impact

- 新增 API 方法：`src/api/modules/organization.js` 中新增行政班 CRUD 方法
- 新增组件：`AdminClassManagement.jsx`、`AdminClassTree.jsx`、`AdminClassNode.jsx`、`AdminClassDrawer.jsx`
- 修改路由：`src/routes.jsx` 新增行政班路由
- 修改布局：`SchoolWorkspaceLayout.jsx` 激活「学生行政班」菜单项
- 修改导出：`src/pages/organization/index.js`
- 枚举降级常量：页面内定义 stageCode/stageYearCode/gradeCode 映射表
- 后端依赖：`/api/admin-classes` CRUD + 待后端新增枚举接口
