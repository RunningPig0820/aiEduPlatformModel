# 坑档案

> summary: 解决会话永久卡发送中问题，落库异常降级加前端看门狗
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J1. 会话卡死 SENDING（P0 防卡死）
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J1. 会话卡死 SENDING（P0 防卡死）
**1. 问题现象**：会话永久卡"发送中"，前端无法恢复（会话 116 卡死根因）。学生发一条消息后 UI 永远转圈，发不了下一条。

**2. 触发流程**：`start/sendMessage/requestAnswer`（TutoringController → `TutoringAppService.java:206/267/299`）→ `orchestrate`（`:578`）→ `llmPort.decideStream(ctx)` 中继（**SSE 200 已发出**）→ meta 到达 → `postDecide`（`:618`）→ `applySideEffects` 落库（DB）→ `buildStream` → `llmPort.generate`。任意环节抛异常都会落到 `orchestrate` 的 `onErrorResume(e -> handleDecideFailure(session, e))`（`:614`）。

**3. 根因分析**：修复前 `handleDecideFailure` 只对 `TutoringAgentException` 降级，其他异常（DB 落库等）原样 `Flux.error(e)` 上抛——**SSE 200 已发出后直接断连，前端收不到 meta/done 终态** → 永久卡 SENDING。本质是"流已建立但无终态事件"。

**4. 排查过程**：从"永久 SENDING"反推——前端等 done 终态；Java 看 orchestrate 日志发现落库异常被原样抛给 SSE；确认断连发生在 `applySideEffects` DB 落库环节。

**5. 解决方案 & 改动点**（`TutoringAppService.java`）：
- `postDecide` 内 `applySideEffects + save` 包 try-catch，异常**降级继续不阻断 SSE**（`653-656`）
- `handleDecideFailure` 不再区分 agent/非 agent：`session.getId()==null` 才重抛，否则一律 `friendlyErrorStream(session)` 兜底终态流（meta + 「网络波动，请重试」token + done），**会话保持 ACTIVE 可重试**（`676-686`）
前端配合 F1 加 SSE 看门狗。

**6. 面试口述要点**：讲"**SSE 会话的终态保证**"——流式接口最怕"连接活着但没终态"。技术权衡：落库失败降级继续（数据最终一致）优先于阻塞流式体验；任何异常都兜底终态流让前端可恢复。踩坑收获：**流式协议必须有 done/error 终态契约，异常路径不能静默断流**。

---
