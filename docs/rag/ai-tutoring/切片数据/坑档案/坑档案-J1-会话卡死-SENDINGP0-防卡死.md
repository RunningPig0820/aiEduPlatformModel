# 坑档案

> summary: 解决会话永久卡发送中问题，落库异常降级加前端看门狗
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J1. 会话卡死 SENDING（P0 防卡死）
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J1. 会话卡死 SENDING（P0 防卡死）
- **坑**：会话永久卡"发送中"，前端无法恢复（会话 116 卡死根因）。
- **根因**：SSE 200 已发出后 `Flux.error` 直接断连，前端收到流结束却无终态 → 永久 SENDING。
- **解决**：**落库副作用异常降级继续** + **非 agent 异常（含 DB 落库）也兜底终态流**（meta + 兜底 token + done），会话保持 ACTIVE 可重试；前端再加 **SSE 看门狗**。
- **证据**：`d087524`；`TutoringAppService.java:669-686`（handleDecideFailure）；前端 `157b704`。
