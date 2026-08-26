# 坑档案

> summary: 解决答对信号丢失，收紧noRealAnswer判定规则
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J4. 答对信号丢失（score=0 / 直接答对不落库）
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: ai-tutoring/rag-slices/坑档案/坑档案-J4-答对信号丢失score0-直接答对不落库.md
> 类别：开发难点

---

### J4. 答对信号丢失（score=0 / 直接答对不落库）
**1. 问题现象**：学生**直接答对**收尾（END 轮），掌握度却记 0 / 不落库。

**2. 触发流程**：`applyMasteryAndErrors`（`TutoringAppService.java:727`）→ 第 3.1 节信号累计判定（`:734-740`）→ 结算时 `persistQuestionAttempt`。

**3. 根因分析**：修复前 `settlingRound = SWITCH || END || REVEAL` **整轮跳过累计**。但 END 轮有真实 eval（学生答对 `exerciseComplete` 收尾）也被跳过 → rounds 空 → 结算时无信号 → score=0 / 直接答对不落库。本质是**"收尾轮"一刀切跳过，误伤了 END 轮的真实作答**。

**4. 排查过程**：从"直接答对掌握度 0"反推——看结算分支的 settlingRound 判定，发现 END 轮整轮跳过；再确认 END 轮其实携带 eval（答对 exerciseComplete），被误伤。

**5. 解决方案 & 改动点**（`TutoringAppService.java:734-740`）：
```java
boolean noRealAnswer = allowedType == ActionType.SWITCH
        || ((allowedType == ActionType.END || allowedType == ActionType.REVEAL) && action.getEval() == null);
if (!noRealAnswer) {
    boolean hinted = session.getAnswerRequestCount() > 0;
    boolean correct = action.getEval() != null && Boolean.TRUE.equals(action.getEval().getCorrect());
    session.onRoundSignal(correct, hinted);
}
```
`noRealAnswer` 收紧：SWITCH 恒跳过；END/REVEAL 仅当 `eval==null`（无真实作答评估）才跳过，有 eval 即真实作答应累计。回归测试：END 答对 → 0.70。

**6. 面试口述要点**：讲"**一刀切跳过策略误伤真实信号**"——SWITCH 整轮跳过没问题，但 END/REVEAL 轮可能有真实 eval。技术权衡：用"是否有真实作答"（eval 非空）替代"是否是收尾轮"作判定，精确不误伤。踩坑收获：**信号收集的排除条件要按"有没有数据"而不是"轮次类型"判断**。

---
