# 解析管线查询统一走别名

> summary: 解析/聚合/vote 查询统一走别名，别名命中与 canonical 等价，canonical 名只增不改。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D4-解析管线查询统一走别名.md
> 类别：数据关联

---

### D4：解析管线②/聚合/vote 的查询统一走别名

> 检索摘要：解析/聚合/vote 查询统一走别名，别名命中与 canonical 等价，canonical 名只增不改。

`QuestionTypeRepository` 增 `findByTopicLabelOrAlias(String)`、`findTopTopicLabels(int)`（D1 词表用）。别名命中与 canonical 命中等价返回 `QuestionType`，调用方无感知。**canonical 名只增不改**（合并只加别名、不改主题名，避免破坏既有引用）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D4）｜ 语雀-决策记录.md D22 ｜ 完善文档 06-题型动态聚集与向量.md
