# 分析-08 Java后端网关与SSE中继（代码真相）

> summary: Java 网关在 RAG 白盒链路的职责与真相——学生角色硬门（可信 session 取 role、body 传 role 忽略、非 STUDENT 固定 403 不进 RAG 不调 LLM 不产生 trace）、SSE 白盒中继（Java 前置 permission 含 traceId，Python snake_case 事件逐条重建 camelCase 契约，done traceId 不一致仅告警不阻断）、每轮 done 落 Redis（会话累计 token + trace 断线补查快照，TTL 24h）、close 结算累计 token/轮数（幂等、未知会话 10002）、turns 断线补查、source 代理（Java 纯 HTTP 转发 Python，COS 读与前缀白名单在 Python 侧）、eval/guide 代理与真实对话 LLM 质量打分（rag_quality_grade 0-5，异步累计 realConversation）。
> 权威度: 0.8
> 模块: rag-system
> COS路径: rag-source/rag-system/代码/分析-08-Java后端网关与SSE中继.md
> 类别：业务流程

## 业务描述与业务场景

学生页面内「RAG 项目介绍助手」的白盒问答：学生提问 → **Java 网关**做角色硬门与 SSE 事件中继 → **Python 无状态引擎**产出白盒事件流（intent/rewrite/rerank/generate…）→ Java 把事件重建为前端 camelCase 契约并透传；同时 Java 承担会话结算（Redis 累计 token、close、turns 补查）、查看原文代理、评估报告/重跑/开始引导代理，以及真实对话 LLM 质量打分（并入评估报告 realConversation 区段）。

区别于 08-21 面试 demo（role 走 body、四业务页）：本模块是**学生**角色、只讲 RAG 项目自身，角色走可信 HttpSession，Python 保持无状态（D-D 定死），turns/close/累计 token 全部归 Java Redis。

## 职责

| 文件 | 职责 |
|---|---|
| `ai-edu-interface/.../learning/RagAssistantController.java`(125 行) | 8 个 REST 端点 + 角色硬门 `requireStudent`（非 STUDENT 固定 403） |
| `ai-edu-application/.../service/learning/RagAssistantAppService.java`(492 行) | SSE 中继重建（snake→camel）、permission 前置、Redis 会话累计/close 结算/turns 补查、eval/guide 代理、真实对话质量打分编排 |
| `ai-edu-infrastructure/.../ai/rag/RagAssistantBridgeImpl.java`(152 行) | Java→Python 桥（WebClient）：ask SSE 原始中继（滤 permission）、source/eval/report/eval/run/guide 非流式转发 |
| `ai-edu-infrastructure/.../ai/rag/RagQualityGraderImpl.java`(137 行) | 真实对话质量评审：复用 LLM 网关按 4 维度打 0-5 分，异步旁路不阻塞 SSE |
| `ai-edu-infrastructure/.../ai/rag/RagWebClientConfig.java`(63 行) | `ragWebClient` Bean：baseUrl + x-internal-token，5s 连接超时 + 60s 响应超时 |
| `ai-edu-interface/.../learning/TutoringAuth.java`(39 行) | 会话角色判定 `isStudent`（role=="STUDENT"） |
| `ai-edu-domain/.../learning/service/RagAssistantPort.java` | 端口接口（ask/source/evalReport/evalRun/guide 契约） |
| `ai-edu-domain/.../learning/model/contract/RagAskRequest.java` | Java→Python 内部契约（snake_case 序列化，含 history/trace_id/top_k/stream） |
| `ai-edu-application/.../dto/learning/rag/*` | 前端 SSE 事件/DTO 契约（camelCase） |
| `ai-edu-infrastructure/.../file/impl/CosFileStorageServiceImpl.java`(197 行) | 通用 COS 文件存储（上传/下载/删除/签名 URL）；**不在 RAG source 代理链路上**（见对账要点） |

## 高层业务调用链（学生提问→Java角色门→SSE中继→Python引擎→前端白盒）

