> summary: 项目介绍RAG权限门规范spec:每页/chunk标注权限标签(学生端/教师端/管理员)并随检索结果携带;权限门前置校验,会话开始时比对当前页权限点与当前角色,有权限才继续检索生成,无权限返回"该页面需要XX权限"且不检索不生成,demo学生账号默认最高权限机制保留。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-project-intro-rag-rag-permission.md
> 类别: 业务流程

# spec-python-project-intro-rag-rag-permission(项目介绍 RAG 权限门规范)

## 文档说明
> 本文件为原始 spec 文档的 RAG 结构化重构版本。
> ⚠️ 重要提示:本文属于**设计阶段素材**,为 08-21 源头设计,后续被 08-25 spec 部分反转;真实实现请以权威度 0.8 的 canonical 真相源文档与代码为准。本文件独立完整,内容不拆分到外部 canonical 文档。

### Requirement: 页面权限标签
> 状态:⚠️
> 检索摘要:页面权限怎么标注?系统须为每个页面/chunk标注权限标签(学生端/教师端/管理员),检索命中时结果metadata须携带permissions权限标签。

系统 SHALL 为每个页面/ chunk 标注权限标签(如学生端/教师端/管理员),并随检索结果携带。

#### Scenario: chunk 携带权限
- **WHEN** 检索命中某 chunk
- **THEN** 该结果的 metadata 中 SHALL 包含其 `permissions` 权限标签

### Requirement: 权限门前置校验
> 状态:⚠️
> 检索摘要:权限门怎么前置校验?会话开始时校验当前页权限点vs当前角色,有权限才继续检索生成,无权限返回"该页面需要XX权限"且不检索不生成,demo学生账号默认最高权限。

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
