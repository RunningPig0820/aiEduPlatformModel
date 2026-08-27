# 选型5 LLM 主模型：GLM-4-flash vs DeepSeek vs 百炼 qwen
> summary: LLM 推理用哪个模型？GLM-4-flash 免费主力 + DeepSeek-V3 双模型投票，数学全流程成本 1-2 元。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型5-为什么用GLM4flash加DeepSeek.md
> 类别：架构设计

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| GLM-4-flash（主） | 免费 | 单模型误判 | ✅ 主模型 |
| DeepSeek-V3（副） | 强/约 0.001 元千 token | 付费 | ✅ 双模型投票副模型 |
| 百炼 qwen | 生态 | 付费 | ❌ 未采用 |
| 证据 | 证据：语雀-LLM推理的成本与效率.md / design-prerequisite-inference D2 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型5）
