# 一道题没被识别出题型（PENDING）时会怎么处理？会不会丢数据？

> summary: 一道题没被识别出题型（PENDING）时会怎么处理？会不会丢数据？
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: 一道题没被识别出题型（PENDING）时会怎么处理？会不会丢数据？
> 模块: ai-tutoring ｜ 节: 操作流程
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-29-操作流程-一道题没被识别出题型PENDING时.md
> 类别：操作流程

## 回答

**核心结论**：识别失败降级 PENDING，但数据不丢、作答信号保留、后续可批量补齐。

**分层展开**：
- **触发**：question_understand 看图识别失败 → 返回空 topic_labels → Java 降级 PENDING（不是错误，是"待归属"状态）。
- **落库不丢**：topic_label 已改为可空（V20 变更，之前 NOT NULL 会导致 PENDING 落库报错），PENDING 题目照常落库，掌握度/作答信号不丢。
- **后续补齐**：题型归属后由后端批量聚集补 canonical（向量最近邻聚集），把历史 PENDING 归一到标准题型。
- **为什么重要**：答疑是高频交互，识别失败率不可能为 0；如果 PENDING 就丢数据，掌握度和学情分析都会缺环。
- **追问点**："PENDING 会影响学生体验吗？" → 不影响答疑主线，题型识别只是落库/掌握度的前置，引导照常走 decide/generate。
