# 开放问题

> summary: 开放项：canonical 命名策略可调、原题链接用 session_id、掌握表改造 vs 新表；spike 已收口（embedding/阈值/聚集粒度）。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-开放问题.md
> 类别：未来演进

---

### 开放问题

> 检索摘要：开放项：canonical 命名策略可调、原题链接用 session_id、掌握表改造 vs 新表；spike 已收口（embedding/阈值/聚集粒度）。

- ✅ **Python 向量链路（spike）**：已交付——CosVectorsClient 建索引（768 维 cosine）/ put/query 跑通、权限已授权、近邻实测数据见 python-integration 第六节。
- ✅ **embedding 模型 + 阈值**：已定——text-embedding-v3（768），distance 归并阈值默认 **0.2（保守）**。
- ✅ **聚集粒度**：已定——「相遇(0.332)/行程」默认拆分（0.2 阈值不归并），宁可拆不误并。
- **canonical 命名**：本期采用「首见名/最高频名兜底 + 定时 LLM 归纳规范名」；命名策略可调。
- **原题链接**：题目表 `session_id` 跳回答疑会话（已有字段），掌握度页「查看题目」展示会话链接；无会话链接显示题目原文。
- **掌握表改造 vs 新表**：本期倾向改造现有表 + 平滑迁移；若历史数据迁移有风险可退化为新表并行。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§开放问题）｜ 语雀-决策记录.md D18/D26
