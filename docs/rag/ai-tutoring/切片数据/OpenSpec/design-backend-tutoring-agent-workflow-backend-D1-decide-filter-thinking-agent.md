# design-backend-tutoring-agent-workflow-backend

> summary: 面试问答：后端工作流中D1阶段事件过滤逻辑调整
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D1. decide filter: thinking + agent
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-tutoring-agent-workflow-backend-D1-decide-filter-thinking-agent.md
> 类别：架构设计

---

### D1. decide filter: thinking + agent

`orchestrate` decide filter（407 行）：

```java
.filter(e -> "thinking".equals(e.event()));                                            // 改前：只中继 thinking
.filter(e -> "thinking".equals(e.event()) || "agent".equals(e.event()));               // 改后：thinking + agent
```

- Python 的 `meta`/`done` 事件仍被消费/丢弃（meta 捕获进 metaSink，done 丢弃）——前端看到的是 Java 重建的 meta。
- 前端收到序列：

  ```
  agent(perceive) → agent(analyze) → agent(plan) → [thinking*] → agent(decide)
      → agent(guardrail) → meta → agent(generate) → token* → agent(memory) → done
  ```

- 注意：`agent(guardrail)` 在 `meta` **之前**（postDecide 先发 guardrail 事件，再进 buildStream）。前端"解析中"状态应以"decide 阶段 agent 已到、meta 未到"为判据，不依赖 meta 紧跟 agent(decide)。
- 换题短路/降级兜底：Python `perceive/analyze/plan` 恒发（`api/tutoring.py` 无条件先发），**无 thinking、无 `agent(decide)`**（`agent(decide)` 只在 thinking 事件时发出，短路/降级仅 yield meta），**仅 meta 仍到**。前端 spec 中"换题/降级轮无 decide agent"场景措辞应改为"无 thinking、无 agent(decide)"。
