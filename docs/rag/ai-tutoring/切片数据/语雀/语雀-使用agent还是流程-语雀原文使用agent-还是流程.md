# 语雀-使用agent还是流程

> summary: 面试问答检索：AI答疑采用Workflow而非LLM Agent的设计结论
> 权威度: 0.7 ｜ 来源: 语雀 ｜ 锚点: 语雀原文：使用agent 还是流程
> 模块: ai-tutoring ｜ 节: 语雀-使用agent还是流程
> COS路径: rag-slices/ai-tutoring/语雀/语雀-使用agent还是流程-语雀原文使用agent-还是流程.md
> 类别：架构设计

---

# 语雀原文：使用agent 还是流程

> 来源: 语雀 业务实施→AI答疑→方案设计→使用agent还是流程 (doc 279938375, 3976字)
> 核心结论: AI答疑是 Workflow（确定性编排），不是 LLM Agent。自适应学习才是 agent 的主场。

---

**Q: ai答疑里面有 agent 的编排吗**

**A: 没有——这个设计里刻意不采用 LLM agent 编排。** 但要先把概念说清楚，因为"有没有 agent"取决于你问的是哪种"agent"。
