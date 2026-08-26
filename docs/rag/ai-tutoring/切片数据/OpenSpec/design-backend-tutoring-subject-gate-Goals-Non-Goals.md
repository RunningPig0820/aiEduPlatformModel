# design-backend-tutoring-subject-gate

> summary: 明确学科判定及模型统一的本期目标与非目标
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-subject-gate
> 类别：项目介绍

---

## Goals / Non-Goals

**Goals:**
- **decide 之前**判定学科（因为不同学科需要不同提示词），学科无关分类器先于数学 decide。
- 非数学题：不建/不续会话、不落题目/掌握度/错误事件，返回「仅支持数学」。
- 学科分类器支持**文本和图片**。
- 三个 LLM 调用统一模型 `doubao-seed-2-0-mini-260428`（temp 0.3）。

**Non-Goals（本期明确不做）：**
- 多学科答疑提示词（本期只支持 math，架构预留 subject 决定提示词的选择点）。
- analyze-question 题型分析的学科过滤。
- subject-classify 的高准确率调优（本期分类器够用即可，误判治理见 Risks）。
