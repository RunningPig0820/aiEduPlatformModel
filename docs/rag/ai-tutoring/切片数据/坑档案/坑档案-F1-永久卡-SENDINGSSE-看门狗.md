# 坑档案

> summary: 解决SSE流异常关闭导致前端永久卡SENDING问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F1. 永久卡 SENDING（SSE 看门狗）
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: rag-slices/ai-tutoring/坑档案/坑档案-F1-永久卡-SENDINGSSE-看门狗.md
> 类别：开发难点

---

### F1. 永久卡 SENDING（SSE 看门狗）
**1. 问题现象**：后端异常静默关流，前端永久"发送中"，学生无法继续（会话 116 实测复现）。

**2. 触发流程**：`ChatInput`(onSend) → `AiQa.jsx` `handleSend` → `useTutoringSession.js` `send()` → `setPhaseBoth('SENDING')` → `tutoringApi.sendMessage(sessionId, text, handlers)` → `tutoring.js` `streamRequest`（fetch POST）→ `readSSE(response, handlers)`。后端轮次中途异常（如副作用落库 DB 异常，非 TutoringAgentException）会静默关流：SSE 已 200、但无 `done`/`error` 事件。

**3. 根因分析**：旧 `readSSE`（提交 `157b704` 移除的代码）：`while (!cancelled)` 循环读到 `done` 后 `break`，最后只处理 `if (cancelled)` 分支，**对「EOF 但无终态事件」无任何兜底**，不回调 `onError`，`phase` 永为 `SENDING`。本质是"前端只认 done，不认 EOF/超时"。

**4. 排查过程**：从"永久 SENDING"反推 → 抓 SSE 网络流发现后端已断但前端无任何回调 → 看 readSSE 的 EOF 分支确认静默 break。

**5. 解决方案 & 改动点**：提交 `157b704`——`readSSE` 抽到 `api/modules/tutoringSse.js`（纯模块，可独立 Playwright 单测），加两道兜底：
1. 流结束（EOF）但没收到 done/error → `onError({ code: 'SSE_EOF' })`「连接中断，请重试」
2. 看门狗：`watchdogTimeout` 内无任何字节 → `onError({ code: 'SSE_TIMEOUT' })`「答疑响应超时，请重试」+ `reader.cancel()`
错误进入 `handleTurnError` → `setPhaseBoth('IDLE')` 回退可重试态，最近 user 消息标记 `retryable`。

**6. 面试口述要点**：讲"**前端对流式协议也要有终态兜底**"——后端保证终态（J1），前端再加看门狗双保险。技术权衡：EOF 判失败 + 超时看门狗 + 回退可重试态，把"卡死"变成"可重试"；看门狗用"无字节"而非"无事件"判定，抗思考长停顿。踩坑收获：**SSE 客户端必须有 EOF/超时两条兜底，别只依赖 done 事件**。

---
