# PENDING 题型照常采信号
> summary: 题型名未识别的题照常采集对错信号落题目表，归属确定后再聚合进掌握表，不因题型待定丢数据。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-边界场景清单-场景21-PENDING题型照常采信号.md
> 类别：数据关联
> 状态：✅

---

### 场景21：PENDING 题型照常采信号（题型未识别不丢）
> 状态：✅
> 检索摘要：题型名未识别的题照常采集对错信号落题目表，归属确定后再聚合进掌握表，不因题型待定丢数据。

| 属性 | 内容 |
|---|---|
| 业务场景 | PENDING 题型照常采信号 |
| 触发条件 | 题目题型识别为 PENDING（未认出） |
| 当前处理 | 信号跟题目走：先落题目表（含对错与引导轮数），canonical 归属确定后再聚合进掌握表（D19） |
| 兜底降级策略 | PENDING 不代表题没做，信号照常采不丢；归属由聚集/人工后续补 |
| 残余风险 | 若前端按「识别失败」丢弃题目，会漏采掌握信号 |
| 证据 | design-backend-question-type-mastery Decision 8 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景21）｜ 语雀-决策记录.md D19 ｜ 完善文档 05-数据落库与掌握度.md ｜ OpenSpec design-backend-question-type-mastery Decision 8（历史设计文档，请核对代码确认实际落地）
