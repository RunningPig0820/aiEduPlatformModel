# 会话状态、断线补查的 trace 快照存哪？TTL 多久？

> summary: 会话状态、断线补查的 trace 快照存哪？TTL 多久？
> 权威度: 1.0
> 模块: rag-system
> COS路径: rag-slices/rag-system/引导问题/引导问题-50-数据存储-会话状态断线补查的trace快照存哪TT.md
> 类别：数据存储

---

## 回答

**核心结论**：Java Redis：`rag:assistant:session:{sessionId}:usage`（累计 token+轮数）、`:closed`（关闭标志）、`rag:assistant:trace:{traceId}`（每轮 done camel 快照）、`rag:assistant:eval:recent`（真实对话质量聚合），全部 **TTL 24h**。

**分层展开**：
- **会话累计**：`rag:assistant:session:{sessionId}:usage`——每轮 done 后 `accumulateSessionUsage` 读-改-写累加 prompt/completion/cacheHit/total + rounds+1；close 读回结算（依据：分析-08）。
- **trace 快照（断线补查）**：`rag:assistant:trace:{traceId}`——每轮 done 的 **camel JSON 直接写**（`persistRound`），断线补查 `GET turns/{traceId}` 用 `CAMEL_MAPPER` 读回（依据：分析-08）。
- **关闭标志**：`rag:assistant:session:{sessionId}:closed`——close 置 "1"（幂等），已关闭再 ask 短路固定话术"本轮对话已结束，可开启新对话"（0 token 不调 Python）（依据：分析-08）。
- **真实对话质量**：`rag:assistant:eval:recent`——每轮 done 异步 LLM 打分（4 维度 0-5）累计 count/sum_quality/quoted_count/sum_latency，并入评估报告 realConversation 区段（依据：分析-08）。
- **⚠️ 风险**：Redis 读-改-写非原子（多轮并发/多实例下可能丢计数，无 Lua/分布式锁）（依据：分析-08）。

> 证据：详见 `7. 引导问题/问题列表.md`（第 50 问）｜ `4.完善文档/04-数据流转.md` ｜ `3.代码/分析-08-Java后端网关与SSE中继.md`
