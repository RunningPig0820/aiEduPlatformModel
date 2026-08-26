# design-backend-ai-tutoring

> summary: 答疑会话表t_tutoring_session的字段设计说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: `t_tutoring_session`
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> 类别：数据存储

---

### `t_tutoring_session`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT PK AUTO | 会话 ID |
| student_id | BIGINT | 学生 ID（网关注入） |
| subject | VARCHAR(32) | 学科（本期恒为 math） |
| question_type | VARCHAR(32) | 题型（答疑侧独立可扩展枚举，可空） |
| question_kind | VARCHAR(32) | 题类（计算/应用/证明，可空） |
| intent_category | VARCHAR(16) | ACADEMIC / GUIDANCE / UNRELATED（废弃？见下） |
| last_emotion | VARCHAR(16) | 最近一轮情绪（F7 七态，Python 输出方权威） |
| status | VARCHAR(16) | ACTIVE / ARCHIVED / TERMINATED |
| round_count | INT | 轮次（≤20） |
| answer_request_count | INT | 要答案次数 |
| end_reason | VARCHAR(32) | COMPLETED / ANSWER_REVEALED / ABANDONED / ROUND_LIMIT / null |
| transcript_url | VARCHAR(512) | COS 对话归档 objectKey（首次实时写时回填） |
| created_at / updated_at / archived_at | DATETIME | created_at=会话开始（标准审计列）；archived_at=归档时间 |
| created_by / modified_by / is_deleted | BIGINT / TINYINT(1) | 标准审计列（默认 0 / 逻辑删除，与全项目一致） |

> 说明：**不建消息表、不存题目内容**。对话每轮实时整写 COS（`tutoring/transcripts/{studentId}/{sessionId}.json`，恒为完整对话），Redis 为活跃期热存；**换题只作事件（仅计数重置）**，后端不记录、不维护题目文本——换题/当前题目判定全在 Python decide。`intent_category` 在 agent 语境下由 decide 判断（无关/学习方法 直接在回复中处理），可暂不落库，或保留用于统计——MVP 建议保留但可空。
