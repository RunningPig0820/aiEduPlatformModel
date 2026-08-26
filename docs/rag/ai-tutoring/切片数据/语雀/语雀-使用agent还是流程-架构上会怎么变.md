# 语雀-使用agent还是流程

> summary: 自适应agent模式与当前workflow的架构差异
> 权威度: 0.7 ｜ 来源: 语雀 ｜ 锚点: 架构上会怎么变
> 模块: ai-tutoring ｜ 节: 语雀-使用agent还是流程
> COS路径: rag-slices/ai-tutoring/语雀/语雀-使用agent还是流程-架构上会怎么变.md
> 类别：架构设计

---

## 架构上会怎么变

| 维度 | 当前 workflow 设计 | 自适应 agent 设计 |
|------|-------------------|-------------------|
| Python 侧 | 4 个无状态 scene 端点 | LangGraph 有状态 agent 循环 + 工具集 |
| 智能位置 | 每一步的内容生成 | 下一步动作的选择（升级了） |
| Java 侧 | 状态机总控流程 | 守门 + 工具 API 提供方（决策权移交） |
| 会话状态 | Java Redis 单源 | Python agent 有状态（LangGraph 检查点）+ Java 守门 |
| LangChain 用量 | 只结构化输出（薄） | agent + tools + memory + 状态图（厚）——真正的 LangChain 业务 |
| 成本/延迟 | 每轮 1 次调用 | 决策 + 执行多次调用（更高，需设上限） |
