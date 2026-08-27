# 断点续传 llmTaskLock（TaskState + CachedLLM + ProcessLock）

> summary: LLM 长任务中断怎么办？llmTaskLock 断点续传——TaskState 检查点 + CachedLLM(SHA256 缓存) + ProcessLock 文件锁，推断 2-3 小时中断可续。
> WARNING: 与 `方案-代码对账.md` 冲突——`--resume` 部分未落地（前置推断 CLI 无 --resume 参数，断点基于缓存文件，部分任务有）；以代码分析文档(0.8)为准
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D11-断点续传llmTaskLock.md
> 类别：开发难点

---

### D11 断点续传 llmTaskLock（TaskState + CachedLLM + ProcessLock）
> 检索摘要：LLM 长任务中断怎么办？llmTaskLock 断点续传——TaskState 检查点 + CachedLLM(SHA256 缓存) + ProcessLock 文件锁，推断 2-3 小时中断可续。

| 属性 | 内容 |
|---|---|
| 背景 | LLM 推断/匹配长任务中途失败需从头再来（推断 2-3 小时、匹配 1-2 小时） |
| 演进 | 无断点 → llmTaskLock（infrastructure-init） |
| 拍板理由 | JSON 文件状态（不依赖 MySQL）+ SHA256 缓存键（同 Prompt 不重复调用）+ portalocker 文件锁；先修关系推断 ~8,980 次调用断点续传价值最高 |
| 系统影响 | `--resume` 支持；进度用实际已完成数显示；MySQL 状态表两层（chapter_state+subbatch_state） |
| 证据 | 证据：edukg/core/llmTaskLock/README.md / design-python-2026-04-08-kg-infrastructure-init.md D1-D5 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D11）
