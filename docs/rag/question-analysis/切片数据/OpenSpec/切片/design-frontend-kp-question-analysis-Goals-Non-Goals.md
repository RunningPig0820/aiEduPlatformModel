# 目标与非目标

> summary: 目标=题型分析页（贴题→识别题型→关联知识点）+学生确认喂聚合+先纯分析；非目标=管理端审核/掌握度标注/动老方案/改聚合。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-Goals-Non-Goals.md
> 类别：项目介绍

---

### 目标与非目标

> 检索摘要：目标=题型分析页（贴题→识别题型→关联知识点）+学生确认喂聚合+先纯分析；非目标=管理端审核/掌握度标注/动老方案/改聚合。

**Goals:**
- 智能练习下「题型分析」页：贴题/拍题 → 单题分析（识别题型 → 关联知识点清单）。
- 学生可在题型分析页「确认/纠正」题型↔知识点关联 → 落 `student_vote` → 喂聚合任务（产品流程闭环）。
- 先纯分析展示；掌握度标注接口预留。

**Non-Goals:**
- 管理端/老师端全局审核（`kp-pending-review`）本期不做，学生确认只走个人观测。
- 掌握度标注第一版不做（`kp-coverage` 数据到位后叠加，接口预留）。
- 不动老方案已收口的掌握度/知识点总览/澄清卡行为。
- 聚合任务本身不改（已消费 STUDENT_VOTE；手动触发/source 加权为可选后续）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§目标与非目标）｜ 语雀-决策记录.md D21 ｜ 完善文档 02-题型分析主流程怎么走.md
