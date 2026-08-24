## Why

当前行政班管理页面（AdminClassManagement.jsx）使用 Mock 学生数据，后端 `AdminClassStudentController` 已完成学生添加和列表查询 API，前端需要对接真实 API 实现学生数据的添加、查看功能。编辑和删除功能前端预留入口（置灰提示"即将上线"），待后端补齐对应能力后再激活。

## What Changes

- 新建 `StudentDrawer.jsx`：学生抽屉表单组件，支持 create（添加）和 view（查看）两种模式，edit（编辑）模式预留但暂不可用
- 修改 `AdminClassManagement.jsx`：替换 Mock 数据为真实 API 调用，增加操作列（查看、编辑、删除），编辑/删除按钮置灰带 tooltip「即将上线」
- 修改 `organization.js`：新增行政班学生 API 接口（getStudentsByDept、createStudent）
- 学生列表展示：姓名、班级、学号、脱敏身份证、家长子列表
- 添加学生表单：学生基本信息（姓名、手机号、身份证号、学号）+ 家长子表单（动态增删，关系类型下拉 + 手机号输入，家长姓名默认手机号后 4 位）
- 查看学生详情：只读抽屉展示完整信息（含家长列表）

## Capabilities

### New Capabilities

- `admin-class-student-ui`: 行政班学生前端交互，包括学生列表展示、添加学生（含多家长绑定）、查看学生详情，编辑/删除预留

### Modified Capabilities

（无修改的现有能力）

## Impact

- **前端组件**：
  - StudentDrawer.jsx（新建）：学生抽屉表单（create/view 模式）
  - AdminClassManagement.jsx（修改）：对接真实 API、增加操作列
- **API 模块**：
  - organization.js（修改）：新增 `getAdminClassStudents`、`createAdminClassStudent`
- **后端 API 依赖**：
  - `GET /api/auth/schools/{schoolId}/admin-classes/{deptId}/students`（获取学生列表）
  - `POST /api/auth/schools/{schoolId}/admin-classes/{deptId}/students`（添加学生）
