# 两道门与边界拒答
> summary: 两道门与边界拒答
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-project-intro-rag-rag-permission-08-两道门与边界拒答.md
> 类别: 业务流程

---

### Requirement: 权限门前置校验
> 检索摘要：权限门怎么前置校验?会话开始时校验当前页权限点vs当前角色,有权限才继续检索生成,无权限返回"该页面需要XX权限"且不检索不生成,demo学生账号默认最高权限。

系统 SHALL 在会话开始时校验「当前页所需权限点 vs 当前角色」:有权限才继续检索/生成;无权限返回权限提示,不检索不生成。

#### Scenario: 有权限放行
- **WHEN** 当前角色满足当前页权限点
- **THEN** 系统 SHALL 放行进入检索与生成

#### Scenario: 无权限拒绝
- **WHEN** 当前角色不满足当前页权限点(demo 中切换角色演示)
- **THEN** 系统 SHALL 返回"该页面需要 XX 权限"提示,且不执行检索/生成

#### Scenario: demo 默认最高权限
- **WHEN** demo 会话使用默认学生账号
- **THEN** 学生账号 SHALL 拥有最高权限,权限门对全部页面放行(机制保留可切换演示)

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-project-intro-rag-rag-permission.md`（§权限门前置校验）
