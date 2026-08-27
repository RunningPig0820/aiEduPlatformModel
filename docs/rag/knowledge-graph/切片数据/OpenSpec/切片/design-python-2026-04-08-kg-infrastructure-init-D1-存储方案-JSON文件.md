# D1: 存储方案 - JSON 文件
> summary: 任务状态存储选型定为 JSON 文件而非 MySQL，理由为简单易用、无需额外服务、适合单机且便于调试。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-D1-存储方案-JSON文件.md
> 类别：数据存储

> 检索摘要：任务状态存储选型定为 JSON 文件而非 MySQL，理由为简单易用、无需额外服务、适合单机且便于调试。

**决策**: 使用 JSON 文件存储状态（不依赖 MySQL）

**理由**:
- 简单易用，无需额外服务
- 适合单机场景
- 便于调试和查看
- 课标处理任务规模不大

```python
# 状态文件结构
task_state.json = {
    "task_id": "curriculum_extraction",
    "created_at": "2026-04-07T10:00:00Z",
    "updated_at": "2026-04-07T10:30:00Z",
    "status": "in_progress",  # pending, in_progress, completed, failed
    "progress": {
        "total": 15,
        "completed": 5,
        "failed": 0
    },
    "checkpoints": [
        {
            "id": "chunk_1",
            "status": "completed",
            "result_file": "cache/chunk_1.json",
            "completed_at": "..."
        },
        {
            "id": "chunk_2",
            "status": "in_progress",
            "started_at": "..."
        }
    ]
}
```

**替代方案**: MySQL
- **优点**: 更可靠，支持并发
- **缺点**: 需要额外配置，增加复杂度

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§D1: 存储方案 - JSON 文件）
