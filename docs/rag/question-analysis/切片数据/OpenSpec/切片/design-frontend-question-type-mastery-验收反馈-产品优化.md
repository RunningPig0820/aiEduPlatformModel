# 验收反馈：产品优化

> summary: 产品验收 4 条已决：纯题型聚合视图、后端分页、时间列用 updatedAt、定名「题型掌握」。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-验收反馈-产品优化.md
> 类别：操作流程

---

### 验收反馈：产品优化（逐个解决）

> 检索摘要：产品验收 4 条已决：纯题型聚合视图、后端分页、时间列用 updatedAt、定名「题型掌握」。

> 产品验收反馈 4 条。逐条记录归属（前端/后端）与待决点。
>
> **已决**：
> ① **定位 = 纯题型聚合视图**——掌握度页去「查看题目」下钻（题目明细留给未来「学习记录」页，tasks 7 降级）；
> ② **分页 = 后端分页**——题型会越来越多，前端全量渲染/切页撑不住（tasks 4.5 后端 + 12.2 前端请求式）；
> ③ **时间列用已有 `updatedAt`**——getMastery 已返回最近作答时间，无需后端加字段（tasks 12.4）。
>
> 全部已决：**A** 定名「题型掌握」（产品拍板）；**B/C/D** 已完成（后端分页 + 前端对接）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§验收反馈：产品优化（逐个解决））
