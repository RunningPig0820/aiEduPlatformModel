# design-backend-ai-tutoring

> summary: 面试问答：AI答疑采用agent+护栏模式，Java与Python服务分工明确
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-ai-tutoring-Context.md
> 类别：架构设计

---

## Context

AI 答疑是学生端核心体验：引导式解答而非直接给答案，答疑中渐进确认学生知识点掌握度，按知识点 key 落库，联动知识图谱点亮。

关键认识：**对话天然是 agent 形态**——学生不会按预设流程走（中途换题、问概念、要答案、闲聊、"我不会"）。经多轮讨论确认：**不做流程状态机控制**（用状态机控制对话分支会导致状态爆炸），改为**能力受限的 agent + 工具护栏**：Python 侧是纯智能的答疑 agent（决策 + 生成），Java 侧是平台（认证网关 + 护栏 + 数据 + 基础设施）。Python 不直接碰 MySQL / KG / COS，一切数据操作经 Java 域服务。

微服务分工：Java API 网关（认证 / 会话 / 路由）+ 答疑域服务（护栏 / 落库 / 图谱 / COS 归档）为一方；Python 答疑 agent（`ai-edu-ai-service` **现有 LLM 服务内的独立模块**，不单独起服务，Java 仍按服务边界调用）为另一方，只做智能判断，暴露 `decide` / `generate` 两个端点。
