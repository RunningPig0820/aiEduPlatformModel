# 数据来源与数据治理

> summary: 三类数据源与人工确认的数据治理
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-concept-linking-02-数据来源与数据治理.md
> 类别：数据关联

本阶段数据源分为三类：

1. EduKG 已有数据（初中、高中为主）：作为知识与关系基准。参考格式文件：Class 定义 `edukg/data/edukg/math/1_概念类(Class)/math_classes.json`；Entity 实体 `edukg/data/edukg/math/8_全部关联关系(Complete)/math_entities_complete.json`；Relation 关系 `edukg/data/edukg/math/8_全部关联关系(Complete)/math_knowledge_relations.json`。
2. 教材数据：教材 JSON 解析出的章节结构，小学 12 册 / 初中 6 册 / 高中 6 册，是本次要补全并匹配的对象。
3. 课标文件：义务教育数学课程标准（2022 年版）PDF，扫描版 189 页，需 OCR 后提取知识点作为小学基准。

数据可信度与治理：
- EduKG 主要覆盖初中和高中，缺少小学知识点，因此小学部分需要从课标提取，经人工确认后再补充。
- 教材知识点命名与 Concept 命名不完全一致，需要匹配报告追踪匹配结果与置信度，低置信度标记待确认。
- 输出 JSON 格式符合 Neo4j 导入格式，参考 EduKG 现有数据格式，保证后续导入脚本可直接复用。
- 人工确认是数据治理的关键环节：匹配报告、对比报告输出后由人工确认，再手动导入，保证数据准确、可回滚、可调整。
- 处理链路保持只读基准：查询 Neo4j Concept 为只读操作，不污染既有图谱数据。
