# 知识点推断与 LLM 补全
> summary: 知识点推断与 LLM 补全
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-prerequisite-inference-05-知识点推断与LLM补全.md
> 类别：数据关联

> 检索摘要：教学知识点推断模块如何用双模型投票补全小学3-6年级与高中缺失的knowledge_points，infer_section/infer_batch的输入输出与断点续传，textbook_kg.txt提示词格式。

## 背景

教材数据中小学3-6年级、高中知识点的 knowledge_points 字段为空，需要 LLM 推断补全。

## 教学知识点推断器（TextbookKPInferer）

TextbookKPInferer 使用 DualModelVoter 双模型投票器作为证据来源，核心方法：
- infer_section(stage, grade, semester, chapter_name, section_name, existing_kps)：推断单个小节的教学知识点。入参为学段、年级、册次、章节名称、小节名称、已有知识点（可选）；返回 knowledge_points 列表、confidence（0.0-1.0）、notes（推断依据）
- infer_batch(sections, resume=True)：批量推断，支持断点续传

## 提示词（textbook_kg.txt）

输入：
- 学段、年级、册次
- 章节名称、小节名称
- 已有知识点（如为空则需推断）

输出（JSON）：
- knowledge_points：推断出的知识点数组
- confidence：置信度（如 0.85）
- notes：推断依据（如"依据人教版七年级上册1.1节标准教学内容"）

## 与前置关系推断的关系

教学知识点推断在 kg-math-complete-graph 模块中实现，本前置关系推断模块复用其输出结果；推断结果输出到 textbook_kps_inferred.json，供前置关系推断作为输入数据。

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D4/§D6）
