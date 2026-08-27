# 累计平均

> summary: 掌握程度=累计平均（历史正确率可解释稳定，一次作答算一次，打折作用于 score）。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-question-type-mastery-D6-累计平均.md
> 类别：数据存储

---

### 决策 6：掌握程度 = 累计平均（每道题加权）

> 检索摘要：掌握程度=累计平均（历史正确率可解释稳定，一次作答算一次，打折作用于 score）。

```
题型掌握表: { topicLabel | source(ai/题库) | mastery% | trainCount }

更新：new = old × (n/n+1) + score × (1/n+1)   // n = 当前训练数
      trainCount += 1
```

- 累计平均 = 历史正确率，可解释、稳定、不抖动。
- **一次作答算一次**（不做题目去重）——同一道题做两次，两次都计入训练数，反映真实练习量。
- 打折作用于 `score`（前几次 70/80/100 递减权重），不作用于结果——避免「第一题答错 → 题型 0%」的假低 / 假高。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-question-type-mastery.md`（§决策 6：掌握程度 = 累计平均（每道题加权））｜ 语雀-决策记录.md D3 ｜ 完善文档 05-数据落库与掌握度.md
