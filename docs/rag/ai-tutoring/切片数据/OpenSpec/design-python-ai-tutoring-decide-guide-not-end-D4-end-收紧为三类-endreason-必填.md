# design-python-ai-tutoring-decide-guide-not-end

> summary: 明确AI辅导end的三类触发条件及必填reason规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D4. `end` 收紧为三类 + `end_reason` 必填
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring-decide-guide-not-end
> 类别：开发难点

---

### D4. `end` 收紧为三类 + `end_reason` 必填

| `end_reason` | 触发条件 |
|---|---|
| `COMPLETED` | 学生独立解出（`exercise_complete=true`） |
| `ABANDONED` | 学生**主动明确**表达放弃/结束（"我不做了""结束""再见"） |
| `safety_flag=true` | 高危内容，Java 拦截 |

明确排除：**答错、答偏、求助、与学习无关的闲聊绝不归 `end`**（无关走 `concept` 继续会话）。prompt 的 `end` 动作描述同步收紧。
