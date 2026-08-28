# rag-assistant-gateway Specification

## Purpose

Java 侧 RAG 项目介绍助手网关：从可信 session 取角色（仅 STUDENT 放行，非学生固定 403 不消耗 token），SSE 白盒事件中继（permission → intent → rewrite → rerank → token → done），trace_id 透传与断线补查，内部调用 Python 引擎。

## ADDED Requirements

### Requirement: 学生角色硬门

系统 SHALL 在 RAG 助手请求入口从可信源（`HttpSession` 或网关解析 Header）获取当前用户角色，禁止信任前端 body 传参；仅当角色明确为 `STUDENT` 时放行进入 RAG 流程，否则返回固定 403 拒绝响应。

#### Scenario: 学生放行

- **WHEN** 已登录学生（session 角色=STUDENT）发送 `POST /api/rag/assistant/ask`
- **THEN** 系统进入 RAG 流程，透传 SSE 白盒事件

#### Scenario: 非学生拒绝

- **WHEN** 已登录用户角色为 TEACHER/ADMIN（或其它非 STUDENT 角色）发送请求
- **THEN** 系统返回固定 403 响应体（如"仅学生可访问此助手"），**不进入 RAG 流程、不调用 LLM、不消耗任何 token、不产生 trace**

#### Scenario: 角色缺失

- **WHEN** 请求无有效会话或角色缺失
- **THEN** 系统返回固定 403 响应体，同样不进入 RAG 流程

### Requirement: SSE 白盒事件中继

系统 SHALL 将 Python 引擎返回的 SSE 事件流按固定时序透传前端：`permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done`，不得重排或丢失。Python 的 `meta`/`done` 内部字段由 Java 消费/重建，不透传原始事件。

#### Scenario: 正常问答时序

- **WHEN** 学生发送问题且流程正常
- **THEN** 前端依次收到 `permission`（角色门结果）→ `intent`（anchor/category/switch/ambiguous/candidates）→ `rewrite`（改写后 query）→ `rerank`（精排 top-K 块）→ `token`（正文流）→ `done`（完整结果）

#### Scenario: 澄清/切换时序

- **WHEN** intent 判定 ambiguous（多候选）或 switch_detected
- **THEN** 前端收到 `intent` 后 `clarify` 或 `switch` 事件，**无 rewrite/rerank/token 流**，随后 `done`

#### Scenario: 范围门低置信过滤时序

- **WHEN** recall 后综合分低于阈值
- **THEN** 前端收到 `rerank`（可为空）后 `boundary` 事件（reason=low_confidence），无 token 流，随后 `done`

### Requirement: 事件契约字段

系统 SHALL 为各 SSE 事件定义稳定 camelCase 契约字段，供前端渲染白盒阶段与引用面板。

#### Scenario: 事件字段齐备

- **WHEN** 各事件产生
- **THEN** `permission` 含 `{role, allowed, traceId}`（trace_id 由 Java 入口生成，流一开始前端即可取，供断线补查）；`intent` 含 `{anchor, category, switchDetected, ambiguous, candidates, lockedSections}`；`rewrite` 含 `{originalQuestion, rewrittenQuery}`；`rerank` 含 `{blocks:[{blockId, title, summary, filePath}]}`；`boundary` 含 `{message, reason}`；`clarify` 含 `{message, candidates, default}`；`switch` 含 `{fromAnchor, toAnchor}`；`done` 含 `{answer, quotedKeys, tokensUsage, traceId, suggestions}`

#### Scenario: snake_case 内部契约映射

- **WHEN** Java 调用 Python 且 Python 返回 snake_case 字段
- **THEN** Java 侧契约 DTO 用 `@JsonProperty` 映射 snake→camel，SSE 事件输出 camelCase（沿用 tutoring 契约纪律，`FAIL_ON_UNKNOWN_PROPERTIES=false`）

### Requirement: trace_id 透传与断线补查

系统 SHALL 在每轮请求入口生成 `trace_id`（同源贯穿 Java/Python 日志），透传 Python 并在 `done` 事件返回；系统 SHALL 提供按 `trace_id` 查询单轮完整结果的接口，供前端断线后补查。

#### Scenario: trace_id 贯穿

- **WHEN** 学生发起一轮问答
- **THEN** Java 生成 `trace_id` 传入 Python，日志两侧同源，`done` 事件携带该 `trace_id`

#### Scenario: 断线补查

- **WHEN** 前端因断线丢失某轮结果，凭 `trace_id` 调 `GET /api/rag/assistant/turns/{trace_id}`
- **THEN** 系统返回该轮完整结果（answer/quotedKeys/tokensUsage/suggestions）或明确"trace 不存在"（超时保留窗口内）

### Requirement: 会话续接基础

系统 SHALL 支持前端回传 `session_id` 以携带当前锚点与轮次上下文到 Python，供 switch/clarify 判定。

#### Scenario: 续接锚点

- **WHEN** 前端回传 `session_id` 且 Python 侧存在该会话状态
- **THEN** intent 判定 `switch_detected` 时以"前端 current_project vs 会话已锚定 project"为依据

#### Scenario: 无会话状态

- **WHEN** `session_id` 缺失或 Python 侧无对应状态
- **THEN** 系统按全新会话处理，锚点取前端 `current_project`（缺失则全局模式）

### Requirement: 显式关闭对话

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
