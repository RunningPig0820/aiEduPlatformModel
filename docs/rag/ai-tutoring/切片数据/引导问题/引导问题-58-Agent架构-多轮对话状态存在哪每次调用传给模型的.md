# 多轮对话状态存在哪？每次调用传给模型的历史和快照是怎么压缩的？

> summary: 状态在 Java Redis，Python 每次调用接收压缩后的上下文（history 截断 + 快照 top-N + 文本截断）。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: 多轮对话状态存在哪？每次调用传给模型的历史和快照是怎么压缩的？
> 模块: ai-tutoring ｜ 节: Agent架构
> COS路径: ai-tutoring/rag-slices/引导问题/引导问题-58-Agent架构-多轮对话状态存在哪每次调用传给模型的.md
> 类别：架构设计

## 回答

**核心结论**：状态在 Java Redis，Python 每次调用接收压缩后的上下文（history 截断 + 快照 top-N + 文本截断）。

**分层展开**：
- **Java Redis 存什么**：会话历史（逐轮 question/answer）、round_count、answer_request_count、掌握度；Python 无状态，不落会话。
- **每次请求传什么**：history（对话轮次列表，含 image_url）+ mastery_snapshot（KpSnapshot：题型名 + 掌握度）+ subject_hint。
- **上下文压缩三件套**：① truncate_history 保留最近 12 条（防窗口爆炸，当前题目由 history 推断）；② snapshot_top_n 按掌握度升序取 top-10（薄弱优先，让模型关注短板）；③ 生成段单块 text 截断 MAX_GEN_TEXT=1200（防超长块撑爆）。
- **为什么压缩在 Python**：喂给模型前的 prompt 优化是 Python 侧知识——窗口大小、薄弱优先排序、渲染模板都在 Python 单端迭代，放 Java 每次 prompt 优化要跨端同步。
- **追问点**："12 条够吗？" → 决策只需要最近上下文推断当前题目 + 学生状态，12 条覆盖典型引导链；换题靠 Java 信号不靠历史。
