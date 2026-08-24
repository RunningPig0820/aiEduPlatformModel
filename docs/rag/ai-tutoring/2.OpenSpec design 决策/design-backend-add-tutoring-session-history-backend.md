## Context

现状（已核实代码）：
- `t_tutoring_session`（MySQL）：每会话一行元数据（status/round_count/transcript_url/…/is_deleted），`student_id` 即 user↔session 索引。Mapper 只有 `selectActiveByStudentId`（仅 ACTIVE）+ `updateTranscriptUrl` + BaseMapper。**无列表接口、无删除接口、无 title 列**。
- **COS transcript 每轮幂等整写**：`TutoringTranscriptArchiver.archive` 由 `TutoringAppService.archiveTranscript` 调用（buildStream 行 618 + postDecide 行 458），objectKey `tutoring/transcripts/{studentId}/{sessionId}.json`，JSON 序列化完整 `List<TutoringChatMessage>`。活跃/已结束/弃用会话内容**都在 COS**（Redis 仅 24h 热存）。
- **`TutoringChatMessage` 只有 `role/content/imageUrl/thinking/createdAt`，无 meta 字段**。前端 `toMessage` 读 `m.type/denied/decide_reason/round/question_kps/eval/status`，服务端消息无 meta → 历史工作流只能退化显示，今日完整工作流依赖前端 localStorage 快照。
- `getSession`（TutoringAppService 行 222）返回 Redis recentMessages + 签名 `transcriptUrl`（`resolveTranscriptUrl`），已结束会话 Redis 已清、transcriptUrl 仍在 → **详情内容加载后端无需改动**，前端直接拉 COS。
- MyBatis-Plus 全局 `logic-delete-field: deleted` 已配置，`TutoringSessionPo.deleted`（映射 `is_deleted`）自动生效：`findById` 已过滤软删行、`deleteById` 即逻辑删。
- `TutoringChatMessage` 经 `DecideContext.history` 序列化发给 Python（Java↔Python 契约 snake_case）——新增字段会随下一轮 decide 请求到 Python，需验证容忍度。

## Goals / Non-Goals

**Goals:**
- 会话记录持久化 + 历史管理能力：全状态列表、软删除、展示标题
- `TutoringChatMessage` 携带工作流 meta → Redis/COS 序列化后历史 ①-⑥ 工作流**完整复原**，摆脱前端 localStorage 快照
- 不新增消息表；内容事实源保持 COS transcript；`getSession` 不动
- 全部 additive / 新端点，不改既有答疑行为

**Non-Goals:**
- 消息内容落 MySQL（不建 `t_tutoring_message`）
- 物理删除 / COS 彻底清理（软删超期清理为后续独立定时任务）
- 会话内容改造、工作流渲染契约变更、decide thinking 持久化

## Decisions

### D1. 不新增消息表；内容事实源 = COS transcript

沿用现有「每轮幂等整写」机制：内容恒在 `tutoring/transcripts/{studentId}/{sessionId}.json`（含每轮完整消息与 generate thinking）。MySQL 只存会话记录。相比「消息落 MySQL」，砍掉建表、双写、消息查询，仅需在消息序列化时补 meta（D2）。Redis 保持活跃期热存与 decide 上下文源。

### D2. `TutoringChatMessage` 补 7 个 meta 字段 + AI 消息 append 填充

给 `TutoringChatMessage` 增加 7 个可空字段（`@JsonProperty` snake_case，与 Java↔Python 契约一致）：`type / denied / decide_reason / round / question_kps / eval / status`。

**填充位置：仅 `buildStream.doOnComplete`（行 616）**，AI 回复 append 时填 meta。行 753（`ensurePersisted`）是 start 的用户消息，meta 恒 null（前端对 user 消息不建 agentFlow）。填充后 Redis append + 行 618 `archiveTranscript` 重写 COS，meta 自动进 COS，无需改归档器。

**meta 取值 = `buildMeta` 同源镜像**（action/allowedType/guard/session 均在 buildStream 参数作用域），保证历史复原与 live SSE 渲染逐字段一致：

| 字段 | 取值 | 依据 |
|---|---|---|
| `type` | `allowedType.name().toLowerCase()` | **生效类型**（护栏降级后），非 `action.type`——`deriveTurnFlow.guideStep/clarify` 依赖此值，live 的 SSE meta.type 也是 allowedType |
| `denied` | `guard.isAllowed() ? null : ActionType.fromCodeOrDefault(action.getType()).name().toLowerCase()` | 护栏拒绝时的原始请求类型（如 reveal），eval 门控判定用 |
| `decide_reason` | `action.getReason()` | Python 决策自由文本 |
| `round` | `session.getRoundCount()` | applySideEffects 已跑完（postDecide 步骤 7 在 buildStream 前），即当前轮次 |
| `question_kps` | `action.getQuestionKps()` | List\<String\>，前端 `Array.isArray` 判定 |
| `eval` | `action.getEval()` | `EvalInfo` 对象（snake_case 内字段）——命名兼容见 Risk R2 |
| `status` | `session.getStatus()?.name()` | ACTIVE/ARCHIVED/TERMINATED；最后一轮 reveal/end 收尾后为 ARCHIVED → 前端 ⑥ 归档点亮 |

用户消息（行 175/202/204/215/753）meta 全空，不填。

### D3. `t_tutoring_session` 补 `title` 列 + 首条用户消息生成

