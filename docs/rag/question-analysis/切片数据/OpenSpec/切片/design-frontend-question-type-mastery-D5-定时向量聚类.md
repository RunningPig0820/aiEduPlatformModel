# 定时向量聚类

> summary: 题型名定时向量聚类 per 学生收敛 canonical（alias 鲁棒，误差可容忍，全局题库后续独立）。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-D5-定时向量聚类.md
> 类别：数据关联

---

### 决策 5：题型名统一 = 定时向量聚类（per 学生）

> 检索摘要：题型名定时向量聚类 per 学生收敛 canonical（alias 鲁棒，误差可容忍，全局题库后续独立）。

学生各入口产生的题型名可能是 alias（"相遇问题"/"行程问题"）。**定时任务**用向量匹配把同一学生的题型收敛成一个 canonical 名。

**为什么用向量而不用规则**：题型名是 LLM 生成的自由文本，无规范枚举；向量匹配对 alias 鲁棒。**误差可容忍**——因为掌握度是百分比聚合，个别题归错题型只影响该题权重，不造成整体语义崩坏。

**粒度：per 学生**。每个学生自己的题型别名收敛为自己的题型行；不做跨学生全局题型库（那是聚合任务的后续独立功能）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§决策 5：题型名统一 = 定时向量聚类（per 学生））｜ 语雀-决策记录.md D6 ｜ 完善文档 06-题型动态聚集与向量.md
