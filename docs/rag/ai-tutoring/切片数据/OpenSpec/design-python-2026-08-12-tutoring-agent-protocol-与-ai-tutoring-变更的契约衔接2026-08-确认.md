# design-python-2026-08-12-tutoring-agent-protocol

> summary: 说明本变更与 ai-tutoring 的契约衔接规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 与 ai-tutoring 变更的契约衔接(2026-08 确认)
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-与-ai-tutoring-变更的契约衔接2026-08-确认.md
> 类别：架构设计

---

## 与 ai-tutoring 变更的契约衔接(2026-08 确认)

本变更是 `ai-tutoring` 的演进,衔接点:
- **ActionMeta 契约不变**(闭集 type/eval/mastery_signals/new_question/end_reason/summary/safety_flag/degraded)——decide 流式化只改响应"载体"(JSON→SSE 的 meta 事件),字段不变
- **请求契约不变**(DecideRequest/GenerateRequest,含 `is_new_question`、image_url 图片通道)——新增的 agent 事件是附加事件,不改请求
- **BREAKING 仅一处**: decide 响应从 JSON 改 SSE 流(Java 消费方式改,见 `docs/ai-tutoring-agent-events.md`)
- 旧文档已标注演进:`ai-tutoring/api.md`(decide 段)、`ai-tutoring/design.md`(决策 2)、`docs/ai-tutoring-agent.md`(3.1 段)
