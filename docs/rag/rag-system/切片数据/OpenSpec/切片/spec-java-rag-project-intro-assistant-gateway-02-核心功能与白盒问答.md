# 核心功能与白盒问答（事件字段契约与显式关闭对话）

> summary: 白盒问答核心能力：SSE各事件camelCase字段契约(前端渲染/引用面板)、显式关闭对话返回累计token与closed后固定话术
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-java-rag-project-intro-assistant-gateway-02-核心功能与白盒问答.md
> 类别：操作流程

---

### Requirement: 事件契约字段
> 检索摘要：SSE各事件的camelCase字段契约是什么？permission含role/allowed/traceId，snake_case内部字段怎么映射成camelCase？

系统 SHALL 为各 SSE 事件定义稳定 camelCase 契约字段，供前端渲染白盒阶段与引用面板。

#### Scenario: 事件字段齐备

- **WHEN** 各事件产生
- **THEN** `permission` 含 `{role, allowed, traceId}`（trace_id 由 Java 入口生成，流一开始前端即可取，供断线补查）；`intent` 含 `{anchor, category, switchDetected, ambiguous, candidates, lockedSections}`；`rewrite` 含 `{originalQuestion, rewrittenQuery}`；`rerank` 含 `{blocks:[{blockId, title, summary, filePath}]}`；`boundary` 含 `{message, reason}`；`clarify` 含 `{message, candidates, default}`；`switch` 含 `{fromAnchor, toAnchor}`；`done` 含 `{answer, quotedKeys, tokensUsage, traceId, suggestions}`

#### Scenario: snake_case 内部契约映射

- **WHEN** Java 调用 Python 且 Python 返回 snake_case 字段
- **THEN** Java 侧契约 DTO 用 `@JsonProperty` 映射 snake→camel，SSE 事件输出 camelCase（沿用 tutoring 契约纪律，`FAIL_ON_UNKNOWN_PROPERTIES=false`）

### Requirement: 显式关闭对话
> 检索摘要：学生怎么主动关闭RAG助手对话？关闭返回累计token/轮数，closed后再ask返回什么固定话术、为什么不消耗token？

系统 SHALL 提供 `POST /api/rag/assistant/sessions/{sessionId}/close` 供学生主动结束对话（角色门同上，仅 STUDENT）。关闭时：中止该会话在途生成流；将会话状态置为 closed（Redis）；返回会话累计 tokens_usage 与轮数。关闭后同一 `session_id` 再发起 ask → 返回固定话术"本轮对话已结束，可开启新对话"，不进入 RAG 流程、不消耗 token。

#### Scenario: 关闭对话返回累计 token

- **WHEN** 学生调 `POST /api/rag/assistant/sessions/{sessionId}/close`
- **THEN** 系统中止在途流、置会话 closed，返回 `{sessionUsage: {promptTokens, completionTokens, cacheHitTokens, totalTokens}, rounds}`（累计值）

#### Scenario: 关闭后再次提问

- **WHEN** 会话已 closed，学生用同一 `session_id` 调 ask
- **THEN** 系统返回固定话术"本轮对话已结束，可开启新对话"，不调用 LLM、tokens_usage 为 0

#### Scenario: 关闭不存在的会话

- **WHEN** 调 close 但 session 不存在或已 closed
- **THEN** 系统幂等处理：已 closed 返回当前累计值；不存在返回明确提示（10002），不报错

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-java-rag-project-intro-assistant-gateway.md`（§事件契约字段 / §显式关闭对话）
