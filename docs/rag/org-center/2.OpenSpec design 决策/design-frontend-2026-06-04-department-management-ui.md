# 组织架构页面设计文档

## 概述

在学校工作台中新增"组织架构"页面，用于管理学校的行政部门（教务处、学生处等）。采用左侧部门树 + 右侧详情面板的布局，支持部门的 CRUD 操作。

## 需求

### 功能需求
- 部门树形结构展示（多级部门）
- 创建、编辑、删除部门
- 通过编辑修改上级部门来调整层级（不支持拖拽）
- 本次仅实现部门管理，教师相关功能后续迭代

### 非功能需求
- 与现有 DaisyUI + Tailwind 风格保持一致
- 手写递归树组件，无额外依赖
- 响应式设计，适配移动端

## 页面布局

```
┌─────────────────────────────────────────────────────────┐
│  组织架构                                    [展开/折叠] │
├──────────────┬──────────────────────────────────────────┤
│ 部门树        │ 右侧详情面板                              │
│              │                                          │
│ ▼ 教务处     │  ┌─────────────────────────────────────┐ │
│   └─教务办   │  │ 教务处                               │ │
│   └─考试中心 │  │ 部门名称：教务处                      │ │
│              │  │ 上级部门：无                          │ │
│ ▼ 学生处     │  │ 教师数量：--                          │ │
│   └─学工办   │  │ 描述：--                              │ │
│              │  └─────────────────────────────────────┘ │
│ [+ 新增根部门]│                                          │
└──────────────┴──────────────────────────────────────────┘
```

## 技术设计

### 路由与入口

**路由：** `/admin/organizations/schools/:id/departments`

**菜单位置：** 学校工作台 → 教职工管理 → 组织架构

```jsx
// SchoolWorkspaceLayout.jsx 菜单更新
{
  label: '教职工管理',
  children: [
    { path: `/admin/organizations/schools/${schoolId}/faculty`, label: '教职工' },
    { path: `/admin/organizations/schools/${schoolId}/departments`, label: '组织架构', status: 'active' },
    { label: '岗位', status: 'pending' },
    { label: '角色', status: 'pending' },
  ]
}
```

### 组件结构

```
src/pages/organization/
├── DepartmentManagement.jsx    # 主页面（左右分栏布局）
├── DepartmentTree.jsx          # 部门树组件（递归渲染）
├── DepartmentNode.jsx          # 树节点组件（单个节点 + 操作按钮）
├── DepartmentDetail.jsx        # 右侧部门详情面板
├── DepartmentDrawer.jsx        # 新增/编辑抽屉表单
└── index.js                    # 导出
```

### API 接口

```javascript
// src/api/modules/organization.js 新增

// 部门管理
getDepartmentTree: (schoolId) =>
  request.get(`/auth/schools/${schoolId}/departments`),

getDepartmentById: (schoolId, id) =>
  request.get(`/auth/schools/${schoolId}/departments/${id}`),

createDepartment: (schoolId, data) =>
  request.post(`/auth/schools/${schoolId}/departments/create`, data),

updateDepartment: (schoolId, id, data) =>
  request.post(`/auth/schools/${schoolId}/departments/${id}/update`, data),

deleteDepartment: (schoolId, id) =>
  request.post(`/auth/schools/${schoolId}/departments/${id}/delete`),
```

### 树形组件设计

**DepartmentNode.jsx 核心逻辑：**

- 递归渲染子节点
- 点击节点名称 → 右侧显示详情
- 点击 `+` → 打开抽屉新增子部门
- 点击编辑 → 打开抽屉编辑当前部门
- 点击删除 → 确认弹窗，有子部门时提示"请先删除子部门"
- 展开/折叠状态本地管理

**样式：**
- 子节点左侧有 border-l 边框线
- 每层缩进 pl-4
- 操作按钮 hover 时显示

### 抽屉表单设计

**DepartmentDrawer.jsx 字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| name | 输入框 | 部门名称（必填） |
| parentId | 下拉选择 | 上级部门（可选，默认根级） |
| sortOrder | 数字输入 | 排序序号（默认 0） |
| description | 文本域 | 部门描述（可选） |

**交互：**
- 新增模式：parentId 可预设（点击节点的+按钮时）
- 编辑模式：回填当前部门数据
- 保存后刷新部门树

## 实现任务

见 tasks.md