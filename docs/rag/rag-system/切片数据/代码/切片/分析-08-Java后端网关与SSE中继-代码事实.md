# 分析-08-Java后端网关与SSE中继-代码事实
> summary: Java网关SSE中继接口契约代码事实
> 来源: 切片 ｜ 锚点: 代码事实
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/rag-system/代码/分析-08-Java后端网关与SSE中继-代码事实.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

### 1. 端点清单与契约（RagAssistantController）

| 端点 | 方法/路径 | 返回 | 角色门 | 证据 |
|---|---|---|---|---|
| ask | `POST /api/rag/assistant/ask` | `Flux<ServerSentEvent<String>>`（SSE 流式） | requireStudent | Controller:53-57 |
| askSync | `POST /api/rag/assistant/ask/sync` | `ApiResponse<Map<String,Object>>`（非流式，桩替） | requireStudent | Controller:61-65 |
| source | `GET /api/rag/assistant/source?path=` | `Mono<ApiResponse<String>>`（查看原文代理） | requireStudent | Controller:69-73 |
| evalReport | `GET /api/rag/assistant/eval/report` | `Mono<ApiResponse<RagEvalReportDTO>>` | requireStudent | Controller:77-81 |
| evalRun | `POST /api/rag/assistant/eval/run` | `Mono<ApiResponse<RagEvalRunDTO>>`（异步重评测） | requireStudent | Controller:85-89 |
| guide | `GET /api/rag/assistant/guide?currentProject=` | `Mono<ApiResponse<RagGuideDTO>>`（开始引导，可选 currentProject） | requireStudent | Controller:93-99 |
| close | `POST /api/rag/assistant/sessions/{sessionId}/close` | `Mono<ApiResponse<RagCloseDTO>>`（关闭+结算） | requireStudent | Controller:103-107 |
| turn | `GET /api/rag/assistant/turns/{traceId}` | `Mono<ApiResponse<SseDoneDTO>>`（断线补查） | requireStudent | Controller:111-115 |

契约纪律（Controller 类注释 Controller:36-41）：前端→Java 用 camelCase（RagAskCommand）；Java→Python 用 snake_case（桥内转换）；SSE 端点**直接返回** `Flux<ServerSentEvent<String>>`，不包 ResponseEntity（包了会丢泛型、Spring MVC 找不到 converter，HttpMessageNotWritableException 修复）。SSE 端点 MediaType 为 `TEXT_EVENT_STREAM_VALUE`（Controller:53）。

### 2. 角色门 403 逻辑（Controller.requireStudent → TutoringAuth.isStudent）

- `requireStudent(session)`（Controller:117-123）：`TutoringAuth.isStudent(session)` 为 false → `log.info` 记录 `sessionRole`（session==null 时记 null）→ 抛 `ResponseStatusException(HttpStatus.FORBIDDEN, "仅学生可访问此助手")`。
- `TutoringAuth.isStudent`（TutoringAuth:24-26）：`"STUDENT".equals(session.getAttribute("role"))`。角色缺失/无 session → getAttribute 返回 null → `"STUDENT".equals(null)`=false → 403。
- 全局异常处理：`GlobalExceptionHandler.handleResponseStatusException`（GlobalExceptionHandler:91-98）把 ResponseStatusException 转 HTTP 状态码 + body `{code:"403", message:"仅学生可访问此助手"}`（code=HTTP 状态值）。
- **body 传 role 一律忽略**：RagAskCommand（command/RagAskCommand.java）无 role 字段，角色只从 session 读；测试 RAG-GATE-004 明确验证 "TEACHER session + body 带 role=STUDENT → 仍 403"（ControllerTest:109-120）。注意 Controller 的 requireStudent **只查 role**，不像 `TutoringAuth.requireStudent`（TutoringAuth:29-38，供同步业务用）会先校验 `userId` 登录态——RAG 助手网关侧缺 userId 但 role=STUDENT 的会话理论可通过（角色门口径=仅看 role）。

### 3. SSE 事件中继字段（AppService.ask + rebuildEvent）

- traceId 由 Java 入口生成：`UUID.randomUUID()`（AppService:96）。
- **permission 事件仅 Java 前置发**（AppService:97-98, 119-121）：`SsePermissionDTO{role:"STUDENT", allowed:true, traceId}`，camel 写前端，是流的第一个事件；流一开始前端即可拿 traceId（断线补查不依赖 done）。
- 桥**防御性过滤 Python 侧 permission**（Bridge:65）：`.filter(ev -> ev != null && !"permission".equals(ev.event()))`，生产 Python 不产 permission。
- 事件重建 `rebuildEvent`（AppService:446-478）：按 event 类型分发
  - `intent/rewrite/rerank/boundary/clarify/switch/token/done` → `SNAKE_MAPPER.readValue`（snake→DTO）→ `CAMEL_MAPPER.writeValueAsString`（DTO→camel 前端契约）。
  - 未知事件（default，如 Python 流内 `error`）→ `dto=null` → **透传原始**（不阻断链路）。
  - 重建抛 JSON 异常 → 告警 + 透传原始（AppService:470-473）。
- **done traceId 一致性校验**（AppService:463-465）：Python done 回显 trace_id ≠ Java 生成的 traceId → `log.warn` 仅告警**不阻断**（契约定稿）。
- SSE 事件字段（前端契约，全部 camelCase）：
  - `permission` = {role, allowed, traceId}（SsePermissionDTO）
  - `intent` = {anchor, category, switchDetected, ambiguous, candidates, lockedSections, degraded}（SseIntentDTO）
  - `rewrite` = {originalQuestion, rewrittenQuery}（SseRewriteDTO）
  - `rerank` = {blocks:[{blockId, title, summary, filePath, score}]}（SseRerankDTO/SseRerankBlock）
  - `boundary` = {message, reason:"low_confidence"}（SseBoundaryDTO，唯一拒答路径）
  - `clarify` = {message, candidates, default}（SseClarifyDTO，`default` 字段用 `@JsonProperty("default")` 避开 Java 关键字，ClarifyDTO:35-36）
  - `switch` = {fromAnchor, toAnchor}（SseSwitchDTO）
  - `token` = {text}（SseTokenDTO）
  - `done` = {answer, quotedKeys, tokensUsage{promptTokens,completionTokens,cacheHitTokens,totalTokens}, traceId, suggestions, reason}（SseDoneDTO/SseTokensUsageDTO；reason=low_confidence|timeout|null）
  - `SseRejectDTO`（message/reason）为**遗留 DTO**：早期「禁区硬拒答」设计的 reject 事件已被 boundary 取代，当前契约不产出（RejectDTO:14-16 注释）。
- 测试契约期望：permission 数据含 `"traceId"` 且**不含** `trace_id`；intent 含 `"switchDetected"`/`"lockedSections"` 不含 snake；done 含 `"quotedKeys"`/`"tokensUsage"`/`"promptTokens":320`（AppServiceTest:85-113, 126-164）。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§代码事实 1-3）
