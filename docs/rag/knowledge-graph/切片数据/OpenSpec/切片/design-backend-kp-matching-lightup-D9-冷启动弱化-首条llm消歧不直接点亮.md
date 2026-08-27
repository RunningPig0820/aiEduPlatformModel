# 冷启动弱化：首条 LLM 消歧不直接点亮

> summary: 题型库无先验时 LLM 消歧首条标 WEAK 不直接点亮，需第二独立信号（做题结果佐证/他人共现/投票达标）才转 RESOLVED，防高置信幻觉结晶。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D9-冷启动弱化-首条llm消歧不直接点亮.md
> 类别：操作流程

> 检索摘要：题型库无先验时 LLM 消歧首条标 WEAK 不直接点亮，需第二独立信号（做题结果佐证/他人共现/投票达标）才转 RESOLVED，防高置信幻觉结晶。

**决策**：题型库无先验支撑时（冷启动首条），LLM 消歧结果 SHALL 标记 `status=WEAK`（弱确定），**不直接点亮**、不直接进题型库先验；满足任一"第二独立信号"才转 RESOLVED：

1. 同生后续做题结果佐证（用该知识点解对了同类题）；
2. 第二名不同学生对该题型消歧到同一 kp（共现佐证）；
3. 学生澄清投票达到阈值且方向一致。

**理由**：冷启动种子 100% 依赖 LLM，是最不可靠的一环。让"确定性"来自「重复 + 客观结果」而非 LLM 一句话，防止高置信幻觉直接结晶。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D9 冷启动弱化：首条 LLM 消歧不直接点亮）
