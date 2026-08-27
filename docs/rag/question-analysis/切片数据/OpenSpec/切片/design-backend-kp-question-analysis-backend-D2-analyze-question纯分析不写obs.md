# analyze-question纯分析不写obs

> summary: analyze-question 走只读解析不写 obs，浏览不产生学习信号防污染聚合；池约束 top-1 例外直接落 obs 喂数据。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D2-analyze-question纯分析不写obs.md
> 类别：架构设计

---

### D2：analyze-question 纯分析，不写 obs（浏览不产生学习信号）

> 检索摘要：analyze-question 走只读解析不写 obs，浏览不产生学习信号防污染聚合；池约束 top-1 例外直接落 obs 喂数据。

`TutoringKpResolverImpl.doResolve` 抽出 `persistObs` 开关：`resolve(label, studentId)` 保持写 obs（答疑语义），analyze-question 走 `persistObs=false` 的只读解析（镜像/题型库权威命中不落 obs，浏览噪声不污染聚合）。

**唯一例外（信任简化，见 D8）**：analyze 池约束选择的 **top-1 直接落 RESOLVED obs**（「最可能」信号进数据喂聚合，题型库冷启动也能沉淀）；学生确认 = 正确（vote 覆盖 top-1 纠正）。仅极端兜底（池空）才落 PENDING obs（`upsertPendingIfAbsent` 去重）挂起待补充。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D2）｜ 语雀-决策记录.md D21 ｜ 完善文档 05-数据落库与掌握度.md
