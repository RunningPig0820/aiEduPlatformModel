# 坑档案

> summary: 解决刷新后找不到ACTIVE会话的问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F2. 刷新后找不到 ACTIVE 会话 / 同题孤儿会话
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: ai-tutoring/rag-slices/坑档案/坑档案-F2-刷新后找不到-ACTIVE-会话-同题孤儿会话.md
> 类别：开发难点

---

### F2. 刷新后找不到 ACTIVE 会话 / 同题孤儿会话
**1. 问题现象**：generate 卡死/中断时本轮无 done，刷新后 sessionId 归 null → 下一条消息重复建会话，历史里堆出同题单轮孤儿。

**2. 触发流程**：`send()`（`useTutoringSession.js:493`）无 `sessionIdRef` → `startSession`；有 → `sendMessage`（路由判定在 `:527-531`）。会话 id 只在 `handleDone`（`:419`）持久化到 localStorage。挂载恢复在 `:850-873`：从 localStorage 找 `status === 'ACTIVE'` 的会话。

**3. 根因分析**：generate 卡死（后端曾漏 `.timeout`，本轮无 `done`）→ `handleDone` 不执行 → `persistSession` 不落库 → 刷新后 localStorage 无 ACTIVE 会话 → `sessionIdRef` 归 null → 下一条消息走 `startSession` 重复建会话。本质是"**持久化时机太晚（只等 done）**"。

**4. 排查过程**：从"历史里同题单轮孤儿"反推 → 看会话 id 持久化时机（只在 handleDone）→ 确认卡死轮无 done 时 id 未落库。

**5. 解决方案 & 改动点**：提交 `873bd78`——`handleMeta` 收到 `meta.sessionId` 即 `persistSession(meta.sessionId, messagesRef.current, 'ACTIVE')`，**不等 done**。`writeStoredSession` 按 id 幂等更新（`useTutoringSession.js:45-56`），刷新后挂载恢复能找回 ACTIVE 会话续走 `sendMessage`。

**6. 面试口述要点**：讲"**关键状态要在最早可得的时机持久化**"——sessionId 在 meta 到达就有，别等 done。技术权衡：meta 即持久化（幂等）换取刷新可恢复，代价是提前落库（会话可能未完成就存 ACTIVE）。踩坑收获：**"恢复能力"的边界 = 状态持久化的时机**；卡片式恢复要拿"最早可靠信号"而非"最完整信号"。

---
