# 知识点推断与LLM补全

> summary: 知识点推断与LLM补全
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/方案总揽-05-知识点推断与LLM补全.md
> 类别：数据关联

---

本块合并《语雀-方案总揽》中「知识点推断与 LLM 补全」相关内容（原文 §6 LLM 推断），说明 TextbookKPInferer、缺失 295→推断 1052、平均置信 0.93、glm-4-flash 主+deepseek 副、成本 1-2 元。断点续传/状态管理详见「断点续传与工程化」块，双模型投票机制详见「知识点匹配与双模型投票」块。

## LLM 推断目标

小学 1-6 年级、高中必修教材原始 JSON 的 `knowledge_points` 为空，需 LLM 推断；初中 7-9 年级完整（~252）无需推断。

## TextbookKPInferer 推断统计

- **TextbookKPInferer**：根据章节信息（学段/年级/章节名/小节名）推断知识点；缺失章节 295 个 → 推断 **1,052 个**知识点，平均置信度 **0.93**；合并后总计 1350 → 最终清洗后 1740。
- 双模型投票（详见匹配块）：主模型 `glm-4-flash`（免费）、副模型 `deepseek-chat`（DeepSeek-V3）。
- 断点续传 llmTaskLock（详见工程化块）：TaskState + CachedLLM（SHA256 缓存）+ ProcessLock；推断 2-3 小时、匹配 1-2 小时，中断可续（`--resume`）；先修关系推断 ~8,980 次调用断点续传价值最高。

## 成本控制

- GLM-4-flash 免费主力；数学 4490 知识点、批大小 50 → 约 90 次调用 ×2 模型 ×1.1 重试 ≈ 200 次，**数学全流程约 1-2 元**。
- 全学科 56,391 知识点 ~1,120 次、DeepSeek 约 10-20 元；日预算 5000 分/总预算 20000 分/70% 告警。

## 工程化状态管理（§6 节选，详见工程化块）

MySQL 状态表（processing_state/llm_cache/cost_tracking/chapter_state+subbatch_state 两层/failed_batches/progress_view）、优雅退出（SIGINT/SIGTERM）、重试策略（超时 2 次/格式错误 1 次/网络 3 次）。
