# 知识点推断与 LLM 补全

> summary: glm-4-flash 提取课标知识点并推断关系，补全小学缺失
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-concept-linking-05-知识点推断与LLM补全.md
> 类别：数据关联

目标：通过 LLM 从课标与教材中提取并推断知识点，补全 EduKG 缺失的小学部分。

LLM 选型：使用智谱 glm-4-flash（免费）。理由：免费、成本可控；中文理解能力强；支持 JSON 结构化输出；通过 LangChain 集成。替代方案 DeepSeek、百炼 qwen 均需付费。

LLM 承担三类推断任务：
1. Class 类型推断：根据知识点语义推断 HAS_TYPE 关系。示例：凑十法→数学方法；20 以内加法→数学运算。若现有 Class 不匹配，建议新增 Class（如小学数概念、小学运算方法、小学几何概念）。
2. Statement 定义提取：为每个知识点生成定义。示例：凑十法的定义是"将一个数拆分成 10 和另一部分..."，并建立 Statement→Concept 的 RELATED_TO 关系。
3. 知识点关系提取：分析知识点之间的关系。PART_OF：20 以内加法→加法（部分-整体）；BELONGS_TO：凑十法→进位加法（所属关系）。

补全策略：EduKG 主要覆盖初中和高中，小学知识点大量缺失（教材 346 个知识点仅 24 个匹配成功，失败率 93% 主因缺小学）。从课标提取小学知识点作为基准，对比报告标记缺失知识点，人工确认后手动导入。

中间产物：curriculum_kps.json 存放课标知识点中间结果；kp_comparison_report.json 存放与 Neo4j Concept 的对比结果。
