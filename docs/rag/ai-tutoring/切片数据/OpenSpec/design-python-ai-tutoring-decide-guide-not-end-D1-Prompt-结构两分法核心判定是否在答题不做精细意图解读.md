# design-python-ai-tutoring-decide-guide-not-end

> summary: 设计Python decide的两分法核心判定prompt结构
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D1. Prompt 结构：两分法核心判定（是否在答题），不做精细意图解读
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> 类别：开发难点

---

### D1. Prompt 结构：两分法核心判定（是否在答题），不做精细意图解读

`_DECIDE_SYSTEM` 把分类简化为**是否在答题**的两分法——decide 无法确定学生每句话的确切意图（想结束/闲聊/抱怨状态），只判断与当前答题是否相关：

| 学生输入 | 判定 | 行为 |
|---|---|---|
| **在答题**（作答/答错/答偏/求助/提问/追问，无论对错） | 引导解题 | `hint`（只推一步）或 `approach`（卡住/求助给思路大纲），`eval.correct=false` 可填 `error_type`，会话 ACTIVE |
| **不在答题**（闲聊/状态表达/离题/纯打招呼/非数学/无法确定） | 引导回题 | `concept`（正常回应、接住学生、拉回题目），会话 ACTIVE，绝不 end |

**唯一例外**：学生表达结束的意思非常明确（"我不做了""结束""再见"）才 `end(ABANDONED)`。prompt 内保留否定硬规则："任何在答题的内容（无论对错、是否跑偏）绝不输出 `end`、绝不输出 `reveal`"——堵死"答错误终"与"答错误 reveal"两个 bug 源。
