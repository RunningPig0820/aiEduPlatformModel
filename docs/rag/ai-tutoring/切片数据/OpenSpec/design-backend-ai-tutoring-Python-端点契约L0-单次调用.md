# design-backend-ai-tutoring

> summary: 答疑Python端点契约的实现与调用规则说明
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Python 端点契约（L0 单次调用）
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

## Python 端点契约（L0 单次调用）

> 实现位于 `ai-edu-ai-service` 独立答疑模块；本仓库定义契约。Java 通过内部 token 调用，Python 不碰任何数据源。`subject_hint` 恒传 `math`。
