# 十七、脚本目录结构更新
> summary: 脚本目录新增 config/db_connection/state_db/缓存/成本/进程锁/优雅退出/主流程，按工程化容错补齐文件。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-脚本目录结构更新.md
> 类别：操作流程

> 检索摘要：脚本目录新增 config/db_connection/state_db/缓存/成本/进程锁/优雅退出/主流程，按工程化容错补齐文件。

edukg/scripts/kg_construction/
├── requirements-scripts.txt
├── config/
│   ├── pipeline.yaml           # 流程配置
│   └── database.yaml           # MySQL 配置
├── db_connection.py            # 新增：MySQL 连接管理
├── state_db.py                 # 新增：状态管理类
├── clean_math_data.py
├── extract_textbook_info.py
├── merge_math_data.py
├── extract_relations.py        # 提取 relateTo/subCategory
├── infer_teaches_before.py
├── extract_definition_dependencies.py
├── infer_prerequisites_llm.py
├── fuse_prerequisites.py
├── import_math_to_neo4j.py
├── validate_prerequisites.py
├── state_manager.py            # 新增：SQLite 状态管理
├── cache_manager.py            # 新增：LLM 缓存管理
├── cost_tracker.py             # 新增：成本监控
├── process_lock.py             # 新增：进程锁
├── graceful_shutdown.py        # 新增：优雅退出
├── run_math_pipeline.py        # 新增：主流程脚本
└── logs/
    └── failed_batches/         # 新增：失败批次日志




> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§十七、脚本目录结构更新）
