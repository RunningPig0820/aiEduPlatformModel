# design-backend-tutoring-agent-workflow-backend

> summary: 验证D1-D5后端契约符合冻结要求
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 冻结确认（对 D1-D5 的验证，已对照代码）
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-tutoring-agent-workflow-backend-冻结确认对-D1-D5-的验证已对照代码.md
> 类别：架构设计

---

## 冻结确认（对 D1-D5 的验证，已对照代码）

| 决策 | 现状 |
|---|---|
| D1 decide filter `thinking + agent` | ✅ `TutoringAppService.orchestrate` 407 行，decide agent 事件按 Python 顺序原样透传 |
| D2 `decideReason`（Python 理由） | ✅ buildMeta 无条件 set；`reason`（护栏 code）语义不变，仅拒绝时 set |
| D3 `SseMasterySignalDTO` camelCase | ✅ `meta.masterySignals` 序列化为 `{kpLabel, signal}`（前端只读此字段，不再读 `meta.eval.masterySignals`） |
| D4 `questionKps` | ✅ ActionMeta question_kps → SseMetaDTO，可空，前端占位"—" |
