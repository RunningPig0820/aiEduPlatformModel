# 分析-08-Java后端网关与SSE中继-代码事实-3
> summary: Java网关质量打分与设计机制代码事实
> 来源: 切片 ｜ 锚点: 代码事实-3
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/rag-system/代码/分析-08-Java后端网关与SSE中继-代码事实-3.md
> 类别：架构设计
> target: 开发对账

---

## 代码事实

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

## 设计要点

- **角色门收敛在 Java（D1）**：前端只走 Java 网关，Python 不自己认证、不碰会话、保持无状态；permission 事件由 Java 前置（D-B），Python 生产端点从 intent 开始（assistant.py:549 注释）。非 STUDENT → 固定 403、不进 RAG、不调 LLM、不产生 trace。
- **SSE 中继三层**：桥原始中继（滤 permission）→ 应用层重建（snake→camel，事件 DTO 契约）→ 前端消费；`SNAKE_MAPPER`/`CAMEL_MAPPER` 双 ObjectMapper，`FAIL_ON_UNKNOWN_PROPERTIES=false` 保证字段追加不破坏（契约冻结：字段追加不重排，DoneDTO javadoc）。
- **Java 是会话聚合点（D8/D12）**：每轮 done 过手即累计（session usage + trace 快照 + 质量分），Python 无状态；close 结算累计 token/轮数、turns 断线补查、closed 短路话术全归 Java Redis（TTL 24h 对齐 tutoring）。
- **质量打分是尽力而为旁路**：`scheduleGradeOnDone` 异步（boundedElastic）、失败 Mono.empty 不入累计、无打分器不打断链路——评估 realConversation 与离线 benchmark 并存展示。
- **蛇↔驼双契约纪律**：`@JsonProperty`（RagAskRequest）+ `SNAKE_MAPPER`/`CAMEL_MAPPER` + `@JsonAlias`（eval 报告数字字段）+ `@JsonProperty("default")`（Java 关键字规避）四件套保证前端 camel / 内部 snake 契约各自稳定。
- **容错与降级**：done traceId 不一致仅告警不阻断；重建失败透传原始；Redis 读写失败只告警；桥流式失败冒泡由编排层降级；close/turn 未知 → 10002 明确提示（不静默返回空）。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§代码事实 7/8 / §枚举、常量、配置 / §设计要点）