```
前端 (camelCase) 
  │ POST /api/rag/assistant/ask   RagAskCommand{question,sessionId,currentProject,topK,stream,history}
  ▼
RagAssistantController.requireStudent(session)   [角色硬门: session.role=="STUDENT" 才放行]  Controller:117-123
  │ 非 STUDENT/缺失 → ResponseStatusException(403,"仅学生可访问此助手") → GlobalExceptionHandler → HTTP 403   GlobalExceptionHandler:91-98
  ▼
RagAssistantAppService.ask(command)   [traceId=UUID; 会话已 closed → 短路话术]  AppService:95-103, 377-386
  │ 1) 前置 permission 事件 {role:"STUDENT",allowed:true,traceId} (camel)  AppService:97-98, 119-121
  │ 2) 桥调 Python (RagAskRequest snake_case: question/session_id/current_project/history/trace_id/top_k/stream=true)  Bridge:54-72
  ▼
Python POST /api/rag/assistant/ask → pipeline_events 逐事件 snake_case (无 permission)
  │ intent → (clarify|switch) → rewrite → rerank → (boundary|token*) → done     Python assistant.py:543-652
  ▼
RagAssistantBridgeImpl 原始中继 SSE（过滤 permission 事件；60s 超时；失败→TutoringAgentException）  Bridge:63-71
  ▼
RagAssistantAppService.rebuildEvent 逐事件 SNAKE_MAPPER 读 snake → CAMEL_MAPPER 写 camel    AppService:446-478
  │    done: traceId 一致性校验(对不上仅告警)  AppService:463-465
  │ 旁路 doOnNext: captureRerankBlocks / captureIntentCategory / persistRound(落库) / scheduleGradeOnDone(打分)
  ▼
前端收到: permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done (全部 camelCase)

非流式/代理端点（均先角色门，再转发 Python）:
  /ask/sync → askStages(桩替, 不调 Python)   AppService:432-443
  /source?path=      → 桥 → Python /api/rag/source/{file_path}(读 COS)   Bridge:130-151
  /eval/report       → 桥 → Python 报告 JSON → 并入 Java realConversation  AppService:194-231
  /eval/run          → 桥 → Python 后台跑评测(异步, 幂等)                 AppService:237-245
  /guide?currentProject → 桥 → Python 模块引导底座池(0 token)            AppService:252-260
  /sessions/{id}/close → Redis 置 closed + 读回累计 token/轮数(结算)      AppService:138-167
  /turns/{traceId}    → Redis 读 done camel 快照(断线补查)               AppService:172-180
```

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

契约纪律（Controller 类注释 Controller:36-41）：前端→Java 用 camelCase（RagAskCommand）；Java→Python 用 snake_case（桥内转换）；SSE 端点**直接返回** `Flux<ServerSentEvent<String>>`，不包 ResponseEntity（包了会丢泛型、Spring MVC 找不到 converter，HttpMessageNotWritableException 修复）。

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

### 4. Redis 会话累计 / close 结算 / turns 补查

Redis 键与 TTL（AppService:72-81）：

| 键 | 用途 | TTL |
|---|---|---|
| `rag:assistant:session:{sessionId}:usage` | 会话累计 token+轮数（每轮 done 累加，close 读回） | 24h |
| `rag:assistant:session:{sessionId}:closed` | 会话关闭标志（值 "1"） | 24h |
| `rag:assistant:trace:{traceId}` | 每轮 done camel JSON 快照（断线补查） | 24h |
| `rag:assistant:eval:recent` | 真实对话质量聚合（每轮 LLM 打分累计） | 24h |

