# 坑档案

> summary: 解决50002残留ACTIVE反复重放的问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F3. 50002 残留 ACTIVE 反复重放
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: ai-tutoring/rag-slices/坑档案/坑档案-F3-50002-残留-ACTIVE-反复重放.md
> 类别：开发难点

---

### F3. 50002 残留 ACTIVE 反复重放
**1. 问题现象**：后端清库后本地残留 ACTIVE，发消息仍走旧 id——每次刷新重放"会话已失效"notice，挂载恢复死循环。

**2. 触发流程**：后端清库（删孤儿会话）后，本地 localStorage 仍残留 `ACTIVE` 陈旧条目。挂载时 `useTutoringSession.js:850-873` 找到本地 ACTIVE → `setSessionState('active')` + `reconcileSession(active.id)`。`reconcileSession`（`:664`）调 `getSession(id)`，后端返回 50002。

**3. 根因分析**：旧行为 50002 分支只 `setSessionState('ended')`，**不清 localStorage、不重置 `sessionIdRef`** → `sessionIdRef` 残留 → 发消息仍走旧 id（`send()` 的 `!sessionIdRef.current` 判定不触发 `startSession`）。本质是"**把确定性错误（会话不存在）当历史回看处理，没清理本地状态**"。

**4. 排查过程**：从"反复重放已失效会话"反推 → 看 50002 分支行为（只 setState('ended')）→ 确认未清 localStorage、未重置 id。

**5. 解决方案 & 改动点**：提交 `c8fcd90`：
- 新增 `removeStoredSession(id)` helper（`:59-67`）
- `reconcileSession` 与 `loadSession` 的 50002 分支改为：`removeStoredSession(id)` + `resetState()`（回新建态）+ `setNotice('会话已失效,可发起新会话')`（`:704-711`、`:826-831`）
- 与接口失败兜底区分：网络失败仍保留本地快照

**6. 面试口述要点**：讲"**确定性错误要清理本地状态，网络错误才保留快照**"——50002 是"会话不存在"，本地残留必须清；网络失败才是"暂不可用"应保留。技术权衡：区分错误类型（确定性 vs 瞬时）决定本地状态策略。踩坑收获：**本地缓存的生命周期要跟后端状态对齐，过期条目要能自愈**。

---
