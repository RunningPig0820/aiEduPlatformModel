# design-python-2026-08-12-tutoring-agent-protocol

> summary: 新增 tutoring agent 流式展示思考过程的方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 8. 保留思考模式,新增 `thinking` 事件(2026-08)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-8-保留思考模式新增-thinking-事件2026-08.md
> 类别：架构设计

---

### 8. 保留思考模式,新增 `thinking` 事件(2026-08)

**背景**: 后端反馈 decide 耗时 17~48s(豆包默认开思考),提议关闭思考降耗时。**产品拍板:不关思考,
把真实推理过程流式展示出去**(decide + generate 都展示)——黑盒等待变可见,符合"思考过程展示"目标。

**实现**: langchain-openai 流式解析会**丢弃 reasoning_content**(实测 additional_kwargs 也为空),故
decide/generate 的流式主路径改为**直连方舟读原始 SSE**(`core/tutoring/ark_stream.py`,httpx),
`reasoning_content` → 新事件 `event: thinking`(与 token 同构的内容流),前端可折叠展示。

**契约影响**: `thinking` 是附加事件,Java 零改动(decide 过滤 meta 时忽略;generate 直接透传)。
降级路径: 原始流失败/args 非法 → 降级现有非流式四段管线(该次无 thinking,罕见)。
