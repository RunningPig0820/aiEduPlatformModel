# design-python-2026-08-12-tutoring-agent-protocol

> summary: 面试问答中Python tutoring agent的decide接口改SSE流方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 1. decide 从非流式改流式(SSE)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-1-decide-从非流式改流式SSE.md
> 类别：架构设计

---

### 1. decide 从非流式改流式(SSE)

**选择**: `POST /api/tutoring/decide` 响应从 `ActionMeta`(JSON)改为 SSE 流:先发 agent 阶段事件,再发 `meta`(携带 ActionMeta),最后 `done`。**BREAKING**(Java 消费方式从"读 JSON"改为"解析 SSE 流提取 meta 事件")。
**原因**: 决策展示归 Python(分工原则),decide 不流式就无法展示它的思考阶段;将来工具层使 decide 变多步时,流式契约一步到位。
**备选**: decide 保持非流式,Java 发占位标签 —— 契约不动,但阶段展示在 Java,与"Python 控制决策展示"相悖,且将来仍要改。
