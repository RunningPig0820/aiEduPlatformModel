# 坑档案

> summary: 解决刷新后找不到ACTIVE会话的问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F2. 刷新后找不到 ACTIVE 会话 / 同题孤儿会话
> 模块: ai-tutoring ｜ 节: 坑档案

---

### F2. 刷新后找不到 ACTIVE 会话 / 同题孤儿会话
- **坑**：generate 卡死/中断时本轮无 done，只在 done 落 localStorage → 刷新后 sessionId 归 null → 下条消息重复建会话。
- **解决**：**meta 到达即持久化**（`handleMeta` 收到 sessionId 立即写 localStorage，幂等），刷新后挂载恢复续走 sendMessage。
- **证据**：`873bd78`；`useTutoringSession.js:258-268`。
