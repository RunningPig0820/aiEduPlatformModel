# design-backend-tutoring-agent-events

> summary: 说明generate阶段agent事件的中继实现方案
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D4. generate 中继 agent 事件
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-events
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-tutoring-agent-events-D4-generate-中继-agent-事件.md
> 类别：架构设计

---

### D4. generate 中继 agent 事件

**选择**: `buildStream` 的过滤器从 `.filter(token)` 改 `.filter(token || agent)`，map 区分：token → 累积 AI 回复 + 透传；agent → 原样中继（`event: agent`）。Python generate 的 meta/done 仍丢弃（Java 自建）。
