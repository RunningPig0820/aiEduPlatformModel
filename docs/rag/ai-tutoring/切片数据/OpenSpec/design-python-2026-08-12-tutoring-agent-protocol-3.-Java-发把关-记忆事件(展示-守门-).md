# design-python-2026-08-12-tutoring-agent-protocol

> summary: 面试问答中Java需发guardrail和memory事件的要求
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 3. Java 发把关/记忆事件(展示"守门")
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol

---

### 3. Java 发把关/记忆事件(展示"守门")

Java 在它真实执行的动作点发事件:
- **guardrail**: 读完 decide 的 `type` + 计数,过护栏规则(要答案上限/轮次/安全 flag/换题)后发 `agent(guardrail)`。Java 只读 type+count 不看对话(防提示词攻击的核心)。
- **memory**: 收到 mastery_signals,解析 kp_label→URI、落 t_student_kp_mastery、点亮图谱、归档会话后发 `agent(memory)`。

**原因**: Java 的"把关"是真实且关键的平台动作,展示它 = 前端看到"Python 在想、Java 在守门",符合分工原则。
