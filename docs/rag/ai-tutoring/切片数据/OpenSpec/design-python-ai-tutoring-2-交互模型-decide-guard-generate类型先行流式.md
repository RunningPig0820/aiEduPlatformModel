# design-python-ai-tutoring

> summary: AI答疑的交互模型为decide→guard→generate流程
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 2. 交互模型:decide → guard → generate(类型先行流式)
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring
> 类别：架构设计

---

### 2. 交互模型:decide → guard → generate(类型先行流式)

> **⚠️ 2026-08 演进(`tutoring-agent-protocol` 变更)**: decide 从非流式改 **SSE 流式**(发 agent 思考阶段 → `meta`(ActionMeta) → `done`),Java 从"读 JSON"改"解析 SSE 提取 meta"。类型先行安全不变(Java 仍在内容流出前审批 type)。事件协议见 `tutoring-agent-protocol`。

**选择**: 一次学生消息 = 两次 Python 调用,中间 Java 护栏:
```
① Java 安全预检 → 组装上下文 → 调 decide(非流式,快)→ action 元数据
② Java 护栏校验 action(答案出口/轮次/换题/收尾)→ 落库副作用
③ 调 generate(流式,按已放行 type)→ SSE 透传
```
**原因**: "类型先行"保证任何内容流入学生前 type 已过护栏——reveal 未授权时正文一个字都不会生成。generate 需要先知道(已放行的)type 才能生成对应内容,因此两段式调用是自然结果,不是过度设计。
**备选**: 一次 LangGraph 流式调用 —— 类型与内容同流,Java 无法在内容流出前审批,违背类型先行安全要求;或图内自审 = 审批搬进 Python,回到"球员当裁判"。阶段 2 升级 LangGraph 时审批仍在 Java。
