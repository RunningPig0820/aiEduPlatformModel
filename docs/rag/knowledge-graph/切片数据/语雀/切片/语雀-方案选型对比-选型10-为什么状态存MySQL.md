# 选型10 状态存储：MySQL vs SQLite
> summary: LLM 任务状态存哪？MySQL（ai_edu_kg）替代早期 SQLite，并发/运维/备份更成熟。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型10-为什么状态存MySQL.md
> 类别：架构设计
> WARNING: 与方案-代码对账 #3 矛盾——TaskState 实际用 JSON 文件落 output/progress/（llmTaskLock），未见 MySQL 状态表实现（翻转）。

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| MySQL | 已有环境/并发/运维/备份 | 需配置 | ✅ 采用 |
| SQLite | 轻量 | 并发弱/备份差 | ❌ 早期方案，演进放弃 |
| 证据 | 证据：语雀-设计方案拆分-4.md / design-data-research 13.2 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型10）
