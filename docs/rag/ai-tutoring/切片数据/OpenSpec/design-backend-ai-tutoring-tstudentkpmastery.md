# design-backend-ai-tutoring

> summary: 学生知识点掌握表t_student_kp_mastery的字段设计说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: `t_student_kp_mastery`
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-tstudentkpmastery.md
> 类别：数据存储

---

### `t_student_kp_mastery`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | |
| student_id | BIGINT | |
| kp_key | VARCHAR(255) | **TextbookKP URI** |
| kp_label | VARCHAR(255) | 知识点名（冗余，便于展示） |
| mastery_level | INT | 0–100 |
| evidence | JSON | 证据（命中步骤、错误事件 id 列表） |
| last_session_id | BIGINT | 最近一次答疑会话 |
| created_at / updated_at | DATETIME | 标准审计列 |
| created_by / modified_by / is_deleted | BIGINT / TINYINT(1) | 标准审计列（默认 0 / 逻辑删除） |
| **UNIQUE(student_id, kp_key)** | | 幂等 |
