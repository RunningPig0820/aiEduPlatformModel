# 边界场景与兜底

> summary: 边界场景与兜底
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-13-边界场景与兜底.md
> 类别：开发难点

---

> 检索摘要：构建流程有哪些风险与兜底？数据源不匹配→标签匹配容忍缺失、LLM 推理不准→置信度阈值过滤(<0.7 丢弃)、年级推断不准→人工修正接口、数据量大→按学科逐个处理、relateTo 语义混淆→严格区分 RELATED_TO；重试按错误类型区分(超时2次指数退避/格式错误1次/网络3次/成本超限与解析0次)，失败批次结构化存储一键重试。

**风险与缓解（状态：）**

| 风险 | 缓解措施 |
|---|---|
| v0.1 与 v3.0 数据不匹配 | 通过标签匹配，容忍部分缺失 |
| LLM 推理不准确 | 置信度阈值过滤（<0.7 丢弃），≥70% 准确率满足 demo |
| 年级推断不准确 | 提供人工修正接口（正式阶段） |
| 数据量太大 | 按学科逐个处理，数学先行验证 |
| relateTo 与 PREREQUISITE 语义混淆 | 严格区分，relateTo → RELATED_TO，LLM → PREREQUISITE |

**风险与缓解（更新，状态：）**

| 风险 | 缓解措施 |
|---|---|
| 任务中断导致重复工作 | 断点续传 + 状态记录 |
| 付费模型重复调用 | SHA256 缓存 + 状态表 |
| 脚本误删已有数据 | 版本目录隔离 + Neo4j MERGE |
| 版本混乱 | 独立目录 + manifest 元数据 |
| 处理状态丢失 | 数据库事务保护 |
| 成本超预算 | 实时监控 + 告警 + 限制 |
| 误启动多进程 | 进程锁机制 |
| 用户手动中断无保存 | Graceful Shutdown |
| 知识点类型缺失 | CSV 必须导出 type 列 |
| relateTo 语义混淆 | 严格区分 RELATED_TO vs PREREQUISITE |

**重试与错误恢复（状态：）**

| 错误类型 | 重试次数 | 退避策略 | 处理方式 |
|---|---|---|---|
| LLM 调用超时 | 2 | 指数退避（1s, 2s） | 状态标记 pending，下次继续 |
| LLM 返回格式错误 | 1 | 立即重试 | 解析失败记录日志 |
| 网络临时故障 | 3 | 固定间隔 2s | 自动重试 |
| 成本超限 | 0 | 停止调用 | 抛出异常，记录状态 |
| 数据解析错误 | 0 | 记录跳过 | 写入 failed_batches |

错误日志结构化：失败批次写入 failed_batches 表（subject/version/batch_id/batch_uris JSON/error_type/error_message/retry_count/status pending|retrying|resolved|abandoned），便于一键重试脚本 retry_failed_batches（status IN pending/retrying 且 retry_count < max，成功后标记 resolved）。

错误类型分类与处理建议：json_parse_error（LLM 格式损坏→检查 Prompt，增加格式修复）、token_limit_exceeded（输入超 Token→减小批次大小）、timeout（网络或 LLM 超时→增加超时时间，重试）、rate_limit（API 频率限制→增加等待时间）、network_error（网络临时故障→重试）、unknown（其他→检查日志，人工介入）。

原子性兜底：事务失败 → 缓存未记录 → 下次重跑会重新调用（可能重复付费）；事务成功 → 缓存已记录 → 下次重跑直接使用缓存。更安全做法：先保存缓存，再处理业务状态（即使业务状态失败，缓存已保存）。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十一、§十五 风险与缓解、§13.10 重试与错误恢复）
