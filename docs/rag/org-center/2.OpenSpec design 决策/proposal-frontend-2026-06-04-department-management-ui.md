## Why

当前学校工作台缺少部门管理功能，教师组织架构无法可视化展示。实际学校运作中，教师归属于各个行政部门（如教务处、学生处），需要部门管理来支持：
- 教师组织架构可视化
- 按部门筛选教师
- 后续按部门分配任务/权限

## What Changes

### 新增功能（本期）
- 组织架构页面：左侧部门树 + 右侧详情面板
- 部门树形展示：支持多级部门展开/折叠
- 部门 CRUD：创建、编辑、删除部门
- 抽屉表单：右侧滑出，用于新增/编辑部门

### 后续补充（依赖后端教师接口）
- 部门成员管理：右侧显示部门教师列表
- 添加教师到部门

### 暂不实现
- 拖拽调整层级
- 部门负责人
- 部门成员角色

## Capabilities

### New Capabilities
- `department-tree-ui`: 部门树形展示（手写递归组件）
- `department-crud-ui`: 部门 CRUD 交互（抽屉表单）

### Modified Capabilities
- `school-workspace-menu`: 新增"组织架构"菜单项

## Impact

### 前端变更
- 新增 5 个组件：DepartmentManagement, DepartmentTree, DepartmentNode, DepartmentDetail, DepartmentDrawer
- 更新 SchoolWorkspaceLayout 菜单配置
- 更新 routes.jsx 路由配置
- 更新 organization.js API 模块