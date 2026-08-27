# 10.2 脚本目录结构
> summary: 脚本目录 edukg/scripts/kg_construction 按流程拆：清洗/教材提取/合并/LLM推理/合并前置/导入/验证，含日志目录。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-脚本目录结构.md
> 类别：操作流程

> 检索摘要：脚本目录 edukg/scripts/kg_construction 按流程拆：清洗/教材提取/合并/LLM推理/合并前置/导入/验证，含日志目录。

edukg/scripts/kg_construction/
├── requirements-scripts.txt   # 脚本独立依赖，不污染主服务
├── clean_math_data.py         # 数学数据清洗
├── extract_textbook_info.py   # 教材信息提取
├── merge_math_data.py         # 数据合并
├── infer_prerequisites_llm.py # LLM 前置关系推理
├── merge_prerequisites.py     # 前置关系合并
├── import_math_to_neo4j.py    # Neo4j 导入
├── validate_prerequisites.py  # 自动验证脚本
└── logs/                      # 错误日志目录

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§10.2 脚本目录结构）
