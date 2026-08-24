## Why

历史会话列表目前存于前端 localStorage（上限 10 条），换设备/清缓存即丢历史、且无法对历史会话做删除操作。后端 `t_tutoring_session` 已按学生（`student_id`）存有 user↔session 索引与元数据，内容事实源为 COS transcript（每轮幂等整写，恒为完整对话）——但缺**列表接口、删除接口、展示标题**，且消息不携带工作流 meta，历史从 COS 复原时 ①-⑥ 工作流快照只能退化显示。需要补齐列表/删除/标题能力，并让消息携带 meta 使历史工作流完整复原。

## What Changes

- `TutoringChatMessage` 补 7 个可空 meta 字段（`type/denied/decide_reason/round/question_kps/eval/status`，`@JsonProperty` snake_case）：AI 消息 append 时从 `ActionMeta`（+生效类型/护栏结果）填入 → Redis 与 COS transcript 序列化均携带 meta，前端 `toMessage` 无需改字段名即可复原 ①-⑥ 工作流快照
- `t_tutoring_session` 补 `title` 列：首条用户消息时生成（内容前 ~30 字，图片题兜底），供历史列表展示
- 新增 **`GET /api/tutoring/sessions`** 列表接口：按 `student_id` 查全状态会话（含已归档、不含已删除），`updated_at` 倒序
- 新增 **`DELETE /api/tutoring/sessions/{id}`** 删除接口：**软删除**（`is_deleted=1`）+ 清 Redis 活跃缓存；COS transcript/图片**保留**（可恢复）
- **不新增消息表**：内容继续经 `GET /sessions/{id}` 返回的签名 `transcriptUrl` 由前端拉取 COS transcript 渲染（后端 `getSession` 已返回，不改动）
- 列表/删除的越权防护：从鉴权上下文取当前用户 id，与会话 `student_id` 不一致返回 404

## Capabilities

### New Capabilities

- `tutoring-session-history`: 答疑会话记录持久化与历史管理——会话列表/软删除接口、`title` 展示、消息 meta 随 Redis/COS 携带以复原历史工作流

### Modified Capabilities

<!-- 无：ai-tutoring / tutoring-agent-events / tutoring-agent-workflow-backend 均为 active change，本变更不改变答疑行为（护栏/类型/轮次/收尾/SSE 流），仅 additive 补 meta 与新增接口 -->

## Impact

- **`ai-edu-domain`**：`TutoringChatMessage` 加 meta 字段（`@JsonProperty` snake_case，Java↔Python 契约不变）；`TutoringSession` 加 `title` 字段（restore/start）
- **`ai-edu-infrastructure`**：`t_tutoring_session` 加 `title` 列（Flyway V13）；`TutoringSessionPo` 加 `title`；`TutoringSessionMapper` 加 `selectListByStudentId`（全状态）+ 软删；`TutoringSessionRepository`/Impl 同步补
- **`ai-edu-application`**：`TutoringAppService` AI 消息 append 填 meta + 新增 `listSessions`/`deleteSession` + title 生成；新增列表项 DTO
- **`ai-edu-interface`**：`TutoringController` 新增 `GET /sessions`、`DELETE /sessions/{id}`
- **测试**：`TutoringAppServiceTest`/`TutoringControllerTest` 补列表/删除/越权；`TutoringTranscriptArchiverTest` 校验 meta 序列化；Python 侧需验证 history 新字段容忍（`extra="forbid"` 会挂）
- **契约**：新增 2 个接口；COS transcript 消息项携带 meta 字段
