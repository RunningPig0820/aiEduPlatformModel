# 前端对接说明 — 答疑事件流更新(2026-08-12)

> 对应后端说明:`docs/backend-notice-2026-08-12.md`(若有)/ 契约文档:`docs/ai-tutoring-agent-events.md`
> 背景: 答疑链路已**全关思考模式**并切 `doubao-seed-2-0-mini`,`thinking` 事件不再发送,同时大幅提速。

---

## 一、变更总览

| 变更 | 说明 |
|------|------|
| `thinking` 事件 | **取消**,不再发送(`reasoning_content` 关思考后不返回) |
| 耗时 | decide ~1.5s / generate ~1.2s / 看图全流程 ~3.4s(原 17~48s / 6.5s+ / 50~145s) |
| token 流式 | **不变**,答案仍逐字流出 |
| agent 阶段事件 | **不变**,perceive/analyze/plan/decide/guardrail/memory 照常发送 |

---

## 二、事件时序(完整一轮)

```
decide 阶段:  agent(perceive/analyze/plan) → agent(decide) → meta(ActionMeta) → done
[Java 护栏]:  agent(guardrail)
generate 阶段: meta(action_type) → agent(generate) → token* → done
[Java 落库]:  agent(memory)
```

> 注意: 原时序中的 `thinking*` 已移除,前端按此渲染。

---

## 三、前端需做的适配

### 1. 移除/隐藏"思考过程"面板(必改)
- 不再有 `event: thinking`,折叠面板会一直空白
- 建议: 隐藏该面板;如需保留"思考中"视觉,用 agent 阶段事件替代(见 2)

### 2. 阶段进度可保留(agent 事件仍在)
- `agent(perceive/analyze/plan)` → decide 前 → guardrail → generate → memory
- 可继续渲染"AI 正在做 X"的进度提示

### 3. 静默期占位大幅简化(建议改)
- 之前为长静默做的脉动/长加载动画不再需要
- 建议: 保留 ~1-2s 轻量短占位("AI 思考中…"),去掉长等待动画

### 4. token 打字机保留(不变)
- 答案仍逐 token 流式,现有逐字 reveal 效果保留

### 5. 可选增强
- `done` 后 Java 追加 `agent(memory)`(掌握度落库完成),可展示"已记录你的掌握情况"

---

## 四、实测数据(2026-08,真实模型冒烟 20/20 通过)

| 场景 | decide | generate | 决策 |
|------|--------|----------|------|
| 纯文本引导 | ~1.8s | ~0.9s | hint ✓ |
| 看图解题 | ~2.0s | ~3.1s | approach ✓(读懂题) |
| 换题短路 | 不走模型 | — | switch ✓ |
| 收尾 | ~1.5s | — | end ✓ |

> 全部未降级(degraded=False),reason 完整。

---

## 五、相关文档
- 契约全文:`docs/ai-tutoring-agent-events.md`(第〇节: thinking 已取消)
- 决策依据:`docs/tutoring-streaming-experience.md`(含最终结论 + 模型对比实测)
