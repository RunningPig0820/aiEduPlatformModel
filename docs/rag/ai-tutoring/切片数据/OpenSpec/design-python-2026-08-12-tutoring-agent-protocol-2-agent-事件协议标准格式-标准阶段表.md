# design-python-2026-08-12-tutoring-agent-protocol

> summary: 面试问答中agent事件协议的标准格式与阶段表定义
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 2. agent 事件协议(标准格式 + 标准阶段表)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-2-agent-事件协议标准格式-标准阶段表.md
> 类别：架构设计

---

### 2. agent 事件协议(标准格式 + 标准阶段表)

```json
event: agent
data: {
  "level": "sub",            // sub=子agent | master=主agent(将来)
  "stage": "plan",           // 标准阶段
  "label": "规划引导方案",    // 前端展示文案
  "status": "processing",    // processing | done | error
  "detail": "..."            // 可选(工具结果/决策摘要)
}
```

标准阶段表(所有子 agent 共用):

| stage | 含义 | 现在真实 or 占位 | 发射方 |
|-------|------|----------------|--------|
| `perceive` | 感知输入 | ✅ 真实 | Python |
| `analyze` | 意图/需求解析 | ⚠️ 占位(在 decide 调用内) | Python |
| `plan` | 规划任务 | ⚠️ 占位 | Python |
| `tool` | 工具调用 | 🔮 将来(知识图谱 agent) | Python(预留) |
| `decide` | 决策完成 | ✅ 真实 | Python |
| `generate` | 生成中 | ✅ 真实 | Python |
| `memory` | 记忆更新 | ✅ 真实 | Java(落库) |
| `guardrail` | 安全把关 | ✅ 真实 | Java |

**占位阶段为何入协议**: 协议按最终形态设计——将来 decide 拆多步/工具层上,占位变真实,协议不改。
