# design-backend-ai-tutoring

> summary: AI辅导采用Redis+MySQL+COS三层存储方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 11. 存储三层：Redis（活跃）+ MySQL（业务）+ OSS/COS（归档）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### 11. 存储三层：Redis（活跃）+ MySQL（业务）+ OSS/COS（归档）

（保留 + 实时写）Redis 存活跃会话（状态、计数、完整消息列表，TTL 24h，供 decide 组装上下文与断点恢复；**不记录题目内容**）；MySQL 存 `t_tutoring_session` + `t_student_kp_mastery` + `t_tutoring_error_event`（结构化业务数据，**无题目内容、无原始消息**）；**对话每轮实时整写 COS**（`FileStorageService`，`tutoring/transcripts/{studentId}/{sessionId}.json`，幂等整写、脱敏，**COS 恒为完整对话**），会话结束终态写一次；`transcript_url`=objectKey 首次实时写即回填，读时签名 URL。

**题目图片存储（2026-08-06，image-first）**：题目/示例图按学生+会话组织 + 时间戳命名——`tutoring/questions/{studentId}/{sessionId}/{yyyyMMdd-HHmmss-SSS}.{ext}`。图片 URL 作为消息 `image_url` 进对话历史（Redis + COS transcript 均含），与对话天然关联；图片发起会话时 Java 先落库拿 sessionId 再传图（不留 pending 临时目录）。**换题=学生发新图**：Java 检测新 URL 首次出现 → decide 带 `is_new_question=true` → Python 短路 `type=switch` → Java 重置计数（判定权在 Java，Python 无状态不依赖 history 图片推断）。
