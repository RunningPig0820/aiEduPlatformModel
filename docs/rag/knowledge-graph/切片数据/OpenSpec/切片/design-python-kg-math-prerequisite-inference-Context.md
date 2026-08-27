# Context：前置关系推断背景与约束
> summary: 前置关系推断是知识图谱项目核心设计成本：需区分教学顺序TEACHES_BEFORE与学习依赖PREREQUISITE，多证据融合生成高质量前置关系，设计约束含多模型投票与断点续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-Context.md
> 类别：数据关联

> 检索摘要：前置关系推断是知识图谱项目核心设计成本：需区分教学顺序TEACHES_BEFORE与学习依赖PREREQUISITE，多证据融合生成高质量前置关系，设计约束含多模型投票与断点续传。

前置关系推断是知识图谱项目的**核心设计成本**部分。需要区分教学顺序（TEACHES_BEFORE）和学习依赖（PREREQUISITE），通过多证据融合生成高质量的前置关系数据。

当前状态：
- **知识点**: 已导入 EduKG 数据（Class 39, Concept 1,295, Statement 2,932）
- **原生关系**: 已导入 RELATED_TO 10,183, SUB_CLASS_OF 38, PART_OF 298, BELONGS_TO 619
- **LLM Gateway**: 支持 GLM-4-flash（免费）和 DeepSeek-V3（低成本）
- **教材数据**: 已生成 TextbookKP 299 个（小学47 + 初中252）

设计约束：
- 区分教学顺序 vs 学习依赖
- 使用多模型投票提高准确率
- 保留低置信度关系作为候选
- **所有 LLM 任务必须支持断点续传**
- **核心代码放入 `edukg/core/llm_inference/`，scripts 只做命令行入口**

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§Context：前置关系推断背景与约束）
