# Design: Tutoring Agent Workflow Backend

## Context

前端 `show-tutoring-agent-workflow` 需要后端补齐两类契约（见该 change design D2/D3/D5）：
- decide agent 事件透传（"本轮意图"的意图解析 live 数据源）
- meta 新字段（"为什么" hover、知识点分析、掌握度信号）

**现状（已逐条核对代码）**：
- `api/tutoring.py` 已发 `perceive → analyze(processing) → plan(processing) → [thinking*] → agent(decide) → meta`，Java `orchestrate` filter 原只放行 thinking，agent 事件全丢。
- `ActionMeta` 原无 `reason`/`questionKps`；`ACTION_META_MAPPER`（FAIL_ON_UNKNOWN_PROPERTIES=false）容忍并静默丢弃 Python 的 `reason`。
- `SseMetaDTO` 原无 `decideReason`/`questionKps`/`masterySignals`；`reason` 已占位为"护栏拒绝原因"（buildMeta 仅在拒绝时 set）。
- `SseEvalDTO` 无 `masterySignals` → 前端 `meta.eval.masterySignals` 恒 undefined（KpChips 一直无数据）。
- 领域 `MasterySignalItem.kpLabel` 标 `@JsonProperty("kp_label")` → 直接放进 `SseMetaDTO.masterySignals` 会序列化成 snake_case，不符合前端 camelCase 契约。

**本变更落地方式**：后端契约已在工作区实现（filter 透传 + ActionMeta/SseMetaDTO/SseMasterySignalDTO + buildMeta 接线，TutoringAppServiceTest 42/42、TutoringLlmClientTest 3/3 绿）。本 change 作为**后端契约的归属变更**，固化设计决策 + 补齐契约文档（`tutoring-agent-events/api.md`）。

## Goals / Non-Goals

**Goals:**
- decide agent 事件透传前端（意图解析 live 数据源）。
- meta 补齐 `decideReason`（Python 理由）/`questionKps`/`masterySignals`，修复 KpChips 契约缺口。
- 全部 additive / 透传，不改既有答疑行为。

**Non-Goals:**
- 不做前端面板（属前端 change `show-tutoring-agent-workflow`）。
- 不改 Python decide（`question_kps` 属前端 change tasks 2.1，独立部署）。
- 不改护栏/类型/轮次/收尾逻辑。

## Decisions

### D1. decide filter: thinking + agent

`orchestrate` decide filter（407 行）：

```java
.filter(e -> "thinking".equals(e.event()));                                            // 改前：只中继 thinking
.filter(e -> "thinking".equals(e.event()) || "agent".equals(e.event()));               // 改后：thinking + agent
```

- Python 的 `meta`/`done` 事件仍被消费/丢弃（meta 捕获进 metaSink，done 丢弃）——前端看到的是 Java 重建的 meta。
- 前端收到序列：

  ```
  agent(perceive) → agent(analyze) → agent(plan) → [thinking*] → agent(decide)
      → agent(guardrail) → meta → agent(generate) → token* → agent(memory) → done
  ```

- 注意：`agent(guardrail)` 在 `meta` **之前**（postDecide 先发 guardrail 事件，再进 buildStream）。前端"解析中"状态应以"decide 阶段 agent 已到、meta 未到"为判据，不依赖 meta 紧跟 agent(decide)。
- 换题短路/降级兜底：Python `perceive/analyze/plan` 恒发（`api/tutoring.py` 无条件先发），**无 thinking、无 `agent(decide)`**（`agent(decide)` 只在 thinking 事件时发出，短路/降级仅 yield meta），**仅 meta 仍到**。前端 spec 中"换题/降级轮无 decide agent"场景措辞应改为"无 thinking、无 agent(decide)"。

### D2. 字段命名定案：`decideReason`（Python 理由）+ `reason` 保持护栏语义

**不重定义 `SseMetaDTO.reason`**（护栏拒绝原因不变），**新增 `decideReason`** 承载 Python 决策自由文本：

- `buildMeta` **无条件** `meta.setDecideReason(action.getReason())`（null ok）。
- `reason`（护栏拒绝原因 `answerCountInsufficient` / `roundLimitExceeded` / `safetyFlagHit`）语义与既有行为不变，仍仅拒绝时 set。
- `denied`（原始请求 type，如 reveal）保留——前端 D3 表用 `denied` + `answerRequestCount` 确定性推导"护栏拦"主文案，不依赖两个 reason 字段。

选择 `decideReason` 而非方案 A（`reason`=Python 理由 + `deniedReason`=护栏原因）：
- **additive，零重定义**：`reason` 既有语义不动，无回归面；方案 A 需改 `reason` 语义（虽当前前端不读，但语义切换有隐性契约变动）。
- **命名更准**：该字段就是 decide 步输出的理由 → `decideReason` 直白；`reason`（护栏 code）与 `decideReason`（Python 文本）语义清晰可分。
- **实现与前端已提交**：前端 change 文档与 Java 实现已按 `decideReason` 落地（测试 42/42 绿），保持现状零代码重做。