- **每轮 done 落库** `persistRound`（AppService:392-405）：done 的 **camel JSON** 直接写 trace 键（`redisService.set(TRACE_KEY_PREFIX+traceId, ev.data(), 24h)`）；再 `accumulateSessionUsage` 把 tokens_usage 读-改-写累加进 session usage 键（prompt/completion/cacheHit/total 各 nvl 0，rounds+1；AppService:408-423）。落库失败只告警，不阻断回答链路。
- **close 结算**（AppService:138-167）：读 usage 键 + closed 键；两者皆 null → `EntityNotFoundException("会话不存在")`（业务码 10002，GlobalExceptionHandler 转 HTTP 404）；closed 为 null → 写 `closed="1"`（TTL 24h）；读回累计 → `RagCloseDTO{sessionId, closed:true, rounds, sessionUsage{prompt/completion/cacheHit/total}}`。**幂等**：已 closed 不重复写标志，仍返回 closed=true。
- **close 后再 ask 短路** `isSessionClosed`（AppService:364-374）+ `closedSessionStream`（AppService:377-386）：`closed="1"` → 返回 permission + done(固定话术 `CLOSED_MSG="本轮对话已结束，可开启新对话。"`，tokensUsage 全 0，suggestions 空)，不调 Python、不落库、不评分。Redis 异常 → 按未关闭处理不阻断（AppService:369-373）。CLOSED_MSG 与 Python `assistant.py:165` 写死常量一致。
- **turns 断线补查**（AppService:172-180）：读 `rag:assistant:trace:{traceId}`，null → `EntityNotFoundException("trace 不存在")`（10002）；否则 `CAMEL_MAPPER.readValue(json, SseDoneDTO.class)` 返回完整结果（answer/quotedKeys/tokensUsage/suggestions）。

### 5. source 代理（查看原文）

- Controller → AppService.source → Bridge.source（AppService:186-188 纯委托）。
- Bridge（Bridge:130-151）：把 filePath 按 `/` 分段逐段 `URLEncoder.encode`（保留目录结构，中文/空格安全）后拼 `/`；**必须用绝对 URI**（`.uri(URI)`，相对路径无 scheme/host 无法与 baseUrl 拼接 → WebClientRequestException）；`GET {baseUrl}/api/rag/source/{encodedPath}`；onStatus 404 → `EntityNotFoundException("原文不存在")`；传输异常 → `TutoringAgentException("RAG 原文服务暂不可用")`。
- **COS 读与前缀白名单在 Python 侧**，不在 Java：Python `api/rag.py:50-72` 的 `/api/rag/source/{file_path:path}` 从 COS 普通桶 `ai-edu-1318177119` 读文件，且 `file_path.startswith(("rag-source/","rag-slices/"))` 才放行（防任意 COS key 读取），读失败 → 404「文件不存在」。Java 的 `CosFileStorageServiceImpl` 是通用文件存储（tutoring transcript 归档等），**不参与 RAG source 代理链路**。

### 6. eval/guide 代理

- **evalReport**（AppService:194-204）：桥返回 Python 原始 snake JSON → `SNAKE_MAPPER.readValue(json, RagEvalReportDTO.class)`，再 `setRealConversation(readRealConversation())` 并入 Java 侧真实对话质量。Python 暂无报告 → 404「暂无评估报告」→ Java `EntityNotFoundException`。`RagEvalReportDTO` 用 `@JsonAlias("hit_at_3")`/`@JsonAlias("precision_at_3")` 收 Python 字段（SNAKE_CASE 策略只把 hitAt3 翻成 hit_at3，数字前不加下划线，ReportDTO:33-35, 49-52）。
- **realConversation 读取**（AppService:207-231）：读 `rag:assistant:eval:recent`，`count==0`/无 key/解析失败 → null（前端不展示该区段）；avgQuality=sum_quality/count、quotedRatio=quoted_count/count、avgLatencyMs=sum_latency_ms/count。
- **evalRun**（AppService:237-245）：桥 POST Python `/eval/run`（异步后台线程跑评测，立即返回），`already_running=true` 幂等非错误；SNAKE_MAPPER 解析 `{running, already_running}` → `{running, alreadyRunning}`。
- **guide**（AppService:252-260）：桥 GET Python `/guide?current_project=`（缺省不发参，Python FALLBACK_MODULE=ai-tutoring 兜底），SNAKE_MAPPER 解析 `{suggestions:[{title,direction}]}` → RagGuideDTO。0 token、非 SSE、不占冻结时序。

