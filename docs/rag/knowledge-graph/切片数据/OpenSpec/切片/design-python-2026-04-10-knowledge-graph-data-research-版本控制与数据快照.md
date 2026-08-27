# 13.7 版本控制与数据快照
> summary: 版本控制按 v1_日期 目录隔离数据快照，manifest.json 记录源数据版本/统计/成本/LLM配置，缓存跨版本复用。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-版本控制与数据快照.md
> 类别：数据存储

> 检索摘要：版本控制按 v1_日期 目录隔离数据快照，manifest.json 记录源数据版本/统计/成本/LLM配置，缓存跨版本复用。

目录结构：
data/
├── versions/
│   ├── v1_20250328/
│   │   ├── math_knowledge_points.csv
│   │   ├── math_prerequisites.csv
│   │   ├── math_prerequisite_candidates.csv
│   │   ├── math_teaches_before.csv
│   │   ├── math_related_to.csv      # relateTo 数据
│   │   ├── math_sub_category.csv    # subCategory 数据
│   │   ├── state.db                 # SQLite 状态文件
│   │   └── manifest.json
│   └── v2_20250329/
│       └── ...
├── cache/
│   └── llm_responses/   # 缓存与版本无关，可跨版本复用
├── state/
│   └── math.lock        # 进程锁文件
│   └── failed_batches/  # 失败批次日志
└── config/
    └── pipeline.yaml    # 配置文件

Manifest 记录：
{
  "version": "v1_20250328",
  "subject": "math",
  "source_data": {
    "ttl_version": "v0.1",
    "main_ttl_version": "v3.0"
  },
  "generated_at": "2025-03-28T10:30:00",
  "stats": {
    "total_kps": 4490,
    "prerequisites": 1234,
    "prerequisite_candidates": 567,
    "teaches_before": 890,
    "related_to": 9870,
    "sub_category": 328
  },
  "cost": {
    "total_tokens": 12345,
    "total_cost_cents": 1234,
    "calls_by_provider": {"zhipu": 100, "deepseek": 50}
  },
  "llm_config": {
    "providers": ["zhipu", "deepseek"],
    "model_versions": {"zhipu": "glm-4-flash", "deepseek": "deepseek-V3"},
    "temperature": 0.3,
    "prompt_version": "v2"
  }
}

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.7 版本控制与数据快照）
