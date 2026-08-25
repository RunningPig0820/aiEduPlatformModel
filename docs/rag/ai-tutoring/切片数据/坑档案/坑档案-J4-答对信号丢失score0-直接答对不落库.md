# 坑档案

> summary: 解决答对信号丢失，收紧noRealAnswer判定规则
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J4. 答对信号丢失（score=0 / 直接答对不落库）
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J4. 答对信号丢失（score=0 / 直接答对不落库）
- **坑**：学生直接答对收尾，掌握度却记 0/不落库。
- **根因**：END/REVEAL 轮整轮跳过累计，但 END 轮有真实 eval（答对 exerciseComplete）也被跳过。
- **解决**：`noRealAnswer` 判定收紧——SWITCH 恒跳过；END/REVEAL **有 eval 就是真实作答**，照常累计。
- **证据**：`1b2feb6`①；`TutoringAppService.java:734-740`。