### 7. 真实对话质量打分（RagQualityGraderImpl + AppService 编排）

- 触发 `scheduleGradeOnDone`（AppService:311-341）：每个 done 事件异步触发，**跳过条件**=answer 空/blank、reason!=null（boundary/timeout 轮）、category=="问候"（M6 ④ 固定欢迎语 0 token）、`ragQualityGrader==null`（无打分器注入不打断链路）。latencyMs 从 ask 起点计时。
- `formatBlockSummaries`（AppService:293-305）：优先取 quotedKeys 命中的精排块，无命中取全部，最多 5 条，格式 `【标题】摘要`。
- 打分实现 `grade()`（GraderImpl:39-51）：`SCENE="rag_quality_grade"`、`SYSTEM_USER_ID=0L`（Python ChatRequest.user_id 必填 int 哨兵）、`TIMEOUT=20s`；`llmGateway.chat(AiEduChatRequest.of(prompt, 0L, scene))` → 解析 score → `onErrorResume → Mono.empty()`（打分失败不入累计、不打断问答）。
- 评分 prompt（GraderImpl:53-92）：4 维度（相关性/完整性/忠实度/清晰度）0-5 整数；忠实度优先级最高（编造 → 总分最高 2 分）；「无引用片段」特殊规则=忠实度不扣分；要求 JSON `{"score","reason"}`。
- 宽容解析 `parseScore`（GraderImpl:115-136）：容忍 LLM 在 JSON 外套代码块（取首个 `{` 到末个 `}`），score 越界（<0 或 >5）→ 抛异常走兜底 empty。
- 片段摘要截断 `formatSummaries`（GraderImpl:95-112）：`SUMMARIES_MAX_CHARS=800`，按**整块**截断不硬切。
- 累计 `accumulateGrade`（AppService:344-361）：读-改-写 `rag:assistant:eval:recent`（count+1、sum_quality+score、quoted_count+非空引用轮、sum_latency_ms+latencyMs），TTL 24h。打分异步在 `Schedulers.boundedElastic()`（AppService:335-337）。

### 8. 桥与 WebClient 配置

- **RagWebClientConfig.ragWebClient**（WebClientConfig:35-62）：`baseUrl=llmGatewayProperties.getBaseUrl()`、`defaultHeader("x-internal-token", internalToken)`（复用 llm-gateway 内部鉴权模式）；宽容 ObjectMapper（JavaTimeModule + FAIL_ON_UNKNOWN_PROPERTIES=false + 关 WRITE_DATES_AS_TIMESTAMPS）；HttpClient 连接超时 5s、响应超时 60s。
- 桥路径常量（Bridge:40-45）：`/api/rag/assistant/ask`、`/api/rag/source`、`/api/rag/assistant/eval/report`、`/api/rag/assistant/eval/run`、`/api/rag/assistant/guide`，`ASK_TIMEOUT=60s`。
- ask 流式（Bridge:54-72）：POST + `accept(TEXT_EVENT_STREAM)` + `bodyValue(request)`；RagAskRequest 经 `@JsonProperty` 序列化为 snake_case（`session_id/current_project/trace_id/top_k`，AskRequest.java:31-46）；`onErrorResume` → `TutoringAgentException("RAG 助手服务暂不可用")`。**流式不可重试**（重试会重发已透传事件），失败由编排层降级。
- 内部契约 `RagAskRequest`（AskRequest.java）：question/session_id/current_project/history(前端最近 3 轮含 clarify)/trace_id/top_k/stream(桥恒 true)。Python 侧 403（token 缺失/不符）→ Java `onErrorMap` → TutoringAgentException。

### 9. 非流式 /ask/sync 是桩替

