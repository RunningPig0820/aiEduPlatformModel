# 图谱数据模型与两层结构

> summary: 图谱数据模型与两层结构
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-03-图谱数据模型与两层结构.md
> 类别：数据存储

---

> 检索摘要：图谱用什么节点和关系建模？知识点按 学科→学段→年级→教材→章节→知识点 六级层级组织；Neo4j 节点 6 类（Subject/Stage/Grade/Textbook/Chapter/KnowledgePoint），关系区分 教学顺序 TEACHES_BEFORE 与 学习依赖 PREREQUISITE，另有候选/标准/关联/难度/主题关系。

**知识点层级结构（状态：）**
学科(Subject) → 学段(Stage: 小学/初中/高中) → 年级(Grade) → 教材(Textbook) → 章节(Chapter) → 知识点(KnowledgePoint)，六级层级是 Neo4j 建模骨架。

**Neo4j 节点模型（状态：）**
- 学科 `(:Subject {name:"数学", code:"math"})`
- 学段 `(:Stage {name:"高中", code:"high_school"})`
- 年级 `(:Grade {name:"高一", code:"g10", order:1})`
- 教材（含版本信息）`(:Textbook {name, isbn, subject, grade, curriculum_year(2019/2003), curriculum_name, publisher(人民教育出版社), edition(人教A版)})`
- 章节 `(:Chapter {name, order, textbook_isbn})`
- 知识点（核心）`(:KnowledgePoint {uri, external_id(跨源映射ID), name, subject, stage, grade, chapter, type(定义/性质/定理/公式), difficulty(1-5), source("edukg")})`

**关系模型（状态：）**
- 层级关系：`HAS_STAGE` / `HAS_GRADE` / `USE_TEXTBOOK` / `HAS_CHAPTER` / `CONTAINS`
- 分类关系：`BELONGS_TO`（→Category）/ `SUB_CATEGORY`
- 教学顺序 `TEACHES_BEFORE {confidence:0.85, source:"textbook_chapter", creator:"system", evidence:["chapter_order"]}` —— 教材安排顺序，不是学习依赖
- 核心前置 `PREREQUISITE {confidence, source:"llm|definition_extraction|teacher", creator:"llm_glm", evidence_types:["definition_dependency","llm_inference"], verified:false, standard_relation:"PREREQUISITE_ON"}`
- EduKG 标准关系 `PREREQUISITE_ON {confidence:0.85, source:"llm"}`（便于互操作）
- 候选前置 `PREREQUISITE_CANDIDATE {confidence:0.65, source:"llm_zero_shot", evidence_types:["llm_inference"], status:"candidate"}`（待验证低置信）
- 知识点关联 `RELATED_TO {source:"edukg_relateTo"}`（TTL 原生 relateTo 数据）
- 难度递进 `GRADED {level, source:"textbook"}`（英语学科专用）
- 主题关联 `THEME {theme_name, source:"llm"}`（历史/语文/地理/政治专用）

设计说明：
- TEACHES_BEFORE：教材教学顺序，不等于学习依赖。如"勾股定理"在教材中先于"圆"，但学圆不需要先学勾股定理。
- PREREQUISITE：真正的学习依赖（不学 A 就学不懂 B），由定义依赖抽取 + LLM 多模型投票生成。
- PREREQUISITE_CANDIDATE：低置信度候选关系，待后续验证。
- PREREQUISITE_ON：EduKG 标准关系，方便未来互操作。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§二 数据模型设计）
