## Context

现状（已核实代码）：
- `t_tutoring_session`（MySQL）：每会话一行元数据（status/round_count/transcript_url/…/is_deleted），Mapper 只支持 `selectActiveByStudentId`（仅 ACTIVE）+ `updateTranscriptUrl` + BaseMapper。**无列表接口、无删除接口**。
- **COS transcript 每轮幂等整写**：`TutoringTranscriptArchiver.archive` 由 `TutoringAppService.archiveTranscript` 调用（buildStream 行 618 + orchestrate 行 457/717），objectKey `tutoring/transcripts/{studentId}/{sessionId}.json`，JSON 序列化完整 `List<TutoringChatMessage>`。**活跃/已结束/弃用会话内容都在 COS**（Redis 仅 24h 热存）。
- **`TutoringChatMessage` 只有 `role/content/imageUrl/thinking/createdAt`，无 meta 字段**。`toMessage`（useTutoringSession.js）读 `m.type/denied/decide_reason/round/question_kps/eval/status`，服务端消息无 meta → 工作流只能退化显示（①③④ 按 type、②⑤⑥ 占位）；今日历史完整工作流依赖前端 localStorage 快照。
- `getSession`（行 222）返回 Redis recentMessages + 签名 `transcriptUrl`（`resolveTranscriptUrl`），已结束会话 Redis 已清、transcriptUrl 仍在。
- 前端历史列表存 localStorage（`ai_tutoring_sessions`，上限 10）；`loadSession` 读 localStorage + `reconcileSession` 合并 Redis；`HistorySidebar` 无删除按钮。

## Goals / Non-Goals

**Goals:**
- 会话记录持久化在 MySQL（列表/删除能力），内容继续从 COS 获取（不落消息表）
- `TutoringChatMessage` 携带 meta → Redis/COS 序列化后历史工作流**完整复原**，摆脱 localStorage 快照
- 提供 `GET /sessions`（列表，全状态，按 user）与 `DELETE /sessions/{id}`（软删除）
- 前端历史列表迁移到 API + `HistorySidebar` 删除交互

**Non-Goals:**
- 消息内容落 MySQL（不新增 `t_tutoring_message`）——内容事实源为 COS transcript
- 物理删除 / COS 彻底清理（软删数据超期后由后续独立定时任务处理）
- 会话内容改造、工作流渲染契约变更

## Decisions

### D1. 不新增消息表；内容事实源 = COS transcript

沿用现有「每轮幂等整写」机制：内容恒在 `tutoring/transcripts/{studentId}/{sessionId}.json`（含每轮完整消息）。MySQL 只存会话记录。删除/列表围绕 `t_tutoring_session` 操作。相比「消息落 MySQL」，砍掉建表、双写、消息查询，仅需在消息序列化时补 meta（见 D2）。

### D2. `TutoringChatMessage` 补 meta 字段

给 `TutoringChatMessage` 增加 7 个可空字段（`@JsonProperty` snake_case，与 Java↔Python 契约一致）：`type / denied / decide_reason / round / question_kps / eval / status`。AI 消息 append（后端设计定位为 buildStream.doOnComplete 行 616；行 753 为 start 用户消息，meta 恒 null）时从 `ActionMeta` 填入。这样 Redis 消息 + COS transcript JSON 都携带 meta，前端 `toMessage` 无需改字段名（已兼容 `decide_reason||decideReason`、`question_kps||questionKps`）。用户消息 meta 为 null（`toMessage` 对 user 消息不建 agentFlow）。

**eval 命名容错（后端 Risk R2）**：transcript 的 eval 内字段为 snake_case（`exercise_complete`），前端 `deriveTurnFlow` 读 camelCase `e.exerciseComplete`（tutoringWorkflow.js:105/154）→ 历史复原该字段 undefined。前端在 `deriveTurnFlow` 读 eval 处改为 `e.exerciseComplete ?? e.exercise_complete`（live 走 SseEvalDTO camel，无影响）。`error_type` 前端不读，无需处理。

### D3. `t_tutoring_session` 补 `title` 列

历史列表展示标题用。`title VARCHAR(255)`：首条用户消息 append 时生成（取内容前 N 字，约 30）。存量会话回填空串，前端用占位（如「答疑会话」）。

