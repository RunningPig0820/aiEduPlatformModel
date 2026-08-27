# 信号跟题目走

> summary: 信号跟题目走：PENDING 题型照常采信号先落题目表，归属确定后再聚合，不因题型待定丢数据。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-D4-信号跟题目走.md
> 类别：数据关联

---

### 决策 4：信号跟题目走，不跟题型走（关键设计点）

> 检索摘要：信号跟题目走：PENDING 题型照常采信号先落题目表，归属确定后再聚合，不因题型待定丢数据。

PENDING 题型（识别不出的题）**照常采集掌握信号**，先落在题目表；题型归属由聚类后定，**归属确定后再聚合进掌握表**。

**为什么**：PENDING 是「题型暂时没认出来」，不代表「题没做」——答对/答错的信号是确定的，不能因为题型待定就丢。若反过来（信号等题型确定才记），PENDING 高频场景下掌握度会大面积漏采。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§决策 4：信号跟题目走，不跟题型走（关键设计点））｜ 语雀-决策记录.md D19 ｜ 完善文档 05-数据落库与掌握度.md
