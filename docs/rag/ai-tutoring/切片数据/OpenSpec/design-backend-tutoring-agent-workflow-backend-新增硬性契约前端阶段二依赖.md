# design-backend-tutoring-agent-workflow-backend

> summary: 新增前端阶段二依赖的decide事件时序稳定契约
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 新增硬性契约（前端阶段二依赖）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend
> 类别：架构设计

---

## 新增硬性契约（前端阶段二依赖）

**decide 事件时序稳定**：前端 SENDING 期连续消费 decide 阶段 agent 事件做 live 走查，序列 `perceive→analyze→plan→decide→meta` 不得重排、不得丢序。当前 filter 透传满足；后续改 decide 消费链路必须回归此序列。
