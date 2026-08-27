# 目标与非目标

> summary: 目标=mastery_signals 稳定输出题型 label+字段改名 topic_label+题型名稳定+snapshot 脱钩；非目标=改 type/signal/question_kps 等。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-ai-tutoring-topic-mastery-signal-Goals-Non-Goals.md
> 类别：项目介绍

---

### 目标与非目标

> 检索摘要：目标=mastery_signals 稳定输出题型 label+字段改名 topic_label+题型名稳定+snapshot 脱钩；非目标=改 type/signal/question_kps 等。

**Goals:**
- `mastery_signals` 稳定输出**题型** label，不输出知识点。
- 字段名 `kp_label` → `topic_label`（语义清晰，Java 已兼容）。
- 题型名稳定规范（同一题型一致命名）。
- `mastery_snapshot` 脱钩（题型无法从知识点快照接地）。

**Non-Goals:**
- 不改 `type` 判定、`eval`、`safety_flag`、降级管线骨架、`generate`。
- 不改 `signal` 枚举（mastered/practicing/struggling）。
- 不改 `question_kps`（继续输出知识点）。
- 不做 student_grade（后端组织系统自查）、LLM 消歧、离线聚合（后端调 llm-gateway）。
- 不做同义词聚类（后端只做字面归一化）。

> 证据：详见 `2.OpenSpec design 决策/design-python-ai-tutoring-topic-mastery-signal.md`（§目标与非目标）