- `askStages`（AppService:432-443）：**不调 Python**，硬编码返回 `answer="（桩替）RAG 项目介绍助手链路已通，等待 Python 白盒引擎接入。"` + `stages=["permission","intent","rewrite","rerank","done"]`；用 `LinkedHashMap` 允许 `reason:null`（`Map.of` 不允许 null 值会 NPE）。真实 Python 非流式（`req.stream=false`）Java 侧**未接**——ask() 恒传 `stream=TRUE`（AppService:112），RagAskCommand.stream 字段在 /ask 路径实际被忽略。

## 枚举/常量/配置

| 常量/枚举 | 值 | 位置 |
|---|---|---|
| 模块 id 闭集 | ai-tutoring / knowledge-graph / question-analysis / rag-system | RagAskCommand/AskRequest javadoc；Python query.py:68 同源 |
| SESSION_TTL_HOURS | 24 | AppService:79 |
| 会话/usage/trace/eval Redis 键前缀 | `rag:assistant:session:` / `:usage` / `:closed` / `rag:assistant:trace:` / `rag:assistant:eval:recent` | AppService:72-79 |
| CLOSED_MSG | 「本轮对话已结束，可开启新对话。」 | AppService:81 |
| ASK_TIMEOUT | 60s | Bridge:45 |
| 桥路径 | ask/source/eval/report/eval/run/guide | Bridge:40-44 |
| 角色 | 仅 `"STUDENT"` 放行，其余固定 403 | Controller:117-123 / TutoringAuth:24-26 |
| 业务错误码 | 10002=EntityNotFoundException（EntityNotFoundException 继承 BusinessException，ErrorCode.ENTITY_NOT_FOUND=10002） | ErrorCode.java:14 |
| 内部鉴权 | `x-internal-token` header（baseUrl + internalToken） | WebClientConfig:58 |
| 打分场景 | `rag_quality_grade` / SYSTEM_USER_ID=0L / 20s 超时 / 摘要 800 字上限 | GraderImpl:27-31 |
| 打分维度 | 相关性/完整性/忠实度/清晰度，0-5 整数，忠实度最高优先级 | GraderImpl:56-76 |
| `SseClarifyDTO.default` | `@JsonProperty("default")` 避开 Java 关键字 | ClarifyDTO:35-36 |
| `RagEvalReportDTO` @JsonAlias | `hit_at_3`→hitAt3、`precision_at_3`→precisionAt3 | ReportDTO:35, 51 |
| SSE 端点 MediaType | `produces = MediaType.TEXT_EVENT_STREAM_VALUE` | Controller:53 |
| history | 前端传最近 3 轮 {question,answer,anchor}，Java 透传不落库 | AppService:109 / AskCommand javadoc |

## 隐性坑与注意事项

1. **非流式 /ask/sync 是桩替，不是真实非流式链路**：AppService:432-443 返回硬编码占位话术，不调 Python；真实 Python 非流式能力存在（rag_assistant.py:116-120）但 Java 未接，ask() 恒 stream=true。
2. **close 不中止在途生成流**：D12 设计写「close 中止在途流」，代码只有「置 closed 标志 + 读回累计」；close 与断连取消（Python is_disconnected）是两条独立路径，Java 侧 close 不会掐 Python 上游流（对账要点）。
3. **角色门只查 role、不查 userId**：Controller.requireStudent 走 `isStudent`（TutoringAuth:24-26）只比对 `role=="STUDENT"`，与同步业务用的 `TutoringAuth.requireStudent`（先校验 userId）口径不同；缺 userId 但 role=STUDENT 的会话理论可放行。
4. **SSE 事件重建失败/未知事件透传原始**：未知事件（如 Python 流内 error）与解析失败都按原样透传（snake_case），前端若按 camel 契约解析会拿不到字段——是「不阻断链路」的代价。
5. **Python 降级标记（degraded）不达前端**：Python `recall` 返回 `degraded` 列表但 rerank/done 事件不带（analysis-07 已证）；Java 的 SseRerankDTO 也只有 blocks 字段，无 degraded 字段——前端看不到「这轮是降级」的显式信号。
6. **trace 快照存的是 camel JSON**：persistRound 直接写 `ev.data()`（已重建 camel），turns 用 CAMEL_MAPPER 读回；若 Python 契约升级新增字段，快照 JSON 的 FAIL_ON_UNKNOWN_PROPERTIES=false 会静默丢弃新字段。
7. **Redis 读-改-写非原子**：accumulateSessionUsage/accumulateGrade/close 都是 get→改→set，多轮并发/多实例下可能覆盖丢计数（无 Lua/分布式锁）。
8. **桥 ask 失败不重试**：流式不可重试（Bridge javadoc），Python 挂 → TutoringAgentException 直接冒泡，前端整轮失败（无降级 done）；与 1.6C /query 端点的降级语义不同。
9. **source 代理 Java 侧无前缀白名单**：防任意路径的检查只在 Python（api/rag.py:65-66），Java 桥只做 urlencode 转发；若 Python 端白名单被绕过，Java 无二次拦截。
10. **done 事件 answer 与 token 流的关系**：done.answer 是全量答案（Python assemble_done），token 事件是增量；前端若以 done 为准，token 只作「流式渲染」用；scheduleGradeOnDone 用 done.answer 打分。

