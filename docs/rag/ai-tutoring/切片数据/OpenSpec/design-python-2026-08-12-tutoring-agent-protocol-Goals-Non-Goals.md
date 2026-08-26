# design-python-2026-08-12-tutoring-agent-protocol

> summary: 明确AI答疑agent协议改造的目标与非目标
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-Goals-Non-Goals.md
> 类别：项目介绍

---

## Goals / Non-Goals

**Goals:**
- 定义 **agent 事件协议**(标准事件格式 + 标准阶段表),答疑子 agent 全程发射思考阶段事件
- decide 改流式:发射 感知→解析→规划→决策 阶段,`meta` 事件携带 ActionMeta(内容不变)
- generate 加 agent 阶段事件(生成中/记忆)
- Java 发把关/记忆事件(护栏审批、掌握度落库)—— 展示 Java"守门"动作
- 事件协议支持两层嵌套(`level: master/sub`),为主 agent 预留
- 把答疑做成**接口稳定、可插拔的子 agent**(契约是它作为子 agent 的边界)

**Non-Goals:**
- **不实现真工具调用**(知识图谱 agent 是将来独立的子 agent;`tool` 阶段仅协议预留)
- 不建主 agent
- 不建知识图谱 / 错题集 / 批改 agent
- 不改变 ActionMeta 契约内容、不改变生成内容约束(引导式学习不变)
