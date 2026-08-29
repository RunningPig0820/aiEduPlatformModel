# 边界场景与兜底

> summary: 边界场景与兜底
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-infrastructure-init-13-边界场景与兜底.md
> 类别：开发难点

断点续传/llmTaskLock 基础设施的边界场景与兜底设计，属 design-python-2026-04-08-kg-infrastructure-init 设计稿（权威 0.7 素材层），业务真实实现请以 canonical 真相源为准。

## Risk 1：文件损坏

**风险**：状态文件损坏导致任务无法恢复。
**缓解**：每次更新前备份，使用原子写入。

## Risk 2：缓存过大

**风险**：大量 LLM 调用产生大量缓存文件。
**缓解**：提供 `--clear-cache` 命令清理。

## Risk 3：锁残留

**风险**：进程异常退出导致锁文件残留。
**缓解**：检查锁文件时间戳，超过超时自动清理。
