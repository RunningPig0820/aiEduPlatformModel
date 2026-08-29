# 断点续传与工程化：进程锁、缓存、成本、版本、幂等与主流程

> summary: 断点续传与工程化（进程锁/缓存/成本/版本/幂等/主流程）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-12-断点续传与工程化-2.md
> 类别：开发难点

---

> 检索摘要：构建工程化还有哪些保障？进程锁(portalocker 文件锁/MySQL 表锁防多进程)、SHA256 缓存键(替代 MD5)、成本监控(日50元/总200元/70%告警)、版本快照 manifest 支持回滚、Graceful Shutdown 中断保存、Neo4j MERGE 幂等、动态批大小防 Token 超限、关系去重合并、run_math_pipeline 七步主流程。

**进程锁（跨平台，状态：）**：防止误启动多进程或意外中断后重复启动。
- 文件锁（portalocker，推荐）：`LOCK_EX|LOCK_NB` 非阻塞获取，写入 pid，上下文管理器进入失败抛 "Another process is running"。
- MySQL 表锁（替代方案）：process_lock 表（lock_name 主键/pid/hostname/acquired_at），获取时先清理超时锁（默认 3600s），INSERT 主键冲突即被占用，支持 get_lock_info 查询占用 pid/host。

**LLM 推理断点续传（状态：）**：process_llm_batches 每批次：查状态（completed 跳过）→ 查缓存（命中则标记 completed 用缓存结果）→ 标记 processing → 调用 LLM → 保存缓存+记录成本；失败按 retry_count 与 MAX_RETRIES 判断 mark_pending（重试）或 mark_failed（写入失败批次日志）。

**成本控制与监控（状态：）**：config/pipeline.yaml cost_limits——daily_limit_cents 5000（日预算 50 元）/ total_limit_cents 20000（总预算 200 元）/ warning_threshold 0.7（70% 告警）；alert 控制台告警（可扩展邮件）。check_cost_limit：超总预算返回 False 停止调用，超日预算/接近上限告警。

**缓存策略（SHA256，状态：）**：SHA256 替代 MD5 避免碰撞风险；cache_key = sha256(json{uris 排序, prompt_version, model})[:32]。

**版本控制与数据快照（状态：）**：data/versions/v1_日期/ 目录隔离（math_knowledge_points.csv/math_prerequisites.csv/math_prerequisite_candidates.csv/math_teaches_before.csv/math_related_to.csv/math_sub_category.csv/state.db/manifest.json）；cache/llm_responses 缓存与版本无关可跨版本复用；manifest.json 记录源数据版本（ttl v0.1/main v3.0）/统计（total_kps/prerequisites/…）/成本（total_tokens/total_cost_cents/按 provider）/LLM 配置（providers/model_versions/temperature/prompt_version）。

**Graceful Shutdown（状态：）**：监听 SIGINT/SIGTERM，收到中断标记 shutdown_requested；检查点保存 pending 状态后退出，下次可继续处理。

**幂等性设计（状态：）**：Neo4j 导入使用 MERGE——知识点节点按 uri 唯一；前置关系按端点和类型唯一（MERGE (from)-[r:PREREQUISITE]->(to)），重复执行不产生重复数据。

**动态批大小调整（状态：）**：不同章节知识点数量差异大，固定批大小可能导致 Token 超限；用 tiktoken 预估 token（Prompt 基础 token + 知识点 token），超出 max_tokens（默认 4000）则开新批。

**关系去重与合并（状态：）**：多个来源可能生成相同关系，按 (from, to, 类型) 合并——保留更高置信度，合并 evidence_types/source 去重，避免图谱冗余。

**主流程 run_math_pipeline（状态：）**：进程锁包住 → Step 1 数据解析 parse_ttl（幂等）→ Step 2 教材匹配 match_textbook（幂等）→ Step 3 定义依赖抽取（幂等）→ Step 4 关系数据提取 extract_relations（幂等）→ Step 5 LLM 推理（断点续传+成本控制）→ Step 6 证据融合 fuse（幂等）→ Step 7 Neo4j 导入（MERGE 幂等）→ 生成 manifest。每步先查 get_step_status 是否 completed，可重跑不重复计费。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.3~13.11）
