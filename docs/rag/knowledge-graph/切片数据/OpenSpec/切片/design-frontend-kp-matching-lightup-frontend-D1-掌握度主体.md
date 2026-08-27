# 掌握度主体

> summary: 掌握度以题型为主体展示，四类明细每项是题型 topicLabel，知识点掌握度由题型→知识点映射派生，不直接观测。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-frontend-kp-matching-lightup-frontend-D1-掌握度主体.md
> 类别：数据存储

---

### 1. 掌握度主体 = 题型（知识点派生）

> 检索摘要：掌握度以题型为主体展示，四类明细每项是题型 topicLabel，知识点掌握度由题型→知识点映射派生，不直接观测。

掌握度 SHALL 以**题型**为主体展示：四类明细（已掌握/练习中/待巩固/待确认）的每一项是**题型**（topicLabel），不是知识点。知识点掌握度不由直接观测得到，而由「题型→知识点映射」派生。

理由：题型是掌握度的直接观测主体——学生做题，观测到的是「会不会做鸡兔同笼」这类题型能力；知识点是题型背后的抽象，学会一个题型只覆盖知识点的局部（ratio < 1）。把掌握度直接落在知识点上，等于把「会做鸡兔同笼」夸大成「掌握二元一次方程」。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-matching-lightup-frontend.md`（§1. 掌握度主体 = 题型（知识点派生））
