# 字段改名 kp_label → topic_label

> summary: 字段改名 kp_label→topic_label，Java 已兼容；关键防回归=纠错提示词必须同步改名，否则掌握度静默丢失。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-ai-tutoring-topic-mastery-signal-D2-字段改名-topic-label.md
> 类别：数据关联

---

### 决策 2：字段改名 kp_label → topic_label（加分项）

> 检索摘要：字段改名 kp_label→topic_label，Java 已兼容；关键防回归=纠错提示词必须同步改名，否则掌握度静默丢失。

`MasterySignalItem.kp_label` → `topic_label`，description 语义改「题型」。Java 已 `@JsonAlias("topic_label")` 兼容旧名，改名无穿透风险。

**关键防回归**：`structured.py` 的 `_schema_instructions` 纠错提示词硬编码了 `"kp_label"`，必须同步改为 `"topic_label"`。否则 function calling schema（绑定 Pydantic 模型，自动变 topic_label）与纠错提示词字段名脱节 → 模型输出旧名 → Pydantic 校验 `topic_label` 缺失 → 反复纠错失败 → 掉进兜底 fallback → mastery_signals 静默丢失。

> 证据：详见 `2.OpenSpec design 决策/design-python-ai-tutoring-topic-mastery-signal.md`（§决策 2）｜ 坑档案 J-QT7
