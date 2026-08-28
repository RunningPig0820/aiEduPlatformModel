# 分析-08-Java后端网关与SSE中继-业务与流程
> summary: Java网关与SSE中继业务与流程
> 来源: 切片 ｜ 锚点: 业务与流程
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/interview/rag-system/分析-08-Java后端网关与SSE中继-业务与流程.md
> 类别：业务流程
> target: 面试项目问答

---

## 业务描述与业务场景

学生页面内「RAG 项目介绍助手」的白盒问答：学生提问 → **Java 网关**做角色硬门与 SSE 事件中继 → **Python 无状态引擎**产出白盒事件流（intent/rewrite/rerank/generate…）→ Java 把事件重建为前端 camelCase 契约并透传；同时 Java 承担会话结算（Redis 累计 token、close、turns 补查）、查看原文代理、评估报告/重跑/开始引导代理，以及真实对话 LLM 质量打分（并入评估报告 realConversation 区段）。

区别于 08-21 面试 demo（role 走 body、四业务页）：本模块是**学生**角色、只讲 RAG 项目自身，角色走可信 HttpSession，Python 保持无状态（D-D 定死），turns/close/累计 token 全部归 Java Redis。

## 职责

按组件职责划分：

- **Controller 层**（8 个 REST 端点）：对外暴露 ask 流式提问、ask/sync 非流式、查看原文、评估报告、评估重跑、开始引导、关闭会话结算、断线补查 8 类接口；统一做**角色硬门 requireStudent**——非 STUDENT 会话固定 403。
- **AppService 层**（会话编排核心）：SSE 事件中继重建（Python snake_case → 前端 camelCase）、permission 前置事件、Redis 会话累计 / close 结算 / turns 补查、eval/guide 代理、真实对话质量打分编排。
- **Bridge 层**（Java→Python 桥）：基于 WebClient 把 ask 做 SSE 原始中继（滤 permission），source/eval/report/eval/run/guide 做非流式转发。
- **质量打分器**：复用 LLM 网关按 4 维度打 0-5 分，异步旁路，不阻塞 SSE 回答链路。
- **WebClient 配置**：拼 baseUrl + 内部鉴权 token（x-internal-token），5s 连接超时 + 60s 响应超时。
- **会话角色判定**：只认 HttpSession 里的 role=="STUDENT"，body 传 role 一律忽略。
- **内部契约/DTO**：Java→Python 用 snake_case 序列化；前端 SSE 事件用 camelCase 契约。
- **通用 COS 文件存储**：上传/下载/删除/签名 URL，**不在 RAG source 代理链路上**（见对账要点）。

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

**文字链路复述**：前端以 camelCase 契约发起 ask；请求先进角色硬门——只有会话 role 为 STUDENT 才放行，否则固定 403，不进 RAG、不调 LLM、不产生 trace。放行后应用层生成 traceId（UUID）、先给前端前置一条 permission 事件，再把命令转 snake_case 调 Python 无状态引擎；Python 逐事件产出 pipeline_events（intent → clarify/switch → rewrite → rerank → boundary/token* → done，不含 permission）；桥做原始 SSE 中继并过滤 permission、60s 超时、失败抛异常；应用层逐事件把 snake 重建为 camel 前端契约（done 校验 traceId 一致，对不上仅告警），旁路挂 rerank 块捕获/意图捕获/落库/打分。前端最终按 permission → intent → (clarify|switch) → rewrite → rerank → (boundary) → token* → done 全 camelCase 收到事件。

其余非流式/代理端点全部先过角色门再转发 Python：/ask/sync 是桩替（硬编码占位）；/source 查看原文代理；/eval/report 评估报告并入 realConversation；/eval/run 异步重评测（幂等）；/guide 开始引导底座池（0 token）；/close 置 closed 并读回累计 token/轮数结算；/turns 读 done camel 快照断线补查。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§业务描述与业务场景 / §职责 / §高层业务调用链）｜ `4.完善文档/08-*.md`
