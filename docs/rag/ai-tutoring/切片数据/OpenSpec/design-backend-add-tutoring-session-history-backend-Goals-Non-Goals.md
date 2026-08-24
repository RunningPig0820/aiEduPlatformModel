# design-backend-add-tutoring-session-history-backend

> summary: 答疑会话历史模块的目标与非目标范围
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-backend-add-tutoring-session-history-backend

---

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
