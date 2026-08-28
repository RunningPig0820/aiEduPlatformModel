# 引导问题体系
> summary: 引导问题体系
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-frontend-ui-11-引导问题体系.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端 spec：进入时 SHALL 拉取 GET /guide 展示 RAG 定向开始引导 chips（定位/架构/数据流/评测/坑）；每轮 done.suggestions 渲染结束建议 chips，点击后作为新问题重发重走链路的 MUST 要求与 scenario 是什么？

### Requirement: 引导完整（开始引导 + 结束建议）
> 检索摘要：进入时拉取 GET /guide 展示 RAG 定向开始引导 chips；每轮 done.suggestions 渲染结束建议 chips 可点再问重走链路。

面板 SHALL 在进入时拉取 `GET /guide` 展示 RAG 定向开始引导 chips；每轮 `done.suggestions` 渲染结束建议 chips，点击后作为新问题重发重走链路。

#### Scenario: 开始引导展示
- **WHEN** 学生进入面板且尚无会话
- **THEN** 展示 RAG 定向开始引导 chips（定位/架构/数据流/评测/坑）

#### Scenario: 结束建议可点再问
- **WHEN** 一轮 done 返回 suggestions
- **THEN** 渲染建议 chips，点击后作为新问题发起新一轮问答

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（§Requirement 引导完整）
