# 知识点推断与 LLM 补全

> summary: 知识点推断与LLM补全
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/演进时间线-05-知识点推断与LLM补全.md
> 类别：数据关联

本块合并《语雀-演进时间线》阶段3 中知识点推断与 LLM 补全的内容，说明缺失教学知识点如何用 LLM 推断补全、属性如何扩展。

## 背景：教学知识点大量缺失

教材目录中数学教学知识点初始大量缺失：小学 3-6 年级为 0、高中必修为 0，需要补全后才可支撑匹配与答疑。

## 方案：complete-graph（D1-D13）TextbookKPInferer

- 用 TextbookKPInferer 对缺失教学知识点做 LLM 推断补全，共补 1052 个知识点，平均置信 0.93。
- 属性扩展采用纯规则（非 LLM）：difficulty / importance / cognitive_level / topic。
- 最终输出完整图谱 JSON，不直接导入 Neo4j——防止低质量 Concept 污染权威图谱，且 JSON 可回滚重试。

## 关键决策

- LLM 推断补知识点（平均置信 0.93），补全后形成 1740 个教学知识点。
- 输出 JSON 不直接导入：保留人工/规则质检窗口，低质量 Concept 不进权威库。

## 落地证据

证据：design-python-2026-04-15-kg-math-complete-graph.md / edukg/README.md（最终 1740 知识点）。
