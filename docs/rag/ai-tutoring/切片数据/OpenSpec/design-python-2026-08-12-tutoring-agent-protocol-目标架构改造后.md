# design-python-2026-08-12-tutoring-agent-protocol

> summary: 阐述AI答疑改造后的目标架构与各层职责
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 目标架构(改造后)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> 类别：架构设计

---

## 目标架构(改造后)

```
┌─ 前端 ─────────────────────────────────────┐
└──────────────┬─────────────────────────────┘
               ▼ 透传 agent 事件 / token
┌─ Java(把关 + 流程 + 前端对接 + 数据提供)──────┐
│  ① 中继 Python 的 agent 事件给前端           │
│  ② 发把关事件: agent(guardrail) 安全审批      │
│  ③ 发记忆事件: agent(memory) 掌握度落库/点亮  │
│  ④ 护栏规则: reveal/轮次/安全/换题            │
│  (将来) 提供工具接口: 掌握度查询/保存          │
└──────────────┬─────────────────────────────┘
               ▼ 调用 decide/generate
┌─ Python(答疑子 agent: 决策智能 + 思考展示)─────┐
│  decide(流式):  agent(perceive)→analyze→plan  │
│                 →decide → meta(ActionMeta)    │
│  generate(流式): agent(generate)→ token* →    │
│                 agent(memory)→ done           │
│  (将来) 主动调知识图谱 agent(工具阶段)          │
└──────────────────────────────────────────────┘
```

**将来演进**(本次不实现):

```
主 agent(编排)
  ├── 答疑 agent ← 本次改造的就是它
  ├── 知识图谱 agent(知识点查询/保存/点亮)  ← 将来,答疑通过工具调它
  ├── 错题集 agent                         ← 将来
  └── 批改 agent                           ← 将来
```
