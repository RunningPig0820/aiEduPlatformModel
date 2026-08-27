# LLM 推断

> summary: LLM 推断(TextbookKPInferer 缺失章节 295→推断 1052 平均置信 0.93; llmTaskLock 断点续传 TaskState+CachedLLM(SHA256)+ProcessLock; 双模型投票 DS=0.6/GLM=0.4/threshold=0.5, GLM-4-flash 免费主力; 数学全流程成本 1-2 元)
> WARNING: 与 `方案-代码对账.md` 冲突——`--resume` 部分未落地（前置推断 CLI 无 --resume 参数，断点基于缓存文件）；以代码分析文档(0.8)为准
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案总揽-6-LLM推断.md
> 类别：数据关联

---

### 6. LLM 推断

- **目标**：小学 1-6 年级、高中必修教材原始 JSON 的 `knowledge_points` 为空，需 LLM 推断；初中 7-9 年级完整（~252）无需推断。
- **TextbookKPInferer**：根据章节信息（学段/年级/章节名/小节名）推断知识点；缺失章节 295 个 → 推断 **1,052 个**知识点，平均置信度 **0.93**；合并后总计 1350 → 最终清洗后 1740。
- **断点续传 llmTaskLock**（`core/llmTaskLock/`）：`TaskState`（检查点/进度）、`CachedLLM`（SHA256 缓存键，同 Prompt 不重复调用）、`ProcessLock`（portalocker 文件锁）；推断 2-3 小时、匹配 1-2 小时，中断可续（`--resume`）；先修关系推断 ~8,980 次调用断点续传价值最高。
- **双模型投票**（`dual_model_voter.py`）：主模型 `glm-4-flash`（免费）、副模型 `deepseek-chat`（DeepSeek-V3）；两模型一致 → 取平均置信度采纳；不一致 → 加权投票 `WEIGHT_DS=0.6 / WEIGHT_GLM=0.4 / THRESHOLD=0.5`，仅 DeepSeek=True 才可能过阈值（DS 否决），不一致时置信度 ×0.7。
- **成本控制**：GLM-4-flash 免费主力；数学 4490 知识点、批大小 50 → 约 90 次调用 ×2 模型 ×1.1 重试 ≈ 200 次，**数学全流程约 1-2 元**；全学科 56,391 知识点 ~1,120 次、DeepSeek 约 10-20 元；日预算 5000 分/总预算 20000 分/70% 告警。
- **工程化状态管理**：MySQL 状态表（processing_state/llm_cache/cost_tracking/chapter_state+subbatch_state 两层/failed_batches/progress_view）、优雅退出（SIGINT/SIGTERM）、重试策略（超时 2 次/格式错误 1 次/网络 3 次）。

> 证据：详见 `1.语雀/语雀-方案总揽.md`（§6）
