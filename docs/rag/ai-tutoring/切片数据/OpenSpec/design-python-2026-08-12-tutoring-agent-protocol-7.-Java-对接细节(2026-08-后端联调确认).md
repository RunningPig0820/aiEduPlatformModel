# design-python-2026-08-12-tutoring-agent-protocol

> summary: 明确 tutoring agent 对接 Java 的各类细节规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 7. Java 对接细节(2026-08 后端联调确认)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol

---

### 7. Java 对接细节(2026-08 后端联调确认)

- **memory 事件归属: Java 发,Python 不发占位**。Python generate 流只有 meta/agent(generate)/token*/done;Java 在真实落库(掌握度/图谱点亮/归档)完成后发 `agent(memory)`。避免双发。
- **decide 重试/超时(流式后)**: 仅"未收到任何 SSE 事件"时(连接阶段)可重试 1 次(无副作用);已收到 agent 事件后失败 → 不重试,透传 error,Java 降级。超时 = 等待 meta 事件到达的超时。
- **guardrail/memory 触发点**: guardrail = Java 护栏审批通过后、调 generate 前(文案"安全把关",detail 可带拒绝摘要);memory = Java 落库完成后(文案"记忆更新")。
- **短路/兜底分支流式**: is_new_question 短路、degraded 兜底均走同一 SSE 流(meta 携带对应 ActionMeta),Java 从 meta 取 type 走护栏,逻辑不变。
- **decide 流中错误**: Python 发 `event: error` → Java 透传前端,**不重试**(已发部分 agent 事件,重试会重发);对外 40004"网络波动",会话保持。
