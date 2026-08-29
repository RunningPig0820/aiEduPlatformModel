# 技术栈与脚本目录

> summary: 技术栈与脚本目录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-18-技术栈与脚本目录.md
> 类别：架构设计

---

> 检索摘要：用什么技术栈、脚本目录怎么组织？Python 3.10+ / rdflib 解析 TTL / neo4j-driver 4.4.x 与 Neo4j 版本严格匹配 / 复用 LLM Gateway（新增 prerequisite_inference scene）；脚本独立依赖 requirements-scripts.txt 不污染主服务；更新后状态存储 MySQL、缓存 SHA256、进程锁 portalocker/MySQL 表锁、配置 YAML、错误日志 MySQL 表。

**技术栈（状态：）**

| 技术项 | 选择 | 说明 |
|---|---|---|
| Python 版本 | 3.10+ | 与主服务一致，避免环境冲突 |
| TTL 解析库 | rdflib | Python 生态最成熟的 RDF 解析库 |
| Neo4j 驱动 | neo4j-driver 4.4.x | 与 Neo4j 版本严格匹配 |
| LLM 调用 | 复用 Gateway | 使用现有 core/gateway/factory.py |

**LLM Gateway 配置（状态：）**：config/model_config.py 新增 scene 映射 `prerequisite_inference` → provider zhipu、model glm-4-flash、temperature 0.3。

**脚本目录结构 edukg/scripts/kg_construction/（状态：）**：requirements-scripts.txt（脚本独立依赖，不污染主服务）、clean_math_data.py（数学数据清洗）、extract_textbook_info.py（教材信息提取）、merge_math_data.py（数据合并）、infer_prerequisites_llm.py（LLM 前置关系推理）、merge_prerequisites.py（前置关系合并）、import_math_to_neo4j.py（Neo4j 导入）、validate_prerequisites.py（自动验证脚本）、logs/（错误日志目录）。

**技术栈更新（状态：）**
- 状态存储：MySQL（已有环境、事务支持、并发性能好）；缓存键算法：SHA256（替代 MD5 避免碰撞）；进程锁：portalocker / MySQL 表锁（跨平台文件锁或分布式锁）；配置格式：YAML（外置配置灵活调整）；错误日志：MySQL 表（结构化存储便于重试脚本）；告警方式：控制台日志（个人项目首选，可扩展邮件）。
- 数据库依赖：requirements-scripts.txt 新增 pymysql>=1.0.2、pyyaml>=6.0、portalocker>=2.7.0。

**脚本目录更新（状态：）**：kg_construction/ 补齐——config/(pipeline.yaml 流程配置, database.yaml MySQL 配置)、db_connection.py（MySQL 连接管理）、state_db.py（状态管理类）、extract_relations.py（提取 relateTo/subCategory）、infer_teaches_before.py、extract_definition_dependencies.py、fuse_prerequisites.py、state_manager.py（SQLite 状态管理）、cache_manager.py（LLM 缓存管理）、cost_tracker.py（成本监控）、process_lock.py（进程锁）、graceful_shutdown.py（优雅退出）、run_math_pipeline.py（主流程脚本）、logs/failed_batches/（失败批次日志）。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十 技术栈与开发规范、§十六 技术栈更新、§十七 脚本目录结构更新）
