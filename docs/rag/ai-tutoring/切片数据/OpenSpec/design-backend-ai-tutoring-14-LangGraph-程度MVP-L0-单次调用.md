# design-backend-ai-tutoring

> summary: 面试问AI答疑MVP的LangGraph方案，答用L0单次调用
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 14. LangGraph 程度：MVP = L0 单次调用
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-14-LangGraph-程度MVP-L0-单次调用.md
> 类别：未来演进

---

### 14. LangGraph 程度：MVP = L0 单次调用

**决定**：MVP 用 **L0 单次调用**——decide 一次调用输出 action 元数据（用 LangChain `with_structured_output` 做 schema 约束），generate 一次调用流式输出正文。**无 agent 循环、无中间工具回调**。护栏拒绝时由 Java 重决策/降级（不依赖 agent 重规划）。

**演进（阶段 2）**：升级 L1/L2 LangGraph 多步 agent——增加工具集（查薄弱点、出变式题等，工具 = Java 内部接口），agent 在循环中自然处理护栏拒绝重规划。工具接口在 MVP 已按 Java 内部 API 预留，升级为低摩擦。
