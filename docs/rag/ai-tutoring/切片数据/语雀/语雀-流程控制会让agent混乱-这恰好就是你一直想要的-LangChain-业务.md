# 语雀-流程控制会让agent混乱

> summary: LangGraph agent结合Java护栏的业务架构方案
> 权威度: 0.7 ｜ 来源: 语雀 ｜ 锚点: 这恰好就是你一直想要的 LangChain 业务
> 模块: ai-tutoring ｜ 节: 语雀-流程控制会让agent混乱
> COS路径: rag-slices/ai-tutoring/语雀/语雀-流程控制会让agent混乱-这恰好就是你一直想要的-LangChain-业务.md
> 类别：架构设计

---

## 这恰好就是你一直想要的 LangChain 业务

LangGraph agent + 工具集 + 护栏就是这个答案。Python 侧是一个有智能的答疑 agent（LangGraph 状态图），Java 侧是护栏层（确定性、可测、掌控业务硬规则）。自适应学习（让 agent 根据掌握度决定教什么）也顺势成为可能——只是给 agent 加两个工具（查薄弱点、出变式题），而不用改状态机。

这是一次架构方向级的调整。
