# design-backend-ai-tutoring

> summary: 讲AI答疑的安全过滤两层处理规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 安全过滤
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> 类别：开发难点

---

## 安全过滤

Java 侧两层：① 本地关键词（自伤/暴力等）→ 直接终止转人工标记；② decide 输出 `safety_flag` 字段（高危内容标记），Java 判定后终止。对话脱敏、PII 合规沿用用户域约定。
