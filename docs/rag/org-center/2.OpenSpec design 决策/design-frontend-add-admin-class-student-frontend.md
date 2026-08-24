## Context

当前 AdminClassManagement.jsx 页面已完成行政班树（学段→年级→班级）的管理交互，右侧学生列表使用 Mock 数据展示。后端 `AdminClassStudentController` 已暴露两个端点：
- `POST /api/auth/schools/{schoolId}/admin-classes/{deptId}/students` — 添加学生
- `GET /api/auth/schools/{schoolId}/admin-classes/{deptId}/students` — 查询学生列表

后端新增/删除/修改 API 暂未实现（设计文档 Non-Goals 明确「本期只做添加」），因此前端编辑/删除按钮预留入口但置灰禁用。

参考模式：DepartmentManagement + TeacherDrawer 的「左侧树 + 右侧列表 + 抽屉表单」架构。

## Goals / Non-Goals

**Goals:**
- 学生列表从 Mock 数据切换为真实 API 调用，点击左侧行政班树节点筛选学生
- 添加学生：右侧抽屉表单，输入学生基本信息（姓名、手机号、身份证号、学号）+ 家长子表单（动态增删）
- 家长子表单：每条包含关系类型下拉（父亲/母亲/监护人）+ 手机号输入，家长姓名自动取手机号后 4 位
- 查看学生详情：右侧只读抽屉展示完整信息（含脱敏身份证和家长列表）
- 编辑按钮：可见但置灰，hover 显示 tooltip「即将上线」
- 删除按钮：可见但置灰，hover 显示 tooltip「即将上线」
- 添加成功后本地更新列表（不刷新整个页面）

**Non-Goals:**
- 不实现学生信息的编辑提交（后端 API 未就绪）
- 不实现学生删除提交（后端 API 未就绪）
- 不确定行内编辑 — 只通过抽屉表单
- 不支持搜索/筛选（姓名/手机号模糊搜索需用户域支持）
- 不修改现有 AdminClassDrawer（树节点管理不受影响）

## Decisions

### D1: 抽屉组件设计 — 新建 StudentDrawer.jsx

**选择**: 新建独立 `StudentDrawer.jsx`，三种模式 `create | view | edit`。样式风格与 `TeacherDrawer.jsx` 保持一致（右侧抽屉，w-80，遮罩层）。

**create 模式字段**:
| 区域 | 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| 学生信息 | 姓名 | 文本输入 | 是 | — |
| 学生信息 | 手机号 | 文本输入 | 是 | 11 位，正则 `^1[3-9]\d{9}$` |
| 学生信息 | 身份证号 | 文本输入 | 是 | 18 位，正则 `^\d{17}[\dXx]$` |
| 学生信息 | 学号 | 文本输入 | 否 | — |
| 家长列表 | 关系类型 | 下拉选择 | 是 | 父亲/母亲/监护人 |
| 家长列表 | 手机号 | 文本输入 | 是 | 11 位，姓名自动取后 4 位 |

**view 模式**: 全部只读展示：姓名、手机号、脱敏身份证、学号、班级、入学日期、状态、家长列表。

**edit 模式**: 预留，内容与 create 相同但实际不会触发（按钮置灰）。

**备选方案**: 复用 TeacherDrawer 并通过 props 切换字段。
**选择理由**: 学生有家长子表单（动态增删），与 TeacherDrawer 差异太大，独立组件更清晰。

### D2: 家长子表单交互

**选择**: 在学生基本信息下方显示「家长信息」区块，每条家长为一行：`[关系类型下拉] [手机号输入] [×删除]`，底部 `[+ 添加家长]` 按钮动态追加。

- 家长姓名字段由前端从手机号后 4 位自动生成（如 `13800001234` → `1234`），不展示单独输入框
- 提交时组装为 `parents: [{ name: "1234", phone: "13800001234", relationship: "父亲" }]`
- 最少 0 个，最多不限制（后端校验由后端负责）

**备选方案**: 弹出独立弹窗添加家长。
**选择理由**: 内联子表单减少操作步骤，直观展示所有家长信息。

### D3: 编辑/删除按钮策略

**选择**: 按钮在操作列可见但置灰（`opacity-50 cursor-not-allowed`），hover 时通过 `title` 属性显示 tooltip「即将上线，敬请期待」。

```
列表行操作列：  [👁] [✏️灰] [🗑灰]
                查看  编辑   删除
              active  灰禁   灰禁
```

**选择理由**: 明确告知用户功能规划，避免疑惑「为什么没有编辑删除？」。与后端 Non-Goals 保持一致。

### D4: 列表表格列设计

**选择**: 6 列表格 — 姓名 | 班级 | 学号 | 身份证（脱敏） | 家长 | 操作。

**家长列渲染**:
- 多条家长垂直排列（子列表），每行格式：`关系类型 姓名 手机号`
- 无家长显示 `—`
- 表格行高随家长数量自适应

**备选方案**: 家长单独一列只显示人数，hover 展开详情。
**选择理由**: 用户明确要求家长列表在表格内直接展示，一目了然。

### D5: API 接口设计

**选择**: 在 `organization.js` 新增两个接口：

```js
// 查询行政班学生列表
getAdminClassStudents: (schoolId, deptId) =>
  request.get(`/auth/schools/${schoolId}/admin-classes/${deptId}/students`),

// 添加学生
createAdminClassStudent: (schoolId, deptId, data) =>
  request.post(`/auth/schools/${schoolId}/admin-classes/${deptId}/students`, data),
```

**选择理由**: 遵循现有 API 模块的路径模式（与教师 API 一致），路径对应后端 `AdminClassStudentController` 的 `@RequestMapping`。

## Risks / Trade-offs

### R1: 后端编辑/删除 API 时间不确定
- **风险**: 前端预留按钮长时间置灰，用户可能持续反馈
- **缓解**: 与后端明确排期，同步沟通进度

### R2: 家长姓名仅用手机号后 4 位
- **风险**: 同名风险（不同手机号后 4 位可能相同），家长列表不够直观
- **缓解**: 当前业务场景家长人数 ≤3，不会造成混淆；后续可改为后端查用户域返回真实姓名

### R3: 身份证号前端透传明文
- **风险**: 前端日志或网络拦截可能泄露身份证明文
- **缓解**: 后端做 AES 加密存储，前端不存储；后续可加 HTTPS + 传输加密

## Migration Plan

1. 新建 `StudentDrawer.jsx`（不影响现有功能）
2. 修改 `organization.js` 新增 API 接口
3. 修改 `AdminClassManagement.jsx` 切换真实 API + 添加操作列
4. 部署：前端独立部署，无需数据迁移
5. 回滚：恢复 Mock 数据即可（git revert）

## Open Questions

- 后端编辑/删除 API 预计何时提供？（决定前端按钮激活时间）
- 家长姓名默认「手机号后 4 位」是否可接受，还是需要后端返回真实姓名？
