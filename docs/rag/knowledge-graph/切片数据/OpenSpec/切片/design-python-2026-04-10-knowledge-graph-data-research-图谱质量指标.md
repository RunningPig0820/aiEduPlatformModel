# 9.6 图谱质量指标
> summary: 图谱质量指标含前置关系覆盖率≥30%、DAG合规率100%、平均前置链长度2-4跳、年级倒置率≤5%、高置信度占比≥60%。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-图谱质量指标.md
> 类别：数据关联

> 检索摘要：图谱质量指标含前置关系覆盖率≥30%、DAG合规率100%、平均前置链长度2-4跳、年级倒置率≤5%、高置信度占比≥60%。

指标	计算方法	目标值（demo）
前置关系覆盖率	有 PREREQUISITE 关系的知识点数 / 总知识点数	≥ 30%
DAG 合规率	无环的知识点比例（检测环的数量）	100%
平均前置链长度	所有知识点的最长前置路径长度的平均值	2~4 跳
年级倒置率	PREREQUISITE 关系出现高年级指向低年级的比例	≤ 5%（惩罚处理后）
置信度分布	高置信度（≥0.8）关系的占比	≥ 60%

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§9.6 图谱质量指标）
