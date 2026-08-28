# 分析-08-Java后端网关与SSE中继-坑与对账
> summary: Java网关SSE中继隐性坑
> 来源: 切片 ｜ 锚点: 坑与对账
> 节: 分析-08-Java后端网关与SSE中继
> COS路径: rag-slices/rag-system/代码/分析-08-Java后端网关与SSE中继-坑与对账.md
> 类别：开发难点
> target: 开发对账

---

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

> 证据：详见 `3.代码/分析-08-Java后端网关与SSE中继.md`（§隐性坑与注意事项）
