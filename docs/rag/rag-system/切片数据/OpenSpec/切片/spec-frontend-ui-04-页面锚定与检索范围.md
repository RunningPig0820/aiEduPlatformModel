# 页面锚定与检索范围
> summary: 页面锚定与检索范围
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-frontend-ui-04-页面锚定与检索范围.md
> 类别：架构设计

---

> 检索摘要（业务向）：前端 spec：每次 ask SHALL 携带 currentProject（camelCase，页面 pageCode 映射、缺省 rag-system 全局模式），模块 id 闭集 ai-tutoring/knowledge-graph/question-analysis/rag-system 的 MUST 要求与 scenario 是什么？

### Requirement: 当前页面锚点携带
> 检索摘要：每次 ask 携带 currentProject（camelCase，由页面 pageCode 映射、缺省 rag-system），模块 id 闭集 ai-tutoring/knowledge-graph/question-analysis/rag-system。

每次 ask SHALL 携带 `currentProject`（camelCase，由当前页面 pageCode 经映射得出，缺省 rag-system），告知后端语料池。模块 id 闭集：`ai-tutoring / knowledge-graph / question-analysis / rag-system`。

#### Scenario: 携带页面锚点
- **WHEN** 学生在 AI答疑页发起提问
- **THEN** ask 请求携带 `currentProject=ai-tutoring`

#### Scenario: 映射缺省
- **WHEN** 页面不在映射表
- **THEN** 携带缺省 `rag-system`（全局模式）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（§Requirement 当前页面锚点携带）
