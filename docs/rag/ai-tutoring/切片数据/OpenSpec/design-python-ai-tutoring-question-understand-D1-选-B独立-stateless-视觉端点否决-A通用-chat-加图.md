# design-python-ai-tutoring-question-understand

> summary: 面试问答中AI辅导题理解选独立视觉端点的理由
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D1. 选 B（独立 stateless 视觉端点），否决 A（通用 chat 加图）
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-question-understand
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-ai-tutoring-question-understand-D1-选-B独立-stateless-视觉端点否决-A通用-chat-加图.md
> 类别：架构设计

---

### D1. 选 B（独立 stateless 视觉端点），否决 A（通用 chat 加图）

理由（代码级）：

1. **A 要改生产共享网关**：`/api/llm/chat` 被 4+ 场景共用，加 image 支持 = 契约膨胀 + 新增「非视觉模型收到图 → 400 降级」护栏逻辑，回归风险波及无关功能。
2. **A 的视觉模型池实际只有一个**：可对外视觉模型只有 doubao（allowed+vision）；glm-4.6v `allowed=False`。通用 chat 加图 = 给一个模型造通用接口，不划算。
3. **B 复用已验证路径**：decide 看图（`HumanMessage image_url → ChatOpenAI(ark)`）生产已跑通，新端点只是把这条路径 stateless 化 + 瘦 prompt，零新风险。
4. **B 模型写死 → 非视觉模型风险天然隔离**：不靠「按 model 路由 + 护栏」，靠构造上不可能（端点只用 doubao）。
