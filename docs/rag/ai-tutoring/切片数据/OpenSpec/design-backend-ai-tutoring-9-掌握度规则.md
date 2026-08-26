# design-backend-ai-tutoring

> summary: AI辅导掌握度规则的定义、计算与校正逻辑
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 9. 掌握度规则
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-9-掌握度规则.md
> 类别：数据关联

---

### 9. 掌握度规则

（保留 + 出口路径）`mastery_level` 0–100，复用学习域 `MasteryLevel` 概念。每轮 eval 返回 `mastery_signals`：mastered→75 / practicing→50 / struggling→25，取 max 单调不减；学生显式纠正时允许下调；错误只记 `t_tutoring_error_event` 不降分。**收尾按 end_reason 校正**：`COMPLETED`（独立解出）→ 提升到 75+；`ANSWER_REVEALED`（看过答案）/ `ABANDONED` / `ROUND_LIMIT` → 不提升。掌握度是**基础信号**，最终掌握靠举一反三 + 错题集（阶段 2+）校正。
