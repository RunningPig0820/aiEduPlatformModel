# design-backend-tutoring-agent-events

> summary: 解决重试超时语义定义问题，明确触发条件与超时规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D5. decide 重试/超时语义（流式后）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-tutoring-agent-events-D5-decide-重试-超时语义流式后.md
> 类别：开发难点

---

### D5. decide 重试/超时语义（流式后）

**选择**: `.retry(agentRetry)` 只在 Mono **error** 时触发（连接失败、未收到任何事件）。空流/`event: error`（Mono 正常完成无 meta）→ `.next()` 返回空 → null → 抛 TutoringAgentException，**不重试**（符合"已发事件后失败不重试"）。超时 = `.block(decideTimeout)` 等 meta 事件超时。