- DDL：`ALTER TABLE t_tutoring_session ADD COLUMN title VARCHAR(255) NULL`（Flyway V13）。
- `TutoringSession` 域实体加 `title` 字段（restore 参数 + 生成入口）；`TutoringSessionPo` 同步。
- 生成时机：`start()` 建首条消息后，从首条用户消息内容取前 ~30 字；图片题 content 空/纯图 → 兜底 `subject + questionType` 或「图片题目」。
- 存量会话 title 为空串，前端用占位「答疑会话」。

### D4. 列表 / 删除接口

| 接口 | 行为 |
|---|---|
| `GET /api/tutoring/sessions` | `TutoringSessionMapper.selectListByStudentId`：`WHERE student_id=? AND is_deleted=false ORDER BY updated_at DESC`（全状态含已归档）→ 列表项 DTO `{sessionId, title, status, subject, questionType, roundCount, updatedAt, archivedAt}` |
| `DELETE /api/tutoring/sessions/{id}` | 归属校验（`loadSession` 已内置，studentId 不匹配 404）→ 软删（`deleteById` 逻辑删或显式 update）→ `sessionCache.clear`（清 session+messages+active 三 key）→ COS 保留 |

- 用户归属：列表按鉴权上下文 `studentId` 查询；删除经 `loadSession` 校验（用 `loadSession` 而非 `loadActiveSession`——已归档/终止会话也可删）。
- 软删：全局 `logic-delete-field: deleted` 已配，`deleteById` 即 `is_deleted=1`；`findById` 自动过滤 → 软删后详情天然 404。
- 列表项 DTO 命名沿用 `sessionId`（与现有 `TutoringSessionDTO` 一致），设计稿 `id` 为简写。

### D5. `getSession` 不改

详情内容加载由前端经 `transcriptUrl` 拉 COS 完成；后端 `getSession` 已返回签名 `transcriptUrl` + Redis recentMessages 兜底。本变更零改动。

## Risks / Trade-offs

- **R1 [Python 容忍 history 新字段] → 实施前实测**。加 meta 的 AI 消息进入下一轮 `DecideContext.history`。Python Pydantic 若开 `extra="forbid"`，decide 直接 422/挂。设计假定 Python 忽略额外字段（additive，历史已在传 `image_url/thinking/created_at` 同理），须在 Python 侧验证模型配置。
- **R2 [`eval.exerciseComplete` 命名不匹配] → 前端一行容错**。`EvalInfo` 内字段 snake_case（`exercise_complete`），前端 `deriveTurnFlow` 读 camelCase `e.exerciseComplete` → 历史复原该字段 undefined（live 走 `SseEvalDTO` 是 camel，无此问题）。推荐前端 `e.exerciseComplete ?? e.exercise_complete`；否则后端需在消息层用 camelCase 结构（领域层无法引用 application 的 SseEvalDTO）。
- **R3 [存量 transcript 无 meta] → 优雅降级**。改造前的 COS 消息无 meta → 历史工作流退化显示（①③④ 按 type、②⑤⑥ 占位），`toMessage` 已兼容不报错；新会话自然补齐。
- **R4 [在途回合最新 user 消息不在 COS] → Redis 兜底**。用户发消息后立即关页，最新 user 消息可能未入 COS → `recentMessages`（Redis 24h）兜底，过期则该条缺失（量小可接受）。
- **R5 [终止类回复不落 Redis/COS] → 接受现状**。`terminate()`/`endByRoundLimit()` 回复只走 SSE `meta.reply`，不进消息列表/COS（既有行为）。历史改从 COS 读后，已终止会话缺最后一条 assistant 回复；如需补齐可在 terminate/round-limit 路径补 `archiveTranscript`（本变更默认不做，前端展示最后一条 user 消息即可）。
- **R6 [越权访问] → 统一鉴权**。列表按 `studentId` 查询天然隔离；删除/详情经 `loadSession` 校验，studentId 不匹配 404。
- **R7 [列表量增长] → 先页码**。当前 `MAX_SESSIONS=10` 量级，列表接口先页码 + 默认 50，超量再加游标。
- **R8 [COS 签名 URL 时效] → 即时拉取**。`transcriptUrl` 为短时签名，前端拿到即 fetch；过期则重调 `GET /sessions/{id}` 刷新。

## Migration Plan

1. **DDL**：`V13__alter_t_tutoring_session_add_title.sql` 加 `title` 列。
2. **消息 meta**：`TutoringChatMessage` 加 7 字段；行 616 append 填 meta；Redis/COS 序列化自动携带。
3. **列表/删除**：Mapper/Repository 补查询与软删；`TutoringAppService` 加 `listSessions`/`deleteSession`/title 生成；Controller 加 2 端点。
4. **验证**：单测（meta 序列化、列表全状态/排除软删/按用户隔离、删除软删+Redis 清+归属校验）+ Python 契约验证（R1）。
5. **回滚**：新接口灰度前可关；软删可恢复（`is_deleted=0`）；前端回退 localStorage 读取；meta 字段 additive 移除无影响。

## Open Questions

- `eval` 命名方案待与前端确认：前端容错 `exercise_complete`（推荐）vs 后端消息层 camelCase 结构。
- 列表项 DTO 字段名 `sessionId`（推荐）vs 设计稿 `id`，以前端 `listSessions` 读取为准。
- 终止类回复是否补落 COS（R5）：本变更接受现状，后续独立处理。
- 列表分页：页码 + 默认 50 起步，超量加游标。
