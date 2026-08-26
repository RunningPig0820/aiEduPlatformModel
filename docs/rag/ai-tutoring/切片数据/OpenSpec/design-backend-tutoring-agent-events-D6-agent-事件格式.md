# design-backend-tutoring-agent-events

> summary: 定义agent事件格式，说明Java侧序列化与方法实现
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D6. agent 事件格式
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events
> 类别：架构设计

---

### D6. agent 事件格式

```json
event: agent
data: {"level":"sub","stage":"guardrail","label":"安全把关","status":"done","detail":"放行: hint"}
```

Java 侧用 `Map` + 现有 `SSE_MAPPER` 序列化（与 `contentToken` 同模式），新增 `agentEvent(stage, label, status, detail)` 帮助方法 + 阶段/文案常量。`level` 恒 `sub`（master 预留）。
