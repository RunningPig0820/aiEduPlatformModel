# ActionMeta 这个契约字段怎么设计的？为什么说它为将来升级预留了空间？

> summary: ActionMeta 这个契约字段怎么设计的？为什么说它为将来升级预留了空间？
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: ActionMeta 这个契约字段怎么设计的？为什么说它为将来升级预留了空间？
> 模块: ai-tutoring ｜ 节: Agent架构
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-57-Agent架构-ActionMeta这个契约字段怎么.md
> 类别：架构设计

## 回答

**核心结论**：ActionMeta 是 Java 护栏审批的依据，字段围绕"动作决策 + 评估 + 掌握度"三层设计，且为阶段 2 升级预留了空间。

**分层展开**：
- **顶层硬信号**（Java 据此放行）：type（动作闭集）、reason（决策理由）、new_question（switch 新题）、end_reason（收尾原因）、summary（收尾总结）、safety_flag（高危标记）、degraded（兜底降级标记）。
- **嵌套软信号**：eval（correct 判对/error_type 错因/emotion F7 七态/exercise_complete 独立解出）、mastery_signals（题型粒度 mastered/practicing/struggling）。
- **为什么预留空间**：① eval/Decision 是独立子结构——将来可单独绑定函数调用，契约不变；② degraded 兜底信号——Java 监控降级频次，工程质量可观测；③ 工具 API 早定形状——阶段 2 升 LangGraph 时把 decide 换成 agent 决策循环，ActionMeta 契约不动、迁移成本低。
- **平铺契约**：type/new_question/end_reason/safety_flag 在顶层，eval 嵌套——与 api.md 契约一致，Java/Python 两侧对齐。
- **追问点**："safety_flag 谁执行？" → Python 只标记，Java 执行终止（TERMINATED + 无 token 流）——裁判在 Java。
