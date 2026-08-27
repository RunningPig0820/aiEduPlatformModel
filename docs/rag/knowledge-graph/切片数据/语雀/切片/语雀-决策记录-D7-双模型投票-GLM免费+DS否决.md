# 双模型投票机制（GLM 免费主力 + DeepSeek，DS 否决权）

> summary: LLM 判断为什么双模型投票？GLM-4-flash 免费主力 + DeepSeek 投票，两模型一致采纳，不一致加权 DS=0.6/GLM=0.4、threshold 0.5，DeepSeek 有一票否决权。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-决策记录-D7-双模型投票-GLM免费+DS否决.md
> 类别：数据关联

---

### D7 双模型投票机制（GLM 免费主力 + DeepSeek，DS 否决权）
> 检索摘要：LLM 判断为什么双模型投票？GLM-4-flash 免费主力 + DeepSeek 投票，两模型一致采纳，不一致加权 DS=0.6/GLM=0.4、threshold 0.5，DeepSeek 有一票否决权。

| 属性 | 内容 |
|---|---|
| 背景 | 单模型误判风险；GLM 免费控成本 |
| 演进 | 单模型 → 双模型投票 |
| 拍板理由 | 两模型一致 → 平均置信度采纳；不一致 → 加权投票（仅 DeepSeek=True 才可能过阈值，DS 否决），不一致时置信 ×0.7 |
| 系统影响 | 匹配投票 WEIGHT_DS=0.6/WEIGHT_GLM=0.4/THRESHOLD=0.5；前置投票两模型一致 ≥0.8 → PREREQUISITE |
| 证据 | 证据：edukg/core/llm_inference/dual_model_voter.py:354-396 / design-python-kg-math-prerequisite-inference.md D2 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D7）
