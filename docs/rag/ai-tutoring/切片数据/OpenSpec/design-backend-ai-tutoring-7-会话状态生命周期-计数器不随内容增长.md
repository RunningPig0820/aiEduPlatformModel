# design-backend-ai-tutoring

> summary: 解决AI辅导后端会话状态与计数器的设计问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 7. 会话状态：生命周期 + 计数器（不随内容增长）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-ai-tutoring-7-会话状态生命周期-计数器不随内容增长.md
> 类别：业务流程

---

### 7. 会话状态：生命周期 + 计数器（不随内容增长）

- 生命周期（3 个，固定）：`ACTIVE` / `ARCHIVED` / `TERMINATED`
- 护栏计数器（数据，非状态）：`round_count`、`answer_request_count`
- 掌握度快照：上下文字段（**当前题目后端不记录**，由 Python 从 history 推断）

状态数量固定为 3，不随题目数量、对话长度、换题次数增长。**"流程"由 agent 上下文承载（自然语言），Java 只留生命周期与计数器。**
