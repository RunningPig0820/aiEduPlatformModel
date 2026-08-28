# 分析-08-Java后端网关与SSE中继-坑与对账-2
> summary: Java网关SSE中继方案代码对账复盘
> 来源: 切片 ｜ 锚点: 坑与对账-2
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/rag-system/代码/分析-08-Java后端网关与SSE中继-坑与对账-2.md
> 类别：开发难点
> target: 开发对账

---

## 对账要点（方案 vs 代码 逐条复盘）

**方案 vs 实现**

1. **D1 角色门在 Java、禁信 body**：原始方案「从可信 session 取角色，非 STUDENT 固定 403，body 传 role 忽略」。代码现状 Controller:117-123 + TutoringAuth:24-26，RagAskCommand 无 role 字段，测试 RAG-GATE-001~004 覆盖。✅ 落地——无差异，角色只认 session。
2. **D-B permission 携带 trace_id**：原始方案 permission 由 Java 前置、带 trace，Python 无感。代码现状 AppService:97-98, 119-121，SsePermissionDTO{traceId}，桥过滤 Python permission。✅ 落地——permission 是流首事件，前端开流即拿 traceId。
3. **D-C sessionId 由前端生成，close 未知→10002**：原始方案 sessionId 前端 UUID 复用；ask 未知按新会话；close 未知 10002。代码现状 RagAskCommand.sessionId @NotBlank；close 双键皆 null → EntityNotFoundException(10002)（HTTP 404）；ask 未知 session 累计从 0。✅ 落地。
4. **D-D 查看原文走 Java 代理**：原始方案 GET /source?path= 经 Java 转发 Python，前端不直连 Python。代码现状 Controller:69-73 → AppService:186-188 → Bridge:130-151（绝对 URI + 逐段 urlencode）。✅ 落地。
5. **D-D source 前缀白名单 / COS 读**：任务清单提「source 代理(COS 读/前缀白名单)」落在 Java。实际 Java 侧**无**白名单、**无** COS 读；白名单（rag-source//rag-slices/）与 COS 读都在 Python api/rag.py:50-72；Java CosFileStorageServiceImpl 是通用存储（tutoring transcript 等），不在 RAG source 链。⚠️ **翻转**——白名单/COS 读在 Python 侧，Java 是纯 HTTP 转发；业务影响：安全前置在 Python 单点，Java 无二次拦截。
6. **D12 close 中止在途流**：原始方案 close 语义含「中止该会话在途生成流」。实际 close() 仅置 closed 标志 + 读回累计（AppService:138-167），**无在途流中止逻辑**；中止由 Python is_disconnected 负责。⚠️ **翻转**——方案有/代码无（Java close 不掐流）；业务影响：close 后仍可能收到在途 token/done。
7. **D8 非流式 done 结构 + stages**：原始方案 /ask/sync 返回 done + stages 摘要。实际 askStages 是 M1 桩替（AppService:432-443 硬编码占位），不调 Python；真实 Python 非流式未接，ask() 恒 stream=true。⚠️ **翻转**——桩替（非流式未接真实链路）；业务影响：/ask/sync 是占位话术，非真实答案。
8. **D8 turns 只存 Java Redis**：原始方案每轮 done 按 trace_id 落 `rag:assistant:trace:{traceId}` TTL 24h，补查读 Redis。代码现状 persistRound 写 camel done JSON（AppService:392-405）+ turn 读回（172-180），TTL 24h。✅ 落地。
9. **D8 history 前端传不落库**：原始方案 history 最近 3 轮 {question,answer,anchor}，Java 透传 Python，刷新后空=新会话。代码现状 command.history → RagAskRequest.history（默认空列表，AppService:109）；RagHistoryItem{question,answer,anchor}；不落库。✅ 落地。
10. **D12 会话累计 token 归 Java**：原始方案 Java 每轮 done 累加进 Redis，close 读回。代码现状 accumulateSessionUsage 读-改-写（AppService:408-423）；close 读回（138-167）。✅ 落地。
11. **真实对话质量打分**：原始方案评估报告 realConversation 区段（Java 每轮 LLM 打分累计）。代码现状 GraderImpl 4 维度 0-5 + AppService scheduleGradeOnDone/accumulateGrade + evalReport 并入。✅ 落地（Java 侧新增能力）。

**契约 vs 实现**

12. **SSE 事件时序与字段**：原始方案 permission→intent→(clarify|switch)→rewrite→rerank→(boundary)→token*→done，camelCase。代码现状 桥保序中继 + AppService 逐事件重建 camel；测试验证全序与字段（AppServiceTest:126-164）。✅ 落地。
13. **reject 事件**：早期「禁区硬拒答」design。实际 SseRejectDTO 保留定义但**不产出**（RejectDTO:14-16），唯一拒答路径=boundary low_confidence。✅ 已废弃（留 DTO 完整性）。
14. **degraded 标记透传**：Python 注释声明「供 done/boundary 透传 degraded 语义」。实际 Python rerank/done 事件不带 degraded（analysis-07 已证）；Java SseRerankDTO 无 degraded 字段。⚠️ **翻转**——方案有/代码无（前端拿不到降级信号）；业务影响：前端无法显式提示用户「本轮为降级回答」。
15. **CLOSED_MSG 对齐**：原始方案 close 后 ask 返回「本轮对话已结束，可开启新对话」。代码现状 AppService:81 常量与 Python assistant.py:165 一致；closedSessionStream 0 token。✅ 落地。

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§对账要点）
