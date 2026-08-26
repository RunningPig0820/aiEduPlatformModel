# design-python-tutoring-subject-gate-python

> summary: 说明学科分类模块与decide模块的边界，不侵入调用链
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 5. 与 decide 的边界(不复用、不侵入)
> 模块: ai-tutoring ｜ 节: design-python-tutoring-subject-gate-python
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-python-tutoring-subject-gate-python-5-与-decide-的边界不复用不侵入.md
> 类别：架构设计

---

### 5. 与 decide 的边界(不复用、不侵入)

subject-classify **独立于 decide**,不改 `_DECIDE_SYSTEM`、不改 decide/generate 调用链。学科判定在 Java 侧完成分流,Python 只提供分类能力。多学科提示词是 Java 本期 Non-Goal,Python 同理不预埋。
