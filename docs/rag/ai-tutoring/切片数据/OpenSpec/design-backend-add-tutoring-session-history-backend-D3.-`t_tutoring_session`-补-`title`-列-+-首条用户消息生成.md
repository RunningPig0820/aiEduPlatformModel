# design-backend-add-tutoring-session-history-backend

> summary: 面试问答：答疑会话历史后端需补t_tutoring_session的title列
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D3. `t_tutoring_session` 补 `title` 列 + 首条用户消息生成
> 模块: ai-tutoring ｜ 节: design-backend-add-tutoring-session-history-backend

---

### D3. `t_tutoring_session` 补 `title` 列 + 首条用户消息生成

- DDL：`ALTER TABLE t_tutoring_session ADD COLUMN title VARCHAR(255) NULL`（Flyway V13）。
- `TutoringSession` 域实体加 `title` 字段（restore 参数 + 生成入口）；`TutoringSessionPo` 同步。
- 生成时机：`start()` 建首条消息后，从首条用户消息内容取前 ~30 字；图片题 content 空/纯图 → 兜底 `subject + questionType` 或「图片题目」。
- 存量会话 title 为空串，前端用占位「答疑会话」。
