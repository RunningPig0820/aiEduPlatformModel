# design-backend-add-tutoring-session-history-backend

> summary: 答疑会话历史模块D1阶段的设计方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D1. 不新增消息表；内容事实源 = COS transcript
> 模块: ai-tutoring ｜ 节: design-backend-add-tutoring-session-history-backend
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-add-tutoring-session-history-backend-D1-不新增消息表内容事实源-COS-transcript.md
> 类别：数据存储

---

### D1. 不新增消息表；内容事实源 = COS transcript

沿用现有「每轮幂等整写」机制：内容恒在 `tutoring/transcripts/{studentId}/{sessionId}.json`（含每轮完整消息与 generate thinking）。MySQL 只存会话记录。相比「消息落 MySQL」，砍掉建表、双写、消息查询，仅需在消息序列化时补 meta（D2）。Redis 保持活跃期热存与 decide 上下文源。
