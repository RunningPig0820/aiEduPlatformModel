# design-python-ai-tutoring

> summary: 解决Python答疑的无状态上下文压缩与截断问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 10. 无状态与上下文压缩
> 模块: ai-tutoring ｜ 节: design-python-ai-tutoring

---

### 10. 无状态与上下文压缩

Python 无状态,Java 每次传全量上下文。`context.py` 做历史截断(保留最近 ~12 条 + 当前题目恒在)+ snapshot 注入 top-N(防快照体积撑爆窗口)。
