# 自动维护闭环（保守）

> summary: 周期任务扫描 CONFLICTED/低置信/分布异常行，用年级锚+题型库先验+LLM 重判，变化回流传先验，仍歧义进 HUMAN_REVIEW 人工队列。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D5-自动维护闭环-保守.md
> 类别：架构设计

> 检索摘要：周期任务扫描 CONFLICTED/低置信/分布异常行，用年级锚+题型库先验+LLM 重判，变化回流传先验，仍歧义进 HUMAN_REVIEW 人工队列。

周期任务（`@Scheduled`，如每日）：

```
错误信号 → 扫描 CONFLICTED/低置信/分布异常行
  → 用「年级锚 + 题型库先验 + LLM」重判
  → 变化时：更新 obs + 更新题型库统计（先验漂移）
  → 仍歧义 → status=HUMAN_REVIEW → 管理端「待确认」队列
```

**错误信号来源**（自动，无人盯）：
- decide 诊断冲突：LLM 说"卡在假设法"但 obs 记了二元一次方程组 → `CONFLICTED`。
- 掌握度矛盾：该生二元一次方程组已 mastered 却仍在鸡兔同笼上 struggling 且归到它。
- 年级分布异常：题型在某年级段分布出现非预期尖峰 → 触发重审。
- 低置信：confidence < 阈值 → 直接重判。

**保守原则**：只有高置信重判才自动改；LLM 也摇摆、无年级锚的进人工。一次修正回流先验 → 全体学生受益（"共享维护"）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D5 自动维护闭环（保守））
