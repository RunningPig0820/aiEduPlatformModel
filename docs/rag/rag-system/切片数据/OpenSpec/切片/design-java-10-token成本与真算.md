# token成本与真算

> summary: token成本与真算（design-java-rag-project-intro-assistant）：tokens_usage四字段+include_usage取usage+cache_hit估算、trace_id断线补查、显式close会话累计token、拒答/降级零usage语义
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-10-token成本与真算.md
> 类别：数据存储

---

### D8. tokens_usage + trace_id

> 检索摘要：计费透明：tokens_usage四字段+Java生成trace_id透传Python供断线补查，history前端传最近3轮不落库，turns只存Java Redis，cache_hit取不到tokenizer估算

`done` 事件携带 `tokens_usage{prompt_tokens, completion_tokens, cache_hit_tokens, total_tokens}` + `trace_id`。usage 取流结束 ark 返回(`include_usage`);cache_hit 取不到 → tokenizer 估算标注"估算"。`trace_id` 由 Java 生成透传 Python(同源贯穿日志,Python done 回显),供前端 `GET /api/rag/assistant/turns/{trace_id}` 断线补查。**history 由前端传**(方案 A,2026-08-26:最近 3 轮 `{question, answer, anchor}`,追问展开用——省略主语的"能说的详细一点吗"靠 history 还原,Java 透传 Python 只消费;不落库,刷新后为空=新会话);**turns 只存 Java Redis**(每轮 done 按 trace_id 落 `rag:assistant:trace:{traceId}` TTL 24h,补查读 Redis;Python 不落会话 trace)。
- **为什么**:spec 第 8 条透明计费;tutoring 已改 ark_stream 取 usage,复用。cache_hit 是 doubao prompt 缓存命中计数,用于成本叙事。**history 方案 A(前端传)**:用户确认"不要落库"——前端本就持有每轮 {question, answer, anchor},随 ask 回传即可,Java 不存 session 历史;刷新后前端消息清空则 history 空=新会话(可接受)。turns/trace 归 Java(每轮过手 done,天然聚合点),Python 保持无状态。
- **备选**:不补查接口 → trace_id 是死口(spec 要求"供断线后补查");Python 落 trace JSONL → 破坏无状态边界,弃。

### D12. 显式关闭对话(close)+ 会话累计 token

> 检索摘要：显式关闭对话close：中止在途流+会话置closed+返回会话累计token，区分断连取消异常路径，累计token归Java（Redis rag:assistant:session:{sessionId}:usage TTL24h）

学生可在对话中主动"结束对话":`POST /api/rag/assistant/sessions/{sessionId}/close`(角色门同上,仅 STUDENT)。close 语义:
- **中止在途流**:若该 session 当前有生成流,中止上游 doubao(同 is_disconnected 取消),前端可关连接。
- **结束会话**:session 状态置 closed(Redis),后续同 session_id 的 ask → 固定话术"本轮对话已结束,可开启新对话",不进入 RAG 流程、0 token。
- **返回会话累计 token**:Java 每轮 `done` 后将 `tokens_usage` 累加进 Redis(`rag:assistant:session:{sessionId}:usage`,TTL 24h 对齐 tutoring);close 时读回返回 `{prompt/completion/cache_hit/total}` 会话累计值 + 轮数。**这补上"对话消耗总 token"的缺口**(原来只有每轮)。
- **为什么**:显式 close 与断连取消是两件事——断连是异常路径(仅中止流),close 是学生主动结束(结束会话 + 结算)。累计 token 放 Java(每轮都经过它,天然聚合点),Python 保持无状态。
- **备选**:close 仅前端清空 UI 不发后端 → 无法结算累计 token、session 状态残留;累计 token 放 Python → 破坏无状态边界。

### Requirement: tokens_usage 透明计费（拒答/降级零 usage 场景）

> 检索摘要：范围门拒答或超时降级时tokensUsage各字段为0（未调generate LLM）或仅含实际消耗，boundary路径recall消耗不计入usage展示或单列

目标 D8 已定义 done.tokensUsage 四字段与 cache_hit 估算。本块独有:系统 SHALL 保证**拒答/降级路径的 usage 语义**——WHEN 范围门拒答或超时降级 → THEN `tokensUsage` 各字段为 0(未调 generate LLM)或仅含实际消耗(boundary 路径 recall 消耗**不计入 usage 展示或单列**)。

### Requirement: 会话累计 token（断连未关闭场景）

> 检索摘要：前端断线未显式close时累计值保留在Redis(TTL内)不丢失，续接同sessionId继续累加

目标 D12 已定义 close 结算与 Redis key(`rag:assistant:session:{sessionId}:usage`, TTL 24h)。本块独有:WHEN 前端断线(未显式 close)→ THEN 累计值**保留在 Redis(TTL 内),不丢失**;续接同 session_id 继续累加。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§D8/D12/§补充 resilience-tokens_usage透明计费/§补充 resilience-会话累计token断连）
