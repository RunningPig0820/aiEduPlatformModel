# design-backend-add-tutoring-session-history-backend

> summary: 面试问答：答疑会话历史后端的getSession接口无需改动
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D5. `getSession` 不改
> 模块: ai-tutoring ｜ 节: design-backend-add-tutoring-session-history-backend

---

### D5. `getSession` 不改

详情内容加载由前端经 `transcriptUrl` 拉 COS 完成；后端 `getSession` 已返回签名 `transcriptUrl` + Redis recentMessages 兜底。本变更零改动。
