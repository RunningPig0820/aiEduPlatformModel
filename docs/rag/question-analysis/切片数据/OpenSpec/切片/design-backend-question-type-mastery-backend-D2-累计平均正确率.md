# 累计平均正确率

> summary: 掌握度算法替换 max 单调不减，采用累计平均正确率，实现可解释真实正确率统计，规避掌握度虚高。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D2-累计平均正确率.md
> 类别：数据存储

---

### Decision 2：掌握度 = 累计平均正确率（替代 max 单调不减）

> 检索摘要：掌握度算法替换 max 单调不减，采用累计平均正确率，实现可解释真实正确率统计，规避掌握度虚高。

```
new = old × n/(n+1) + score × 1/(n+1)     // n = train_count
train_count += 1
```

- **为什么累计平均**：正确率视角，可解释、稳定、不抖动。「某题型练 10 道对 6 道 = 64%」业务含义通透。
- **备选**：max 单调不减（现状，置信度视角，答错不降分）——与「可追溯正确率」诉求冲突；EWMA——比累计平均更「敏感近期」，但更难解释、难回查。
- **一次作答算一次**：不做题目去重，同一道题做两次计两次训练数（反映真实练习量）。
- **打折作用于 score 不作用于结果**（避免「第一题答错 → 题型 0%」的假低）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 2）｜ 语雀-决策记录.md D3 ｜ 完善文档 05-数据落库与掌握度.md
