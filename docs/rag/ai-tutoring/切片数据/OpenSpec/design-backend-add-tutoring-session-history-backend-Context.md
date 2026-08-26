# design-backend-add-tutoring-session-history-backend

> summary: 答疑会话历史模块的现状与数据存储情况
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-backend-add-tutoring-session-history-backend
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-add-tutoring-session-history-backend-Context.md
> 类别：数据存储

---

## Context

现状（已核实代码）：
- `t_tutoring_session`（MySQL）：每会话一行元数据（status/round_count/transcript_url/…/is_deleted），`student_id` 即 user↔session 索引。Mapper 只有 `selectActiveByStudentId`（仅 ACTIVE）+ `updateTranscriptUrl` + BaseMapper。**无列表接口、无删除接口、无 title 列**。
- **COS transcript 每轮幂等整写**：`TutoringTranscriptArchiver.archive` 由 `TutoringAppService.archiveTranscript` 调用（buildStream 行 618 + postDecide 行 458），objectKey `tutoring/transcripts/{studentId}/{sessionId}.json`，JSON 序列化完整 `List<TutoringChatMessage>`。活跃/已结束/弃用会话内容**都在 COS**（Redis 仅 24h 热存）。
- **`TutoringChatMessage` 只有 `role/content/imageUrl/thinking/createdAt`，无 meta 字段**。前端 `toMessage` 读 `m.type/denied/decide_reason/round/question_kps/eval/status`，服务端消息无 meta → 历史工作流只能退化显示，今日完整工作流依赖前端 localStorage 快照。
- `getSession`（TutoringAppService 行 222）返回 Redis recentMessages + 签名 `transcriptUrl`（`resolveTranscriptUrl`），已结束会话 Redis 已清、transcriptUrl 仍在 → **详情内容加载后端无需改动**，前端直接拉 COS。
- MyBatis-Plus 全局 `logic-delete-field: deleted` 已配置，`TutoringSessionPo.deleted`（映射 `is_deleted`）自动生效：`findById` 已过滤软删行、`deleteById` 即逻辑删。
- `TutoringChatMessage` 经 `DecideContext.history` 序列化发给 Python（Java↔Python 契约 snake_case）——新增字段会随下一轮 decide 请求到 Python，需验证容忍度。
