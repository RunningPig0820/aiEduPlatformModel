# 断点续传与工程化：状态管理与断点续传

> summary: 断点续传与工程化（状态管理与断点续传）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-12-断点续传与工程化.md
> 类别：开发难点

---

> 检索摘要：长任务怎么断点续传、状态存哪？用 MySQL 替代 SQLite 承接处理状态(processing_state/llm_cache/cost_tracking/chapter_state/subbatch_state/progress_view/failed_batches)；重跑最小单位=章节(业务层)、内部按 token 拆子批次(技术层)；StateDB 封装状态读写；MySQL 事务保证原子性，更安全做法先写缓存再更新业务状态。

**工程化核心原则（状态：）**：幂等性（脚本可重复执行，不产生重复数据或重复调用 LLM）；断点续传（任务中断后从上次进度继续，避免从头开始）；成本控制（对付费模型 DeepSeek-V3 的调用结果必须持久化，防止重复计费）；版本管理（每次构建生成带版本号的数据快照，支持回滚）；并发安全（防止误启动多进程，造成重复调用和数据冲突）。

**状态管理（MySQL，状态：）**：使用 MySQL 替代 SQLite，原因：已有 MySQL 环境无需额外安装、支持更好并发性能、支持更丰富运维工具、数据更安全（有备份机制）。
- 连接配置：config/database.yaml（host/port/database ai_edu_kg/charset utf8mb4/pool_size 5）+ pymysql 连接池 MySQLManager（get_connection / transaction 事务上下文管理器，commit/rollback）。
- 状态表：processing_state（subject/version/step/batch_id/status pending|processing|completed|failed/result_file/retry_count/error_message，UNIQUE(subject,version,step,batch_id)）、llm_cache（cache_key SHA256 唯一/provider/model/batch_uris JSON/response JSON/tokens_used/cost_cents）、cost_tracking（subject/version/provider/model/total_tokens/total_cost_cents/call_count，UNIQUE(subject,version,provider,model)）。
- 两层状态表：chapter_state（业务层，按章节：total_kps/processed_kps/status pending|processing|completed|skipped|failed/priority，UNIQUE(subject,version,chapter_id)）+ subbatch_state（技术层，按子批次：kp_uris JSON/cache_key/result_file/retry_count，UNIQUE(subject,version,batch_id)，外键引用 chapter_state ON DELETE CASCADE）。
- 辅助：progress_view 进度视图（completed/processing/failed 章节数 + progress_percent）、failed_batches 失败批次表。

**StateDB 类（状态：）**：封装 MySQL 操作——章节状态（get_chapter_status / mark_chapter_processing / mark_chapter_completed / mark_chapter_failed / skip_chapter）、子批次状态（is_subbatch_completed / mark_subbatch_completed / mark_subbatch_failed）、LLM 缓存（get_cached_response / save_cache 含 ON DUPLICATE KEY UPDATE）、进度查询（get_progress / get_failed_chapters）、成本追踪（track_cost 按 provider/model 累积）。

**按课程单元划分（状态：）**：重跑最小单位 = 章节（业务认知），内部按 token 限制拆子批次（技术限制，max_tokens 4000）。process_by_chapter：查章节状态（completed/skipped 跳过）→ mark_chapter_processing → 取章节知识点 → 按 token 拆子批次 → 逐子批次查 subbatch 状态（completed 跳过）、处理、标记；子批次异常则标记 failed 并中断该章节。

**进度可视化（状态：）**：show_progress 按学科/版本展示 progress_percent、completed/processing/failed 章节数及失败原因；命令行入口 --show-progress / --retry-failed / --skip-chapter；手动跳过章节标记 skipped 状态，后续重跑自动跳过。

**原子性操作保证（状态：）**：结果文件写入 + 状态更新用 MySQL 事务两阶段提交。关键保证：事务失败 → 缓存未记录 → 下次重跑会重新调用（可能重复付费）；事务成功 → 缓存已记录 → 下次重跑直接使用缓存。**更安全做法：先保存缓存（独立事务优先保证），再更新业务状态**（safer_process_subbatch），即使业务状态失败缓存已保存。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十三 任务执行与容错设计 13.1~13.2）
