# design-python-ai-tutoring-question-understand

> summary: 面试问答中AI辅导题理解的实现路径说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D3. 实现 = decide 看图路径 stateless 化
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-question-understand
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-question-understand-D3-实现-decide-看图路径-stateless-化.md
> 类别：架构设计

---

### D3. 实现 = decide 看图路径 stateless 化

- 模型写死 `doubao-seed-2-0-mini-260428`（settings 已有，TUTORING_DECIDE_MODEL 同款）。⚠️ Java 消息写的 "doubao-seed-2-0-lite" 需与方舟控制台实际开通 ID 对齐，Python 侧以 mini-260428 为准。
- 温度 0.3（与 decide 一致，判断要稳）。
- 构造 `HumanMessage(content=[{"type":"text"},{"type":"image_url","url":imageUrl}])`，调 `ChatOpenAI(ark)` —— 与 decide 看图完全同一路径。
- 解析：纯文本返回 → 去编号/bullet 拆行 → 1~5 个；或复用 structured 降级（可选）。LLM 异常/空 → `{topicLabels: []}`。
