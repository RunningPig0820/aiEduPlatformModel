# analyze纯分析不写obs
> summary: 题型分析端点是只读解析，除封闭域池约束 top-1 直接落 RESOLVED obs 外不写观测，浏览行为不污染聚合统计。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-决策记录-D21-analyze纯分析不写obs.md
> 类别：业务视角

---

### D21 analyze-question 纯分析不写 obs（浏览不产生学习信号）
> 检索摘要：题型分析端点是只读解析，除封闭域池约束 top-1 直接落 RESOLVED obs 外不写观测，浏览行为不污染聚合统计。

| 属性 | 内容 |
|---|---|
| 背景 | resolve 是 label 级且写 obs；题型分析是浏览行为，写 obs 会污染聚合 |
| 演进 | resolve 复用 → 抽 persistObs 开关，analyze 走只读解析 |
| 拍板理由 | 浏览不产生学习信号；唯一例外：封闭域池约束 top-1 直接落 RESOLVED obs（最可能信号进数据喂聚合，题型库冷启动也能沉淀），学生确认 vote 可覆盖纠正 |
| 系统影响 | 题型分析页贴题不产生学习信号，掌握度只被 AI 答疑更新（D12） |
| 证据 | design-backend-kp-question-analysis D2 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D21）｜ 完善文档 02-题型分析主流程怎么走.md
