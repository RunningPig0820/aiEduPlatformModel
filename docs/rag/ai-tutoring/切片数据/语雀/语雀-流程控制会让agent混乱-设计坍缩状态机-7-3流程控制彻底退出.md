# 语雀-流程控制会让agent混乱

> summary: 面试问答中，说明状态机简化为3种，流程控制彻底退出
> 权威度: 0.7 ｜ 来源: 语雀 ｜ 锚点: 设计坍缩：状态机 7 → 3，流程控制彻底退出
> 模块: ai-tutoring ｜ 节: 语雀-流程控制会让agent混乱

---

## 设计坍缩：状态机 7 → 3，流程控制彻底退出

```
原来的设计（流程控制）：                        新的设计（受限 agent）：
┌───────────────────────────┐              ┌───────────────────────────┐
│ 7 个状态：NEW/CLARIFYING/  │              │ 会话生命周期（3 个）:       │
│ GUIDING/REVEALING/        │              │   ACTIVE / ARCHIVED /     │
│ SUMMARIZING/ARCHIVED/     │              │   TERMINATED              │
│ TERMINATED                │              │ 护栏计数器（数据，非状态）:  │
│ turn-router 扩状态分支     │              │   round_count             │
│ 换题/回旧题分支            │              │   answer_request_count    │
└───────────────────────────┘              └───────────────────────────┘
        ↓ 变 ↓
Python 4 个端点：                          Python：答疑 Agent（LangGraph）
  intent/socratic/eval/extract              系统提示：苏格拉底教学法
  每次 Java 调一个                          Agent 在封闭工具集内自由决策顺序

Java 状态机 + 路由                           护栏：工具执行点硬检查（Java）
  ↑ 这是正在爆炸的东西                        ↑ 这才是"限制功能"
```
