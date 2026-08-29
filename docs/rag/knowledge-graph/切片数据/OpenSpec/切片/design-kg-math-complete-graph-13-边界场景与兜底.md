# 边界场景与兜底

> summary: 边界场景与兜底
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-13-边界场景与兜底.md
> 类别：开发难点

---

> 检索摘要：这个项目有哪些风险？匹配率低/推断不准/人工验证成本/依赖未完成/通用标签误删/属性不一致怎么兜底？

本文档设计阶段列出的风险与兜底措施：

R1 知识点匹配率低：LLM 匹配可能不准确导致匹配率低。缓解：双模型投票 + 置信度阈值 + 候选关系保留（MATCHES_KG_CANDIDATE）。

R2 教学知识点推断质量：LLM 推断的知识点可能不准确。缓解：使用教研员角色提示词 + 保留置信度 + 人工验证。

R3 手动导入验证成本：人工验证 JSON 数据需要时间。缓解：输出详细统计摘要 + 提供 Cypher 模板 + 分批验证导入。

R4 推理依赖：依赖 kg-math-prerequisite-inference 的推理机制。缓解：该模块需要先完成。

R5 "通用"标签处理复杂度：清理"通用"标签可能误删有效数据。缓解：先检测并列出候选重复数据，人工确认后再处理。

R6 知识点属性推断一致性：不同章节推断的 difficulty/importance 可能不一致。缓解：使用统一标准 + 建立属性校验规则。

匹配阶段异常兜底：LLM 调用失败时 continue，不中断整个知识点；输出所有教材知识点（含未匹配）并增加 matched 字段。粗筛规模兜底：图谱 5000+ 知识点不直接全量走 LLM 投票，先粗筛 top-20 候选，避免 LLM 调用量爆炸。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§R1-R6 / §D4.5 / §D4.2）
