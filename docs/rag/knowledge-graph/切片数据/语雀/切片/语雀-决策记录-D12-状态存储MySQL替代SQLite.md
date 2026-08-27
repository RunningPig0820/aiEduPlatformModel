# 状态存储 MySQL 替代早期 SQLite

> summary: LLM 任务状态存哪？MySQL（ai_edu_kg）替代早期 SQLite，原因：已有环境/并发/运维/备份。
> WARNING: 与 `方案-代码对账.md` 冲突——TaskState 实际用 JSON 文件落 `output/progress/`（llmTaskLock），未见 MySQL 状态表实现（design 构想未落地）；以代码分析文档(0.8)为准
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D12-状态存储MySQL替代SQLite.md
> 类别：架构设计

---

### D12 状态存储 MySQL 替代早期 SQLite
> 检索摘要：LLM 任务状态存哪？MySQL（ai_edu_kg）替代早期 SQLite，原因：已有环境/并发/运维/备份。

| 属性 | 内容 |
|---|---|
| 背景 | 早期用 SQLite/JSON 文件存状态，多进程并发/运维/备份受限 |
| 演进 | SQLite → MySQL |
| 拍板理由 | 已有 MySQL 环境；并发安全；运维/备份成熟；表结构（processing_state/llm_cache/cost_tracking/chapter_state+subbatch_state/failed_batches/progress_view） |
| 系统影响 | 原子性 MySQL 事务两阶段；进程锁 portalocker 文件锁 / MySQL 表锁；成本预算日 5000 分/总 20000 分/70% 告警 |
| 证据 | 证据：语雀-设计方案拆分-4.md / design-python-2026-04-10-knowledge-graph-data-research.md 13.2 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D12）
