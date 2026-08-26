# 语雀-使用agent还是流程

> summary: 面试问语雀AI答疑的技术选型，答混合演进方案
> 权威度: 0.7 ｜ 来源: 语雀 ｜ 锚点: 建议：混合演进
> 模块: ai-tutoring ｜ 节: 语雀-使用agent还是流程
> COS路径: ai-tutoring/rag-slices/语雀/语雀-使用agent还是流程-建议混合演进.md
> 类别：架构设计

---

## 建议：混合演进

1. MVP 保持 workflow（苏格拉底引导，快、稳、成本低），但 Python 侧从一开始就用 LangChain 的 with_structured_output + 模块化场景，为后续 agent 化留好接口。
2. 阶段 2 升级为受限 agent：把"下一步动作"交给 LangGraph 决策循环，动作集先放 4-5 个，跑通后再扩。

这样既拿到一个能上线的 MVP，又有一个真正用上 LangChain agent 能力的第二阶段目标。
