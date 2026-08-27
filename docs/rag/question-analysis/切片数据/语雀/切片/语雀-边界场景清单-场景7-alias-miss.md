# alias miss
> summary: analyze 返回原始题型名和掌握表 canonical 不一致，需要后端输出 canonical 做等值匹配，匹配失败静默展示未开始，容易造成学生困惑。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-边界场景清单-场景7-alias-miss.md
> 类别：开发难点

---

### 场景7：alias miss（题型名不匹配）
> 检索摘要：analyze 返回原始题型名和掌握表 canonical 不一致，需要后端输出 canonical 做等值匹配，匹配失败静默展示未开始，容易造成学生困惑。

| 属性 | 内容 |
|---|---|
| 业务场景 | alias miss（题型名不匹配） |
| 触发条件 | analyze 返回原始名 vs 掌握表 canonical 名不同 |
| 当前处理 | 未处理（前端联调契约：analyze.topicLabel 需过聚集 post-process 出 canonical） |
| 兜底降级策略 | 后端保证返回 canonical；等号匹配查掌握度 |
| 残余风险 | 匹配不上静默降级显示"未开始"，学生困惑 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景7）｜ 完善文档 02-题型分析主流程怎么走.md ｜ 坑档案.md J-QT5
