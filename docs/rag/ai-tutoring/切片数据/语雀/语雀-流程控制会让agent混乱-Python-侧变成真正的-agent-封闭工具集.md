# 语雀-流程控制会让agent混乱

> summary: 面试问答中，介绍Python侧改为带封闭工具集的agent
> 权威度: 0.7 ｜ 来源: 语雀 ｜ 锚点: Python 侧变成真正的 agent + 封闭工具集
> 模块: ai-tutoring ｜ 节: 语雀-流程控制会让agent混乱
> COS路径: rag-slices/ai-tutoring/语雀/语雀-流程控制会让agent混乱-Python-侧变成真正的-agent-封闭工具集.md
> 类别：架构设计

---

## Python 侧变成真正的 agent + 封闭工具集

```
┌──────────────────────────────────────┬───────────────────────────────────────────┐
│ 工具（封闭能力集，Agent 只能调这些） │    执行点硬护栏（Java，违规直接拒绝）     │
├──────────────────────────────────────┼───────────────────────────────────────────┤
│ evaluate_answer(回答)                │ 每次调用记 round_count；满 20 拒绝        │
│ next_hint()                          │ 生成一条引导，不含答案                    │
│ give_approach()                      │ 给思路；可（第 1 次求答案的出口）         │
│ reveal_answer()                      │ 硬检查 answer_request_count ≥ 2，否则拒绝 │
│ explain_concept(知识点)              │ 简短讲解后拉回当前题                      │
│ switch_question(新题)                │ 旧题归档（end_reason=ABANDONED），开新题  │
│ extract_and_summarize()              │ 会话收尾：提取知识点/薄弱点/总结          │
└──────────────────────────────────────┴───────────────────────────────────────────┘
```

学生说"这题不会"→ agent 自己决定问"请把题目发给我"（不需要 CLARIFYING 状态）；学生贴新题 → agent 自己决定调 switch_question（不需要换题分支）；学生说"答案给我" → agent 想调 reveal_answer，但护栏发现 count=0，工具直接拒绝，agent 只能退而求其次给思路。

> ⚠️ **最新逻辑（2026-08 代码）**：Python 侧**不是 LangGraph agent**——MVP = **L0 单次调用**：`decide`（出动作元数据 type 闭集：hint/approach/reveal/concept/switch/end）+ `generate`（流式正文）两端点，Java 在动作出口审批（`TutoringGuardrailService`）。工具集（evaluate/next_hint/reveal_answer/switch_question…）的落地形态 = **ActionMeta type 闭集 + Java 护栏**，非 agent 自由调工具。`switch_question` 落地 = switch 事件 + 计数重置（**不归档旧题、不开新会话**）。LangGraph 多步 agent 是阶段2（L1/L2，ActionMeta 契约已预留）。
