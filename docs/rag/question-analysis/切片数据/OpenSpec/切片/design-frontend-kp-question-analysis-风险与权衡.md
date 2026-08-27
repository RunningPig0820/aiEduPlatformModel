# 风险与权衡

> summary: 列举题型分析页运行风险（LLM 依赖/冷启动阈值/候选波动/vote 10003 等）与缓解手段，明细见正文。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-风险与权衡.md
> 类别：开发难点

---

### 风险与权衡

> 检索摘要：列举题型分析页运行风险（LLM 依赖/冷启动阈值/候选波动/vote 10003 等）与缓解手段，明细见正文。

- [analyze-question 依赖 LLM 可用] → 题目理解走 LLM，服务不可用/低置信时返回 PENDING + candidates（同 resolve 契约），前端渲染空态 + 提示，不阻塞。
- [学生确认冷启动阈值] → 单学生确认不立即生效（聚合需 ≥3 学生/≥5 命中）。缓解：前端「确认成功」提示 + 说明「已记录，将参与整理」，避免学生以为立即改全局。
- [candidates 内容冷启动波动] → 后端已确认：status 稳定（无数据锚恒 PENDING），但 candidates 内容可能波动（属预期）。前端容忍空结果 + 渲染动态候选。
- [vote 10003] → 后端已做 candidates 镜像校验，正常不触发；前端仍兜住（toast + 复位可重试）。
- [PENDING 题型无知识点] → analyze-question 低置信时只有 candidates 无 knowledgePoints，前端展示「待确认」候选 + 让学生选（走 vote）。
- [WEAK → PENDING 频率变高] → 冷启动猜测不再冒充 RESOLVED，PENDING 分支是常态路径，需覆盖「有 candidates」与「空」。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§风险与权衡）
