# design-backend-add-tutoring-session-history-backend

> summary: 面试问答：答疑会话历史后端需实现列表查询与删除接口
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D4. 列表 / 删除接口
> 模块: ai-tutoring ｜ 节: design-backend-add-tutoring-session-history-backend

---

### D4. 列表 / 删除接口

| 接口 | 行为 |
|---|---|
| `GET /api/tutoring/sessions` | `TutoringSessionMapper.selectListByStudentId`：`WHERE student_id=? AND is_deleted=false ORDER BY updated_at DESC`（全状态含已归档）→ 列表项 DTO `{sessionId, title, status, subject, questionType, roundCount, updatedAt, archivedAt}` |
| `DELETE /api/tutoring/sessions/{id}` | 归属校验（`loadSession` 已内置，studentId 不匹配 404）→ 软删（`deleteById` 逻辑删或显式 update）→ `sessionCache.clear`（清 session+messages+active 三 key）→ COS 保留 |

- 用户归属：列表按鉴权上下文 `studentId` 查询；删除经 `loadSession` 校验（用 `loadSession` 而非 `loadActiveSession`——已归档/终止会话也可删）。
- 软删：全局 `logic-delete-field: deleted` 已配，`deleteById` 即 `is_deleted=1`；`findById` 自动过滤 → 软删后详情天然 404。
- 列表项 DTO 命名沿用 `sessionId`（与现有 `TutoringSessionDTO` 一致），设计稿 `id` 为简写。
