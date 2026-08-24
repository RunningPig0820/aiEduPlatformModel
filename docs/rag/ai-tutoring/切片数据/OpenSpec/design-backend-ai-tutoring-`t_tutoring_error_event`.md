# design-backend-ai-tutoring

> summary: 答疑错误事件表t_tutoring_error_event的字段设计说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: `t_tutoring_error_event`
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### `t_tutoring_error_event`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | |
| student_id | BIGINT | |
| session_id | BIGINT | |
| kp_key | VARCHAR(255) | 关联知识点（可空） |
| error_type | VARCHAR(64) | eval 输出的错误类型 |
| emotion | VARCHAR(16) | 该轮情绪（F7 七态） |
| step_index | INT | |
| student_answer | TEXT | 学生原答 |
| created_at / updated_at | DATETIME | 标准审计列 |
| created_by / modified_by / is_deleted | BIGINT / TINYINT(1) | 标准审计列（默认 0 / 逻辑删除） |