## 设计要点

- **角色门收敛在 Java（D1）**：前端只走 Java 网关，Python 不自己认证、不碰会话、保持无状态；permission 事件由 Java 前置（D-B），Python 生产端点从 intent 开始（assistant.py:549 注释）。非 STUDENT → 固定 403、不进 RAG、不调 LLM、不产生 trace。
- **SSE 中继三层**：桥原始中继（滤 permission）→ 应用层重建（snake→camel，事件 DTO 契约）→ 前端消费；`SNAKE_MAPPER`/`CAMEL_MAPPER` 双 ObjectMapper，`FAIL_ON_UNKNOWN_PROPERTIES=false` 保证字段追加不破坏（契约冻结：字段追加不重排，DoneDTO javadoc）。
- **Java 是会话聚合点（D8/D12）**：每轮 done 过手即累计（session usage + trace 快照 + 质量分），Python 无状态；close 结算累计 token/轮数、turns 断线补查、closed 短路话术全归 Java Redis（TTL 24h 对齐 tutoring）。
- **质量打分是尽力而为旁路**：`scheduleGradeOnDone` 异步（boundedElastic）、失败 Mono.empty 不入累计、无打分器不打断链路——评估 realConversation 与离线 benchmark 并存展示。
- **蛇↔驼双契约纪律**：`@JsonProperty`（RagAskRequest）+ `SNAKE_MAPPER`/`CAMEL_MAPPER` + `@JsonAlias`（eval 报告数字字段）+ `@JsonProperty("default")`（Java 关键字规避）四件套保证前端 camel / 内部 snake 契约各自稳定。
- **容错与降级**：done traceId 不一致仅告警不阻断；重建失败透传原始；Redis 读写失败只告警；桥流式失败冒泡由编排层降级；close/turn 未知 → 10002 明确提示（不静默返回空）。

## 对账要点

