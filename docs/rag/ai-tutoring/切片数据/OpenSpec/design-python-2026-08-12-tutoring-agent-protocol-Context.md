# design-python-2026-08-12-tutoring-agent-protocol

> summary: 介绍AI答疑两调用架构及改造的三个现实原因
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-Context.md
> 类别：项目介绍

---

## Context

AI 答疑当前是**两调用架构**(`ai-tutoring` 变更已落地):`decide`(非流式返回 ActionMeta)→ Java 护栏 → `generate`(流式 SSE)。Java 拥有数据(掌握度/图谱/会话)并做护栏审批;Python 无状态、纯智能。

三个驱动本次改造的现实:

1. **等待黑盒**:每次 1-2 分钟才有答案,用户面对黑盒等待,无法感知进展。
2. **答疑要成为"子 agent"**:最终愿景是**主 agent + 多领域子 agent**(答疑 / 知识图谱 / 错题集 / 批改)。答疑必须先做成接口稳定、可插拔的子 agent,将来主 agent 才能直接编排。
3. **分工原则**:Python = 决策智能(思考/生成),Java = 把关(护栏)+ 流程控制 + 前端对接 + 数据提供。
