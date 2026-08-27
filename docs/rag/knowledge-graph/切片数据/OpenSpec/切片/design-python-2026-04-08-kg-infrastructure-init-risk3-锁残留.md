# Risk 3: 锁残留
> summary: 进程异常退出导致锁文件残留，检查时间戳超过超时自动清理。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-risk3-锁残留.md
> 类别：开发难点

> 检索摘要：进程异常退出导致锁文件残留，检查时间戳超过超时自动清理。

**风险**: 进程异常退出导致锁文件残留
**缓解**: 检查锁文件时间戳，超过超时自动清理

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§Risk 3: 锁残留）