| 对账分类 | 项 | spec口径 | 代码现状 | 结论 |
|---|---|---|---|---|
| 方案vs实现 | D1 角色门在 Java、禁信 body | spec「从可信 session 取角色，非 STUDENT 固定 403，body 传 role 忽略」 | Controller:117-123 + TutoringAuth:24-26；RagAskCommand 无 role 字段；测试 RAG-GATE-001~004 覆盖 | ✅ 落地 |
| 方案vs实现 | D-B permission 携带 trace_id | permission={role, allowed, traceId}，trace 由 Java 入口生成，Python 无感 | AppService:97-98, 119-121；SsePermissionDTO{traceId}；桥过滤 Python permission | ✅ 落地 |
| 方案vs实现 | D-C sessionId 由前端生成，close 未知→10002 | sessionId 前端 UUID 复用；ask 未知按新会话；close 未知 10002 | RagAskCommand.sessionId @NotBlank；close 双键皆 null → EntityNotFoundException(10002)（HTTP 404）；ask 未知 session 累计从 0 | ✅ 落地 |
| 方案vs实现 | D-D 查看原文走 Java 代理 | GET /source?path=urlencoded 转发 Python，前端不直连 Python | Controller:69-73 → AppService:186-188 → Bridge:130-151（绝对 URI + 逐段 urlencode） | ✅ 落地 |
| 方案vs实现 | D-D source 前缀白名单 / COS 读 | 任务清单提「source 代理(COS 读/前缀白名单)」 | Java 侧**无**白名单、**无** COS 读；白名单（rag-source//rag-slices/）与 COS 读都在 Python api/rag.py:50-72；Java CosFileStorageServiceImpl 是通用存储（tutoring transcript 等），不在 RAG source 链 | ⚠️ 白名单/COS 读在 Python 侧，Java 是纯 HTTP 转发 |
| 方案vs实现 | D12 close 中止在途流 | close 语义含「中止该会话在途生成流」 | close() 仅置 closed 标志 + 读回累计（AppService:138-167），**无在途流中止逻辑**；中止由 Python is_disconnected 负责 | ⚠️ 方案有/代码无（Java close 不掐流） |
| 方案vs实现 | D8 非流式 done 结构 + stages | /ask/sync 返回 done + stages 摘要 | askStages 是 M1 桩替（AppService:432-443 硬编码占位），不调 Python；真实 Python 非流式未接，ask() 恒 stream=true | ⚠️ 桩替（非流式未接真实链路） |
| 方案vs实现 | D8 turns 只存 Java Redis | 每轮 done 按 trace_id 落 `rag:assistant:trace:{traceId}` TTL 24h，补查读 Redis | persistRound 写 camel done JSON（AppService:392-405）+ turn 读回（172-180），TTL 24h | ✅ 落地 |
| 方案vs实现 | D8 history 前端传不落库 | history 最近 3 轮 {question,answer,anchor}，Java 透传 Python，刷新后空=新会话 | command.history → RagAskRequest.history（默认空列表，AppService:109）；RagHistoryItem{question,answer,anchor}；不落库 | ✅ 落地 |
| 方案vs实现 | D12 会话累计 token 归 Java | Java 每轮 done 累加进 Redis，close 读回 | accumulateSessionUsage 读-改-写（AppService:408-423）；close 读回（138-167） | ✅ 落地 |
| 方案vs实现 | 真实对话质量打分 | 评估报告 realConversation 区段（Java 每轮 LLM 打分累计） | GraderImpl 4 维度 0-5 + AppService scheduleGradeOnDone/accumulateGrade + evalReport 并入 | ✅ 落地（Java 侧新增能力） |
| 契约vs实现 | SSE 事件时序与字段 | permission→intent→(clarify\|switch)→rewrite→rerank→(boundary)→token*→done，camelCase | 桥保序中继 + AppService 逐事件重建 camel；测试验证全序与字段（AppServiceTest:126-164） | ✅ 落地 |
| 契约vs实现 | reject 事件 | 早期「禁区硬拒答」design | SseRejectDTO 保留定义但**不产出**（RejectDTO:14-16），唯一拒答路径=boundary low_confidence | ✅ 已废弃（留 DTO 完整性） |
| 方案vs实现 | degraded 标记透传 | Python 注释声明「供 done/boundary 透传 degraded 语义」 | Python rerank/done 事件不带 degraded（analysis-07 已证）；Java SseRerankDTO 无 degraded 字段 | ⚠️ 方案有/代码无（前端拿不到降级信号） |
| 契约vs实现 | CLOSED_MSG 对齐 | close 后 ask 返回「本轮对话已结束，可开启新对话」 | AppService:81 常量与 Python assistant.py:165 一致；closedSessionStream 0 token | ✅ 落地 |

## 已读代码清单

