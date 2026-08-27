# 选型9 断点续传：llmTaskLock vs 无断点重跑
> summary: LLM 长任务中断怎么办？llmTaskLock（JSON 状态 + SHA256 缓存 + portalocker 锁）支持 --resume，推断 2-3 小时可续。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型9-为什么用llmTaskLock断点续传.md
> 类别：架构设计
> WARNING: 与方案-代码对账 #15 矛盾——前置推断 CLI 无 --resume 参数，断点基于缓存文件（部分任务有），部分落地。

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| llmTaskLock（状态+缓存+锁） | 断点续传/缓存省调用/跨平台 | 文件管理成本 | ✅ 采用 |
| 无断点全量重跑 | 简单 | 中断丢进度 | ❌ 否决 |
| 证据 | 证据：design-infrastructure-init D1-D5 / edukg/core/llmTaskLock |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型9）
