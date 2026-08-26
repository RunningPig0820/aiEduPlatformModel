# design-python-tutoring-subject-gate-python

> summary: 介绍学科分类接口的后端契约与模型现状
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-python-tutoring-subject-gate-python
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-tutoring-subject-gate-python-Context.md
> 类别：架构设计

---

## Context

- **后端契约(已冻结)**:`POST /api/tutoring/subject-classify`,请求 `{content, image_url}`(至少一个非空),响应 `{"subject": "..."}`;失败/异常 → 空结果,Java 按 math 放行。不对前端开放,仅 Java 桥调用。
- **subject 闭集(K12 十值,2026-08 扩)**:`math`/`physics`/`chemistry`/`biology`/`chinese`/`english`/`politics`/`geography`/`history`/`other`。本期 Java 只放行 math,其余跳过;显式枚举便于记录真实学科 + 后续分学科答疑。⚠️ **后端 DTO 需同步扩**(Java 严格枚举反序列化遇 chinese 等新值会报错,见 Risks)。
- **现有成熟模式**:question_understand / vector 均为 stateless 小端点(不碰 MySQL/KG),Java 经桥调用。subject-classify 完全复用该模式。
- **模型现状**:decide(`TUTORING_DECIDE_MODEL`)与 question_understand(`_UNDERSTAND_MODEL`)均为 `doubao-seed-2-0-mini-260428` / temp 0.3 —— 三个统一模型现状已满足两个,subject-classify 沿用。
- **关键已知**:doubao mini **默认开思考**(先写草稿再答),question_understand 曾因未关思考导致 32s+ 卡顿(2026-08-19 已修复:关思考 + 20s 超时 + 关 SDK 重试)。subject-classify 同为 stateless 快调用,**必须照搬该修复**,否则学科门变成 30s+ 卡点。
