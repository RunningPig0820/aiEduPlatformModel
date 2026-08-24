# design-backend-tutoring-agent-workflow-backend

> summary: 明确后端需实现的目标与不做的非目标事项
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend

---

## Goals / Non-Goals

**Goals:**
- decide agent 事件透传前端（意图解析 live 数据源）。
- meta 补齐 `decideReason`（Python 理由）/`questionKps`/`masterySignals`，修复 KpChips 契约缺口。
- 全部 additive / 透传，不改既有答疑行为。

**Non-Goals:**
- 不做前端面板（属前端 change `show-tutoring-agent-workflow`）。
- 不改 Python decide（`question_kps` 属前端 change tasks 2.1，独立部署）。
- 不改护栏/类型/轮次/收尾逻辑。
