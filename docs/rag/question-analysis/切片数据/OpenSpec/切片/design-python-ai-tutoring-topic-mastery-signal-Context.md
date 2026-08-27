# 背景：掌握度信号需配合题型化翻转

> summary: 掌握度信号需配合题型化翻转：继续输出知识点名会污染后端题型库，Java 已兼容字段改名。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-ai-tutoring-topic-mastery-signal-Context.md
> 类别：项目介绍

---

### 背景：掌握度信号需配合题型化翻转

> 检索摘要：掌握度信号需配合题型化翻转：继续输出知识点名会污染后端题型库，Java 已兼容字段改名。

- **现状**：`decide` 每轮输出 `mastery_signals`（`MasterySignalItem.kp_label` + `signal`），label 语义为「知识点」，接地到 `mastery_snapshot`（旧 `t_student_kp_mastery` 的知识点 label 候选）。后端 `kp-matching-lightup` 已决定把掌握度主体从知识点翻转为题型，`mastery_signals` 需配合输出题型。
- **链路**：`decide → mastery_signals[].kp_label → Java resolve → 掌握度落库 → 图谱点亮`。当前若继续输出知识点名，后端会把它当题型落进题型掌握度表 → 题型库混入知识点名 → 整条链路脏。
- **关键约束**：后端 Java 已用 `@JsonAlias("topic_label")` 兼容旧字段名；前端读的是 Java 透传的 `kpLabel`（camelCase），与 Python 字段名无关 → 改名无跨仓库穿透风险。

> 证据：详见 `2.OpenSpec design 决策/design-python-ai-tutoring-topic-mastery-signal.md`（§背景）
