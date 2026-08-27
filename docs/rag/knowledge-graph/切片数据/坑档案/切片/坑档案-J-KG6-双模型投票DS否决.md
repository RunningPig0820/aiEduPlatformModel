# 坑档案-J-KG6-双模型投票DS否决
> summary: 双模型投票不一致：GLM 与 DeepSeek 判断冲突，加权投票让 DeepSeek 有否决权
> 来源: 坑档案 ｜ 锚点: J-KG6 ｜ 节: 5.难点/坑档案.md
> COS路径: rag-slices/knowledge-graph/坑档案/坑档案-J-KG6-双模型投票DS否决.md
> 类别：开发难点
> target: 开发对账

---

**1. 问题现象**：同一个知识点对，GLM 说"匹配"、DeepSeek 说"不匹配"——两模型不一致时结果被丢弃，部分真匹配被漏掉；一致通过率偏低。

**2. 触发流程**：`vote_with_retry` 对同一 prompt 并行调 GLM-4-flash + deepseek-chat → `_parse_json_response` 解析出各自的 `is_match/decision` + confidence → `_check_consensus` 比较两模型判断。

**3. 根因分析**：两模型对语义边界的判断天然有分歧（GLM 偏宽松、DeepSeek 偏严格）。修前逻辑"两模型一致才采纳"，不一致直接 `consensus=False` 丢弃——把"可以仲裁的冲突"当"不可用结果"丢掉了，牺牲召回。`dual_model_voter.py:353-354` 注释："不一致时：使用加权投票（DeepSeek=0.6, GLM=0.4，阈值=0.5）"。

**4. 排查过程**：统计投票结果里 `consensus=False` 占比过高；抽查不一致样本发现 GLM 大多答 True、DeepSeek 答 False，且 DeepSeek 答 True 时往往确实匹配——**严格模型的正例可信度高**。

**5. 解决方案 & 改动点**：加权投票仲裁（`edukg/core/llm_inference/dual_model_voter.py:356-396`）：`WEIGHT_DS=0.6, WEIGHT_GLM=0.4, THRESHOLD=0.5`——不一致时 GLM=True 得 0.4（<0.5 不过）、DeepSeek=True 得 0.6（≥0.5 过），即**只有 DeepSeek=True 才可能过阈值，DeepSeek 拥有一票否决**；通过时置信度再乘 0.7 打折，标记 `vote_type='weighted'`、`winner`。配套 `vote_prerequisite`（`dual_model_voter.py:398-437`）前置关系规则：两模型一致 + conf≥0.8 → PREREQUISITE、≥0.6 → PREREQUISITE_CANDIDATE、不一致 → 不采纳。提交：`00bfa3f [知识图谱]-[教材关联逻辑]`（dual_model_voter.py 创建）、`9885742`（投票细节调整）。

**6. 面试口述要点**：双模型不是"投票数相等"——**模型质量不对称时要按可信度加权**。本项目 DeepSeek 更严格（几乎不误报），所以给 0.6 权重，GLM 宽松只给 0.4，等价于"DeepSeek 同意才过、DeepSeek 否决就挂"。权重=否决权的本质是**把低误报模型的意见设成硬约束**；不一致时还打折置信度（×0.7），避免"仲裁出来"的结果冒充高置信。面试可展开：为什么不用 majority vote？因为 2 模型没有多数，加权是最小可行的仲裁。
