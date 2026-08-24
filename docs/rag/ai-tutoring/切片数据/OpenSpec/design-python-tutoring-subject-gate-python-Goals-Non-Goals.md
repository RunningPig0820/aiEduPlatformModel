# design-python-tutoring-subject-gate-python

> summary: 明确学科分类功能的目标与非目标范围
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-python-tutoring-subject-gate-python

---

## Goals / Non-Goals

**Goals:**
- 学科无关小分类器:只判学科,不做任何解题。
- 文本 + 图片双通道(无图纯文本 / 有图多模态)。
- 闭集 subject(5 值);失败/超时/非法输出 → 空 subject(Java 放行)。
- 模型统一 doubao mini / 0.3;关思考 + 20s 内部超时 + 关 SDK 重试。
- 绝不抛异常(stateless 端点模式)。

**Non-Goals(本期):**
- 多学科答疑提示词(Java 侧本期只放行 math,Python 只做分类不做学科解题)。
- subject 高精度调优(后端 RisK:误判治理后续做)。
- analyze-question 题型分析的学科过滤(后端明确不涉及)。
