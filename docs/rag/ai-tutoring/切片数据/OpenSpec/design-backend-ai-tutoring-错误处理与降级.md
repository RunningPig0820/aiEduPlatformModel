# design-backend-ai-tutoring

> summary: 讲AI答疑的错误处理与降级策略
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 错误处理与降级
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-backend-ai-tutoring-错误处理与降级.md
> 类别：开发难点

---

## 错误处理与降级

- Python decide/generate 调用失败：重试 1 次；仍失败回复"网络波动，请重试"，会话保持 ACTIVE 不断开
- Python 结构化输出兜底：返回 **200 + ActionMeta(type=hint, degraded=true)**（不使用 503），Java 按普通 hint 放行 + 记日志——保证 API 永不返回畸形 ActionMeta
- decide 输出缺字段/非法 type：走默认（type=hint），记日志，不阻断（`degraded` 场景被此逻辑自然覆盖）
- reveal 被护栏拒绝后重决策仍输出 reveal：Java 直接降级为固定思路话术 + count→1
- 掌握度解析 label 失败：不点亮，记日志，收尾标记"待收录"
- round 达 20 后学生继续发言：Java 强制 end(ROUND_LIMIT) 收尾，提示"本轮已结束"