**同一轮对比（第 1 次要答案被护栏拦）：**

```
本变更: type="approach" denied="reveal" reason="answerCountInsufficient" decideReason="学生第 1 次明确要求答案"
方案 A: type="approach" denied="reveal" reason="学生第 1 次明确要求答案" deniedReason="answerCountInsufficient"
```

- 两条方案主文案相同（`denied`+计数推导），差别只在 hover 数据源字段名。
- 本变更 `decideReason` = Python 自由文本（hover），`reason` = 护栏 code（前端不消费，调试用）。

### D3. masterySignals 序列化（隐性坑）：新建 SseMasterySignalDTO

领域 `MasterySignalItem.kpLabel` 标了 `@JsonProperty("kp_label")`（Java↔Python 内部契约 snake_case）。若直接把 `List<MasterySignalItem>` 放进 `SseMetaDTO.masterySignals`，Jackson 会按字段上的 `@JsonProperty` 序列化成 `{kp_label, signal}`——**不符合前端 camelCase 契约**（spec 要求 `{kpLabel, signal}`）。

- 新建 `SseMasterySignalDTO {kpLabel, signal}`（camelCase，sse dto 包）。
- `buildMeta` 映射：`action.getMasterySignals() → List<SseMasterySignalDTO>`（kpLabel/signal 一一透传）。

### D4. questionKps

- `ActionMeta` 新增 `@JsonProperty("question_kps") List<String> questionKps`（Python decide 模型读题顺手列涉及知识点，可空，不额外调用 LLM）。
- `SseMetaDTO.questionKps`（List<String>）透传。
- Python 未下发时（后端先部署/未改 Python）→ Java 透传 null → 前端显示占位"—"（前端 design D4，数据驱动）。

### D5. 契约文档与测试

- `tutoring-agent-events/api.md`（本 change 剩余真实工作）：line 77 decide agent 事件"仍不中继"改为"透传"；meta 事件示例补 `decideReason`/`questionKps`/`masterySignals` 字段说明。
- 后端测试已在工作区更新：`sendMessage_decideThinkingRelayedFirst` 断言 decide agent 事件透传；meta 新字段断言（decideReason/questionKps/masterySignals）——TutoringAppServiceTest 42/42、TutoringLlmClientTest 3/3 绿。

## Risks / Trade-offs

- **decide agent 事件快闪**：decide ~1.5s，live 状态短暂即定型 → 前端定型后保留结果（✓ 决策结果 + 为什么），不人为放慢。
- **decideReason 质量**：Python 自由文本可能为空/跑题 → 前端主文案用确定性推导，decideReason 仅 hover，空则隐藏。
- **双 reason 字段**：`reason`（护栏 code）与 `decideReason`（Python 文本）同驻 meta，语义需在文档/命名上分清——本 design D2 与 api.md 已明确，前端只消费 `decideReason`。
- **SseMasterySignalDTO 新增**：前端独立消费，纯新增字段，向后兼容。

## Migration Plan

1. Java：filter + `ActionMeta`/`SseMetaDTO`/`SseMasterySignalDTO` + `buildMeta`（全部 additive，已实现）→ 提交。
2. `tutoring-agent-events/api.md` 契约更新（本 change 5.3）。
3. 前端 change（`show-tutoring-agent-workflow`）接新字段 → 联调。
4. 回滚：后端字段 additive，回滚仅损失新展示，不破坏既有答疑。

## Open Questions

无（与前端 change D2/D3/D4/D5 对齐；字段命名已定 `decideReason`）。

---

# 阶段二（2026-08-13）：契约冻结确认

## Context

前端阶段二（展示位重构：六阶段进气泡、每回合重置、SENDING live 走查）为纯前端重构，交接结论：**契约冻结，后端/模型端零改动**。阶段一（D1-D5）实现即阶段二所需的全部后端契约。

## 冻结确认（对 D1-D5 的验证，已对照代码）

| 决策 | 现状 |
|---|---|
| D1 decide filter `thinking + agent` | ✅ `TutoringAppService.orchestrate` 407 行，decide agent 事件按 Python 顺序原样透传 |
| D2 `decideReason`（Python 理由） | ✅ buildMeta 无条件 set；`reason`（护栏 code）语义不变，仅拒绝时 set |
| D3 `SseMasterySignalDTO` camelCase | ✅ `meta.masterySignals` 序列化为 `{kpLabel, signal}`（前端只读此字段，不再读 `meta.eval.masterySignals`） |
| D4 `questionKps` | ✅ ActionMeta question_kps → SseMetaDTO，可空，前端占位"—" |

## 新增硬性契约（前端阶段二依赖）

**decide 事件时序稳定**：前端 SENDING 期连续消费 decide 阶段 agent 事件做 live 走查，序列 `perceive→analyze→plan→decide→meta` 不得重排、不得丢序。当前 filter 透传满足；后续改 decide 消费链路必须回归此序列。

## Non-Goals（阶段二）

- 不做任何后端 / Python 改动，不新增字段、不新增事件。
- 不做展示位实现（属前端 `AgentTurnFlow` / live 管线）。