### D4. 列表 / 删除接口

| 接口 | 行为 |
|---|---|
| `GET /api/tutoring/sessions` | `t_tutoring_session WHERE student_id=? AND is_deleted=false ORDER BY updated_at DESC`（全状态，含已归档）→ `[{id,title,status,subject,questionType,roundCount,updatedAt,archivedAt}]` |
| `DELETE /api/tutoring/sessions/{id}` | 软删：session 行 `is_deleted=1` + `sessionCache.clear`（清 Redis 两 key）。COS transcript/图片**保留**（软删可恢复） |

- 用户归属：从鉴权上下文取当前用户 id，与 `session.student_id` 不一致返回 403/404（列表/删除均校验）。

### D5. 前端内容加载：`transcriptUrl → COS transcript`

`loadSession(id)` 流程：
1. `GET /sessions/{id}` → 拿 `transcriptUrl`（签名 URL，已结束/活跃会话均有）与 `status`
2. `transcriptUrl` 存在 → `fetch` COS JSON → `messages` 数组（完整 `TutoringChatMessage`，含 meta）→ `toMessage` 逐条复原（`agentFlow` 由 meta 派生 → 工作流完整）
3. `transcriptUrl` 为空（新会话仅首条用户消息、无 AI 回合）→ 回退 `recentMessages`（Redis）
4. 两者皆失败 → 回退 localStorage 离线兜底

### D6. 前端列表与删除迁移

- `src/api/modules/tutoring.js`：+`listSessions()`（无参，后端从 Session 取 studentId，前端**不传 user_id**）+`deleteSession(id)`
- `useTutoringSession.js`：历史列表 `getStoredSessions()` → `listSessions`；**列表项字段映射 `sessionId → id`**（HistorySidebar/AiQa 用 `session.id`，后端列表项 DTO 为 `sessionId`）后再交给侧栏；`loadSession` 按 D5；localStorage 仅离线兜底
- `HistorySidebar.jsx`：每项删除按钮 + 确认框 → `deleteSession(id)` → 刷新列表；删除当前打开会话回新建态

### D7. 删除语义：软删 + COS 保留

- 软删（`is_deleted=1`）即「用户视角删除」：列表/详情不可见，数据完整可恢复。
- COS 对象不删：恢复时内容完好；物理清理拆为后续独立能力（定时任务扫 `is_deleted=1` 超期 → 删 COS + 硬删行）。
- 代价：软删数据占存储，量小可接受。

## Risks / Trade-offs

- **在途回合不在 COS**：transcript 在每轮 AI 回复后整写；用户发消息后立即关页，最新 user 消息可能未入 COS → Redis 24h 内可回退（recentMessages），过期则该条缺失。可接受（量小）。
- **存量 transcript 无 meta**：改造前的 COS transcript 消息无 meta → 历史工作流退化显示（①③④ 按 type、②⑤⑥ 占位），`toMessage` 已优雅降级不报错；新会话自然补齐。
- **越权访问**：列表/删除未校验归属 → 统一从鉴权上下文取 user，`student_id` 不匹配拒绝。
- **COS 签名 URL 时效**：`transcriptUrl` 为短时签名 → 前端即时拉取即可；过期则重调 `GET /sessions/{id}` 刷新。
- **序列化兼容**：`TutoringChatMessage` 加字段不破坏既有 Python 消费（Java→Python 用 snake_case，新增可空字段 Python 侧忽略；Python→Java 无此模型）。

## Migration Plan

1. 后端：`t_tutoring_session` 加 `title` DDL；`TutoringChatMessage` 加 meta 字段 + append 填 meta
2. 后端：列表 + 删除接口 + title 生成
3. 前端：api 层 + hook（列表/COS 加载）+ HistorySidebar 删除
4. 验证：新会话 COS 含 meta；列表/删除 E2E；历史工作流完整复原；localStorage 兜底
5. 回滚：接口灰度前可关；删除走软删可恢复；前端回退 localStorage 读取

## Open Questions

- 列表分页策略（页码 vs 游标）：当前 `MAX_SESSIONS=10` 量级，先页码 + 默认 50，超量再加游标。
- `user_id` 命名：`t_tutoring_session` 现有 `student_id`，列表按此查询（用户维度映射），不新增列。
