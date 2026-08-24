## Why

历史会话列表目前存于前端 localStorage（上限 10 条），后端 `t_tutoring_session` 仅存元数据、会话内容每轮实时整写在 COS transcript。后果：换设备/清缓存即丢历史、无法对历史会话做删除操作。需要让会话记录持久化在 MySQL（可列表/删除），内容继续从 COS 获取。

## What Changes

- **MySQL 只存会话记录**：不新增消息表；`t_tutoring_session` 补 `title` 列（列表展示标题），其余元数据列已齐
- **`TutoringChatMessage` 补 meta 字段**（type/denied/decide_reason/round/question_kps/eval/status）：AI 消息 append 时从 `ActionMeta` 填入，随 Redis + COS transcript 序列化 → 历史从 COS 复原时 ①-⑥ 工作流**完整还原**（不再依赖前端 localStorage 快照）
- 新增 **`GET /api/tutoring/sessions`** 列表接口：按 `user_id` 查全状态会话（含已归档、不含已删除），`updated_at` 倒序
- 新增 **`DELETE /api/tutoring/sessions/{id}`** 删除接口：**软删除**（`is_deleted=1`）+ 清 Redis 活跃缓存；COS transcript/图片**保留**（可恢复，物理清理另立后续能力）
- 会话内容来源：`GET /sessions/{id}` 已返回签名 `transcriptUrl`，前端从 COS 拉取 transcript JSON（完整消息含 meta）渲染；Redis recentMessages 仅作无 transcript 时的兜底
- 前端历史列表从 localStorage 迁移到 `GET /sessions`；`HistorySidebar` 增加每项**删除按钮 + 确认**；localStorage 降级为离线兜底

## Capabilities

### New Capabilities

- `tutoring-session-history`: 历史会话记录持久化到 MySQL（列表/删除接口 + 内容经 COS 复原 + 前端历史列表迁移与删除交互）

### Modified Capabilities

<!-- 无：tutoring-agent-workflow 仍为 active change；本次仅让消息随 Redis/COS 携带 meta 以复原工作流，不改变六阶段渲染契约 -->

## Impact

- **后端** `ai-edu-backend`：
  - `TutoringChatMessage` 补 meta 字段（+`@JsonProperty` snake_case，Java↔Python 契约不变）
  - `TutoringAppService`：AI 消息 append（行 616/753）从 `ActionMeta` 填 meta；新增列表/删除；title 生成
  - `TutoringSessionMapper/Repository`：补全状态列表查询（非仅 ACTIVE）、软删
  - `t_tutoring_session` DDL 加 `title` 列
- **前端** `ai-edu-front`：
  - `src/api/modules/tutoring.js`：+`listSessions()` +`deleteSession(id)`
  - `useTutoringSession.js`：历史列表走 `listSessions`；`loadSession` 经 `transcriptUrl` 从 COS 拉 transcript 复原消息；localStorage 降级兜底
  - `HistorySidebar.jsx`：删除按钮 + 确认 + 删除后刷新
- **契约**：新增 2 个接口；COS transcript 消息项携带 meta 字段
