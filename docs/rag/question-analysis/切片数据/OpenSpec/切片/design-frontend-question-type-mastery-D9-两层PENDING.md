# 两层 PENDING

> summary: 两层 PENDING 拆枚举不混用：识别态/掌握度态/知识点关联态三层枚举分开，识别失败不查掌握度。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-D9-两层PENDING.md
> 类别：开发难点

---

### 决策 9：两层 PENDING 拆枚举，不混用

> 检索摘要：两层 PENDING 拆枚举不混用：识别态/掌握度态/知识点关联态三层枚举分开，识别失败不查掌握度。

| 枚举 | 语义 | 取值 |
|---|---|---|
| `analyze-status` | 题型识别态 | `RESOLVED` / `PENDING`（题型没认出来） |
| `mastery-status` | 掌握度态 | `MASTERED` / `PRACTICING` / `CONSOLIDATING` / `NOT_STARTED`（练过与否） |
| `kp-status` | 知识点关联态 | `CONFIRMED` / `UNCONFIRMED`（本期断联，预留） |

**为什么**：`analyze-question` 的 PENDING（题型没认出来）和 `getMastery` 的 PENDING（题型练了但知识点待确认）语义不同，混用会导致「识别失败被当成待确认」。拆开后：识别失败 → 走候选/空态，不查掌握度；识别成功 → 查掌握度四态。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§决策 9：两层 PENDING 拆枚举，不混用）｜ 语雀-决策记录.md D14 ｜ 完善文档 02-题型分析主流程怎么走.md
