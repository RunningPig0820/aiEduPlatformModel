# 聚合阈值（配置化）

> summary: 题型库聚合阈值进 application.yml：进 CANDIDATE 需去重学生≥3 且总命中≥5，升 STABLE 需审核通过+去重学生≥10 且近 30 天增长。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D4-聚合阈值-配置化.md
> 类别：数据存储

> 检索摘要：题型库聚合阈值进 application.yml：进 CANDIDATE 需去重学生≥3 且总命中≥5，升 STABLE 需审核通过+去重学生≥10 且近 30 天增长。

| 阶段 | 条件 |
|---|---|
| 进 CANDIDATE | `(topic)` 去重学生数 ≥ 3 且 总命中 ≥ 5 |
| 升 STABLE | 审核通过 + 去重学生数 ≥ 10 且近 30 天仍增长 |

聚合桶按 `topic_label`（分布子表再按 kp 拆）。阈值进 `application.yml`（`ai-edu.kp.aggregation.*`）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D4 聚合阈值（配置化））
