# Tutoring Agent Workflow Backend

## Why

前端 OpenSpec change `show-tutoring-agent-workflow`（Agent 工作流面板：本轮意图实时解析 + 题目六阶段生命周期）需要后端配套契约，当前有两类缺口：

1. **decide agent 事件被丢弃**：Python `api/tutoring.py` 已发出 `perceive → analyze → plan → decide` 的 decide 阶段 agent 事件，但 `TutoringAppService.orchestrate` 的 filter 只放行 `thinking`，这些事件被丢弃——面板"本轮意图"的"解析意图…"live 状态拿不到数据源。
2. **meta 事件缺字段**：`meta` 无 `questionKps`/`masterySignals`（前端 KpChips 读 `meta.eval.masterySignals` 恒 undefined）；Python 决策理由（`reason`）被 `ACTION_META_MAPPER`（容忍未知字段）静默丢弃，未透传到前端。

本变更补齐这些契约，全部 additive / 透传语义，**不改动既有答疑行为**（护栏/类型/轮次/收尾逻辑均不变）。

## What Changes

- `TutoringAppService.orchestrate` decide filter 从 `only thinking` 改为 `thinking + agent`，透传 Python decide 的 `agent(perceive/analyze/plan/decide)` 事件。
- `ActionMeta` 新增 `reason`（Python 决策自由文本）、`questionKps`（题目涉及知识点，可空）。
- `SseMetaDTO` 新增 `decideReason`（Python 决策自由文本）、`questionKps`、`masterySignals`（`List<SseMasterySignalDTO>`，camelCase `{kpLabel, signal}`）；**`reason` 语义不变**（护栏拒绝原因，仅拒绝时 set），与新增 `decideReason` 语义清晰可分（见 design D2）。
- 新建 `SseMasterySignalDTO`（camelCase）——避免复用领域 `MasterySignalItem` 的 `@JsonProperty("kp_label")` 把字段序列化成 snake_case（design D3 隐性坑）。
- `buildMeta` 带出 decideReason/questionKps/masterySignals；护栏拒绝时 set `denied` + `reason`（语义不变）。
- OpenSpec `tutoring-agent-events/api.md` 契约更新：decide agent 事件透传 + meta 新字段。

## Capabilities

### New Capabilities

- `tutoring-agent-workflow-backend`: 答疑编排的 decide agent 事件透传 + meta 事件新契约字段（decideReason/questionKps/masterySignals），为前端 Agent 工作流面板提供数据契约。

### Modified Capabilities

<!-- 无既有 spec 需求变更：本变更不改变答疑行为，仅新增透传与字段（additive）。 -->

## Impact

- **Java（主）**：`TutoringAppService.orchestrate/postDecide/buildMeta`、`ActionMeta`、`SseMetaDTO`、新增 `SseMasterySignalDTO`。
- **测试**：`TutoringAppServiceTest.sendMessage_decideThinkingRelayedFirst` 需更新（decide agent 事件透传断言）+ meta 新字段断言。
- **契约文档**：`openspec/changes/tutoring-agent-events/api.md`。
- **Python（配套，独立部署）**：decide meta 增加 `question_kps`（见前端 change tasks 2.1，不在本变更范围；Python 未下发时 Java 透传 null，前端显示占位"—"）。

---

# 阶段二（2026-08-13）：展示位重构 · 契约冻结确认

## Why

前端 `show-tutoring-agent-workflow` 阶段二把 agent 工作流六阶段从顶部独立面板移入**每个 AI 回答气泡内**（每回合重置走一遍），并新增 SENDING 期 live 走查（替换打字指示）。前端交接结论：**契约冻结，后端与模型端无需任何改动** —— 本变更已实现的契约完全覆盖阶段二全部需求，阶段二是纯前端重构。

## What（对后端：无改动）

前端交接表逐项确认（已对照当前代码核对）：

| 契约项 | 前端用途 | 现状 |
|---|---|---|
| decide 阶段 agent 事件 perceive/analyze/plan/decide 透传 | SENDING 期实时展示"解析意图…"（①意图分类处理中） | ✅ `orchestrate` filter 已放行 thinking + agent |
| `meta.decideReason`（Python 决策自由文本） | ①决策行的 hover 补充说明 | ✅ buildMeta 无条件带出 |
| `meta.questionKps`（List,可空） | ②知识点分析，每回合展示 | ✅ ActionMeta question_kps → SseMetaDTO |
| `meta.masterySignals` | 知识点 chips（KpChips） | ✅ SseMasterySignalDTO camelCase {kpLabel, signal} |
| `meta.type/denied/eval/status` | ①③④⑤⑥ 各阶段点亮判定 | ✅ 既有字段 |

## 唯一新增依赖：decide 事件时序稳定

前端 SENDING 期会连续消费 decide 阶段 agent 事件做 live 走查，**事件时序（perceive→analyze→plan→decide→meta）稳定**成为硬性契约。当前 filter 原样透传保持 Python 顺序，已满足；后续任何改动不得重排/丢序。

## Impact（阶段二）

- **无代码改动**（Java / Python 均不动）；仅本 change 文档固化契约冻结结论。
- 无迁移/回滚动作。