- `ai-edu-backend/ai-edu-interface/src/main/java/com/ai/edu/interfaces/api/learning/RagAssistantController.java`（125 行，全文：8 端点 + requireStudent）
- `ai-edu-backend/ai-edu-interface/src/main/java/com/ai/edu/interfaces/api/learning/TutoringAuth.java`（39 行，全文：isStudent/requireStudent）
- `ai-edu-backend/ai-edu-application/src/main/java/com/ai/edu/application/service/learning/RagAssistantAppService.java`（492 行，全文：SSE 中继/permission/Redis/close/turns/eval/guide/打分编排）
- `ai-edu-backend/ai-edu-infrastructure/src/main/java/com/ai/edu/infrastructure/ai/rag/RagAssistantBridgeImpl.java`（152 行，全文：ask/source/eval/report/eval/run/guide 桥）
- `ai-edu-backend/ai-edu-infrastructure/src/main/java/com/ai/edu/infrastructure/ai/rag/RagQualityGraderImpl.java`（137 行，全文：4 维度打分 prompt/解析/截断）
- `ai-edu-backend/ai-edu-infrastructure/src/main/java/com/ai/edu/infrastructure/ai/rag/RagWebClientConfig.java`（63 行，全文：ragWebClient Bean）
- `ai-edu-backend/ai-edu-infrastructure/src/main/java/com/ai/edu/infrastructure/file/impl/CosFileStorageServiceImpl.java`（197 行，全文：通用 COS 存储，确认不在 RAG source 链）
- `ai-edu-backend/ai-edu-infrastructure/src/main/java/com/ai/edu/infrastructure/ai/LlmGatewayProperties.java`（全文：baseUrl/internalToken）
- `ai-edu-backend/ai-edu-domain/src/main/java/com/ai/edu/domain/learning/service/RagAssistantPort.java` + `RagQualityGrader.java`（端口契约）
- `ai-edu-backend/ai-edu-domain/src/main/java/com/ai/edu/domain/learning/model/contract/RagAskRequest.java` + `RagQualityScore.java` + `RagIntentMeta.java` + `RagHistoryItem.java`（内部契约）
- `ai-edu-backend/ai-edu-domain/src/main/java/com/ai/edu/domain/shared/service/RedisService.java`（Redis 接口）
- `ai-edu-backend/ai-edu-application/src/main/java/com/ai/edu/application/dto/learning/rag/*`（全部 DTO：SseIntent/Permission/Rewrite/Rerank(+Block)/Boundary/Clarify/Switch/Token/TokensUsage/Reject/Done、RagGuide(+Suggestion)/Close/SessionUsage/EvalReport/EvalRun/RealConversation）
- `ai-edu-backend/ai-edu-application/src/main/java/com/ai/edu/application/dto/learning/command/RagAskCommand.java`（前端命令）
- `ai-edu-backend/ai-edu-common/src/main/java/com/ai/edu/common/exception/EntityNotFoundException.java` + `TutoringAgentException.java` + `constant/ErrorCode.java`（10002/40004）
- `ai-edu-backend/ai-edu-interface/src/main/java/com/ai/edu/interfaces/config/GlobalExceptionHandler.java`（403/404/500 转译）
- 测试：`RagAssistantAppServiceTest`（490 行）、`RagAssistantControllerTest`（293 行，RAG-GATE-001~004）、`RagAssistantBridgeImplTest`（438 行）、`RagQualityGraderImplTest`（契约期望）
- 参照材料（对账用，非真值）：`docs/rag/rag-system/2.OpenSpec design 决策/原来的文件/spec-java-rag-project-intro-assistant-gateway.md`、`design-java-rag-project-intro-assistant.md`、`docs/rag/rag-system/3.代码/分析-04-检索编排.md`、`分析-07-API降级与容错.md`
- Python 契约实证（对照）：`ai-edu-ai-service/core/rag/assistant.py`（652 行 pipeline_events）、`ai-edu-ai-service/api/rag_assistant.py`（213 行 端点）、`ai-edu-ai-service/api/rag.py`（source 前缀白名单 + COS 读 50-72）、`ai-edu-ai-service/api/chat.py`（verify_internal_token 27-35）、`ai-edu-ai-service/config/settings.py`（COS 桶/超时）
