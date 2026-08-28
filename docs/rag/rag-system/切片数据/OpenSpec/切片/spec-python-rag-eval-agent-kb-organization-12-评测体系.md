# 评测体系（评测前置：状态机保障评测有效性）
> summary: 评测体系（评测前置）：模块状态机以 evaluated 为终态，语料变更后已索引模块回退 chunked 待重索引，避免用旧索引评测，保证评测集跑在最新语料上。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-eval-agent-kb-organization-12-评测体系.md
> 类别：数据关联

---

### 评测前置：状态机保障评测有效性
> 检索摘要：知识库模块状态机以 evaluated 为终态，语料变更（完善文档被修改）后已索引模块回退为 chunked 待重索引，避免用旧索引评测，保证评测集跑在最新语料上。

系统 SHALL 通过模块状态机保障评测有效性：模块整理状态推进到 `evaluated` 终态后方可评测；某模块完善文档在已索引之后被修改，该模块状态 SHALL 从 `indexed` 回退为 `chunked`（待重索引），避免用旧索引评测。

#### Scenario: 语料变更使索引失效

- **WHEN** 某模块完善文档被修改（已索引之后）
- **THEN** 该模块状态 SHALL 从 `indexed` 回退为 `chunked`（待重索引），避免用旧索引评测

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-eval-agent-kb-organization.md`（§模块清单与状态机）
