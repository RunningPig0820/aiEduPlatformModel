# design-backend-tutoring-subject-gate

> summary: 确认数学答疑后端编排及模型调用现状
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-subject-gate

---

## Context

已确认的现状（代码验证）：

- **Java 编排**：安全预检 → 收题（文字/图片→COS）→ `TutoringSession.start(studentId,"math")` 建会话 → Python `decide`（数学提示词）→ Java 护栏 → Python `generate` → 透传。
- **decide 是数学专用提示词**（`prompts.py _DECIDE_SYSTEM`："你是数学答疑的决策器"）；对非数学题仅有一条口头规则（"非数学题说明只辅导数学并引导回来"→ type=concept），**无结构化 subject 输出**。
- **`subject_hint` 是死参数**：Java 恒传 `subject_hint="math"`，但 decide 提示词模板无 `{subject_hint}` 占位符——传了没用到。
- **模型现状**：decide（`settings.TUTORING_DECIDE_MODEL`）与 question_understand（`_UNDERSTAND_MODEL`）**均为 `doubao-seed-2-0-mini-260428`，temp 0.3**——三个统一模型现状已满足两个。
- **Python stateless 端点模式成熟**：understand / vector 均为独立小端点，不碰 MySQL/KG，Java 经桥调用。
