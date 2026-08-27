# Risk 2: 缓存过大
> summary: 大量 LLM 调用会产生过多缓存文件，提供 --clear-cache 命令清理。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-risk2-缓存过大.md
> 类别：开发难点

> 检索摘要：大量 LLM 调用会产生过多缓存文件，提供 --clear-cache 命令清理。

**风险**: 大量 LLM 调用产生大量缓存文件
**缓解**: 提供 `--clear-cache` 命令清理

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§Risk 2: 缓存过大）
