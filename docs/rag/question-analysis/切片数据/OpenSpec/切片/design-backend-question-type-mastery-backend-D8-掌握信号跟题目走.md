# 掌握信号跟题目走

> summary: 掌握信号跟题目走：PENDING 题型照常采信号落题目表，归属确定后再聚合，不因题型待定丢数据。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D8-掌握信号跟题目走.md
> 类别：数据存储

---

### Decision 8：掌握信号跟题目走，不跟题型走

> 检索摘要：掌握信号跟题目走：PENDING 题型照常采信号落题目表，归属确定后再聚合，不因题型待定丢数据。

- 题型名未识别（PENDING）的题**照常采集信号**，落题目表；题型归属确定（归一/后续人工）后再聚合进掌握表。
- **为什么**：PENDING 是「题型暂时没认出」，不代表「题没做」——答对/答错信号是确定的，不能因题型待定就丢。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 8）｜ 语雀-决策记录.md D19 ｜ 完善文档 05-数据落库与掌握度.md
