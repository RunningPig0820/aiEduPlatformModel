# design-backend-tutoring-subject-gate

> summary: 确认三个LLM调用统一使用doubao-seed-2-0-mini模型
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 4. 三个 LLM 调用统一模型（已确认）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-subject-gate

---

### 4. 三个 LLM 调用统一模型（已确认）

| 端点 | 模型 | 现状 |
|------|------|------|
| decide | `doubao-seed-2-0-mini-260428` / 0.3 | 已是 |
| question_understand | `doubao-seed-2-0-mini-260428` / 0.3 | 已是 |
| **subject-classify（新）** | `doubao-seed-2-0-mini-260428` / 0.3 | 沿用 |
