# 坑档案

> summary: 解决50002残留ACTIVE反复重放的问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F3. 50002 残留 ACTIVE 反复重放
> 模块: ai-tutoring ｜ 节: 坑档案

---

### F3. 50002 残留 ACTIVE 反复重放
- **坑**：后端清库后本地残留 ACTIVE，发消息仍走旧 id。
- **解决**：50002 是确定性响应（非网络失败）→ 清理 localStorage 陈旧条目 + 回新建态。
- **证据**：`c8fcd90`；`useTutoringSession.js:704-718`。
