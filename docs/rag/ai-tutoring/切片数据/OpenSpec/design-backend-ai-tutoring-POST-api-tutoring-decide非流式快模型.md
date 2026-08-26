# design-backend-ai-tutoring

> summary: POST /api/tutoring/decide接口的请求响应与判定规则说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: `POST /api/tutoring/decide`（非流式，快模型）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-POST-api-tutoring-decide非流式快模型.md
> 类别：架构设计

---

### `POST /api/tutoring/decide`（非流式，快模型）

请求：`{history, round_count, answer_request_count, mastery_snapshot, subject_hint}`
- **判定链路（关键）**：换题 / 当前题目由 **Python decide 从 `history` 语义判断**，Java **不发送、不记录、不维护题目内容**——记录易错（OCR 乱码、模型转述、陈旧快照），判定权全在 Python。Java 只认 `type=switch` 事件重置计数，`new_question` 为 Python 输出、Java 仅作展示可选、不落库。
- `mastery_snapshot` 必须是 `[{kp_key, label, mastery_level}]`——**label 必带**，Python 侧用它做"label 接地"（优先复用已知知识点名，降低 Java label→URI 解析噪声）
响应：决策 3 的 action 元数据（type 闭集 + eval + mastery_signals + new_question + end_reason + summary + safety_flag + degraded）。若学生消息过简无题目 → type=concept 带澄清问题（由 decide 决定，Java 按 type 放行）。结构化输出失败兜底返回 **200 + ActionMeta(type=hint, degraded=true)**，不返回 503。
