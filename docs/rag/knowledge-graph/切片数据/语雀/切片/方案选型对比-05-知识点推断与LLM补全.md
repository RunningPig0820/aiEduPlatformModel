# 知识点推断与 LLM 补全

> summary: 知识点推断与 LLM 补全
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/方案选型对比-05-知识点推断与LLM补全.md
> 类别：数据关联

---

本块合并《语雀-方案选型对比》中「LLM 主模型选型」相关内容（选型5），解答「LLM 推理/补全用哪个模型、成本多少」类问题。

**选型5｜LLM 主模型：GLM-4-flash vs DeepSeek vs 百炼 qwen**

> 检索摘要：LLM 推理用哪个模型？GLM-4-flash 免费主力 + DeepSeek-V3 双模型投票，数学全流程成本 1-2 元。

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| GLM-4-flash（主） | 免费 | 单模型误判 | 主模型 |
| DeepSeek-V3（副） | 强/约 0.001 元千 token | 付费 | 双模型投票副模型 |
| 百炼 qwen | 生态 | 付费 | 未采用 |
| 证据 | 证据：语雀-LLM推理的成本与效率.md / design-prerequisite-inference D2 |  |  |
