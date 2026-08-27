# 风险与权衡

> summary: 列举 analyze-question 链路运行风险（LLM 幻觉/阈值误并/冷启动波动/池过大等）与缓解手段，明细见正文。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-风险与权衡.md
> 类别：架构设计

---

### 风险与权衡

> 检索摘要：列举 analyze-question 链路运行风险（LLM 幻觉/阈值误并/冷启动波动/池过大等）与缓解手段，明细见正文。

#### 风险清单（一）：识别与合并风险

- [LLM 题目理解幻觉题型名] → 下一步 resolve 兜底（PENDING 不报错）+ 学生确认；题型库命中才算可靠；prompt 注入词表收敛命名。
- [kp 重叠阈值误并（两个真实不同题型共享大量知识点）] → 阈值 70% 保守 + 可配置；合并只加别名、不动 canonical 名，误并可后续拆。
- [别名表增长（变体无限）] → 别名仅聚合命中时插入，且有 UNIQUE；聚合是离线低频任务；长期同义词收敛仍留大数据。
- [analyze 权威结果不写 obs → 冷启动题型库空] → 预期（浏览噪声不污染聚合）；存疑落 PENDING obs + vote/维护任务补充；题型库随答疑/投票/确认逐步积累，测试环境需真实数据或手动触发聚合。
- [candidates 冷启动波动] → status 稳定（无数据锚恒 PENDING），candidates 内容波动属 LLM 非确定；数据锚积累后收敛，前端容忍动态候选。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§风险与权衡，上半）
