# 两层 PENDING 混用
> summary: analyze 识别 PENDING 与 getMastery 掌握度 PENDING 语义分离，禁止前端共用同一个 status 变量，否则全部状态展示错乱（D14）。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-边界场景清单-场景8-两层PENDING混用.md
> 类别：开发难点

---

### 场景8：两层 PENDING 混用
> 检索摘要：analyze 识别 PENDING 与 getMastery 掌握度 PENDING 语义分离，禁止前端共用同一个 status 变量，否则全部状态展示错乱（D14）。

| 属性 | 内容 |
|---|---|
| 业务场景 | 两层 PENDING 混用 |
| 触发条件 | 前端共用一个 status 变量判断 analyze 与 getMastery 的 PENDING |
| 当前处理 | 已定稿：两层分开判（D14）——识别层 PENDING 展示候选，掌握度层 PENDING 才是待确认 |
| 兜底降级策略 | 绝不共用一个判断变量 |
| 残余风险 | 若前端不遵守契约，状态展示全错 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景8）｜ 语雀-决策记录.md D14 ｜ 完善文档 02-题型分析主流程怎么走.md ｜ 坑档案.md J-QT3
