# 分析-08-Java后端网关与SSE中继-业务链路
> summary: Java网关与SSE中继业务链路
> 来源: 切片 ｜ 锚点: 业务链路
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/rag-system/代码/分析-08-Java后端网关与SSE中继-业务链路.md
> 类别：业务流程
> target: 开发对账

---

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

**文字链路复述**：前端以 camelCase 契约发起 `POST /api/rag/assistant/ask`（命令含 question/sessionId/currentProject/topK/stream/history）；请求先进 `RagAssistantController.requireStudent` 角色硬门——只有会话 role=="STUDENT" 才放行，非 STUDENT/无 session 直接抛 403「仅学生可访问此助手」，不进 RAG、不调 LLM、不产生 trace。放行后 `RagAssistantAppService.ask` 生成 traceId（UUID）、先给前端前置一条 permission 事件（role/allowed/traceId，camel），再经桥把命令转 snake_case 调 Python。Python 无状态引擎逐事件产出 pipeline_events（intent → clarify/switch → rewrite → rerank → boundary/token* → done，不含 permission）；桥做原始 SSE 中继并防御性过滤 permission、60s 超时、失败抛 TutoringAgentException；应用层 `rebuildEvent` 逐事件用 SNAKE_MAPPER 读 snake、CAMEL_MAPPER 写 camel 重建前端契约（done 校验 traceId 一致，对不上仅告警），旁路 doOnNext 挂 captureRerankBlocks/captureIntentCategory/persistRound(落库)/scheduleGradeOnDone(打分)。最终前端按契约收到 permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done 全 camelCase 事件。

其余非流式/代理端点全部先过角色门再转发 Python：`/ask/sync` 是桩替（硬编码占位，不调 Python）；`/source?path=` 查看原文代理；`/eval/report` 评估报告并入 realConversation；`/eval/run` 异步重评测（幂等）；`/guide?currentProject=` 开始引导底座池（0 token）；`/sessions/{id}/close` Redis 置 closed 并读回累计 token/轮数结算；`/turns/{traceId}` 读 done camel 快照做断线补查。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§业务描述与业务场景 / §职责 / §高层业务调用链）
