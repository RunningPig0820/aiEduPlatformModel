# 权限与安全
> summary: 权限与安全
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-project-intro-rag-rag-permission-09-权限与安全.md
> 类别: 业务流程

---

### Requirement: 页面权限标签
> 检索摘要：页面权限怎么标注?系统须为每个页面/chunk标注权限标签(学生端/教师端/管理员),检索命中时结果metadata须携带permissions权限标签。

系统 SHALL 为每个页面/ chunk 标注权限标签(如学生端/教师端/管理员),并随检索结果携带。

#### Scenario: chunk 携带权限
- **WHEN** 检索命中某 chunk
- **THEN** 该结果的 metadata 中 SHALL 包含其 `permissions` 权限标签

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-project-intro-rag-rag-permission.md`（§页面权限标签）
