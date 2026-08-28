## ADDED Requirements

### Requirement: 页面权限标签

系统 SHALL 为每个页面/ chunk 标注权限标签（如学生端/教师端/管理员），并随检索结果携带。

#### Scenario: chunk 携带权限

- **WHEN** 检索命中某 chunk
- **THEN** 该结果的 metadata 中 SHALL 包含其 `permissions` 权限标签

### Requirement: 权限门前置校验

系统 SHALL 在会话开始时校验「当前页所需权限点 vs 当前角色」：有权限才继续检索/生成；无权限返回权限提示，不检索不生成。

#### Scenario: 有权限放行

- **WHEN** 当前角色满足当前页权限点
- **THEN** 系统 SHALL 放行进入检索与生成

#### Scenario: 无权限拒绝

- **WHEN** 当前角色不满足当前页权限点（demo 中切换角色演示）
- **THEN** 系统 SHALL 返回"该页面需要 XX 权限"提示，且不执行检索/生成

#### Scenario: demo 默认最高权限

- **WHEN** demo 会话使用默认学生账号
- **THEN** 学生账号 SHALL 拥有最高权限，权限门对全部页面放行（机制保留可切换演示）
