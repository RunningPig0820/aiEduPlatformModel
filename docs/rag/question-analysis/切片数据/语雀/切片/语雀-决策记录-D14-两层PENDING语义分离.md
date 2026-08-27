# 两层PENDING语义分离
> summary: 区分 analyze-question 与 getMastery 的 PENDING 语义，不再复用同一个状态字段；识别失败与掌握度未归属是两类业务状态。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-决策记录-D14-两层PENDING语义分离.md
> 类别：数据存储
> 状态：✅
> entry_id: D14
> source_doc: 语雀-决策记录.md
> tags: ["D14","掌握度口径","status_done"]

---

### D14 两层 PENDING 语义分离

> 状态：✅
> 检索摘要：区分 analyze-question 与 getMastery 的 PENDING 语义，不再复用同一个状态字段；识别失败与掌握度未归属是两类业务状态。

| 属性 | 内容 |
|---|---|
| 背景 | analyze-question 与 getMastery 都用 PENDING 但含义相反 |
| 演进 | 定稿，两套 PENDING 语义完全解耦 |
| 拍板理由 | analyze PENDING=题型没认出（展示候选/空态）；getMastery PENDING=题型已练、知识点待确认；绝不共用一个判断变量 |
| 系统影响 | 前端状态展示分层判断，识别失败不查掌握度 |
| 证据 | 语雀-方案设计2-问题1 坑2 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D14）｜ 语雀-方案总揽.md §8.5 ｜ 完善文档 02-题型分析主流程怎么走.md ｜ 坑档案 J-QT3-两层PENDING语义冲突
