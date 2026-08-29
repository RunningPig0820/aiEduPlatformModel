# 知识点匹配与双模型投票

> summary: 早期匹配策略：精确匹配 + LLM 模糊匹配
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-concept-linking-06-知识点匹配与双模型投票.md
> 类别：架构设计

本文档对应早期匹配设计：精确匹配 + LLM 模糊匹配。双模型投票为后续演进版本，不在本设计范围内。

匹配流程：
1. 精确匹配：label 完全相同 → matched（confidence: 1.0）。
2. 模糊匹配：LLM 语义匹配 → fuzzy_match（confidence: 0.8）。
3. 无匹配：Concept 不存在 → new（confidence: 0.0）。
4. 输出报告：matching_report.json 供人工确认。

设计理由：精确匹配成本低，先尝试；LLM 模糊匹配提高匹配率；输出报告供人工确认，避免低质量自动导入。

当前匹配现状：教材知识点 346 个，仅 24 个匹配成功（6%），失败 322 个（93%）。失败主因是 EduKG 缺少小学知识点，而非匹配算法本身。

风险与兜底：模糊匹配可能关联错误知识点。缓解措施：输出匹配报告人工确认；记录匹配置信度，低置信度标记待确认；不自动导入，需人工确认后方可入库。
