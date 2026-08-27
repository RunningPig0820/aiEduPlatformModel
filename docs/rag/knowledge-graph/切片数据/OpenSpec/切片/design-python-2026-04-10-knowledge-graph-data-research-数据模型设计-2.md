# 数据模型设计（续）
> summary: 图谱数据模型按 学科→学段→年级→教材→章节→知识点 六级层级组织知识点，是 Neo4j 建模基础。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-数据模型设计-2.md
> 类别：数据关联

---

### 二、数据模型设计（知识点层级结构）（续）

> 检索摘要：图谱数据模型按 学科→学段→年级→教材→章节→知识点 六级层级组织知识点，是 Neo4j 建模基础。

### 2.2.1 跨源映射表（新增）
> 检索摘要：跨源映射表解决未来引入好未来等外部数据时 URI 变化导致关系失效问题，以 SQLite 表保存标准URI与外部ID映射。

建议来源：后续可能引入外部数据（如好未来数据），需建立跨源映射避免 URI 变化导致关系失效。
-- 跨源映射表（SQLite）
CREATE TABLE kp_source_mapping (
id INTEGER PRIMARY KEY,
canonical_uri TEXT NOT NULL,      -- 标准 URI（内部唯一标识）
external_id TEXT NOT NULL,        -- 外部数据源 ID
source_name TEXT NOT NULL,        -- 数据源名称（edukg/haoweilai/etc）
confidence REAL DEFAULT 1.0,      -- 匹配置信度
UNIQUE(canonical_uri, external_id, source_name)
);

### 2.3 关系模型（区分教学顺序与学习依赖）
> 检索摘要：关系模型区分教学顺序与学习依赖：TEACHES_BEFORE 教学顺序、PREREQUISITE 核心前置、PREREQUISITE_CANDIDATE 低置信候选，RELATED_TO/GRADED/THEME 关联。

// ========== 层级关系 ==========
(:Subject)-[:HAS_STAGE]->(:Stage)
(:Stage)-[:HAS_GRADE]->(:Grade)
(:Grade)-[:USE_TEXTBOOK]->(:Textbook)
(:Textbook)-[:HAS_CHAPTER]->(:Chapter)
(:Chapter)-[:CONTAINS]->(:KnowledgePoint)

// ========== 分类关系 ==========
(:KnowledgePoint)-[:BELONGS_TO]->(:Category)
(:KnowledgePoint)-[:SUB_CATEGORY]->(:KnowledgePoint)

// ========== 教学顺序（教材安排顺序，不是学习依赖）==========
(:KnowledgePoint)-[:TEACHES_BEFORE {
confidence: 0.85,
source: "textbook_chapter",
creator: "system",         // 新增：创建者（system/llm/teacher）
evidence: ["chapter_order"]
}]->(:KnowledgePoint)

// ========== 核心前置关系（真正的学习依赖）==========
// 业务查询用 PREREQUISITE，EduKG 标准用 PREREQUISITE_ON
(:KnowledgePoint)-[:PREREQUISITE {
confidence: 0.85,
source: "llm",           // llm/definition_extraction/teacher
creator: "llm_glm",      // 新增：具体创建者（便于审计）
evidence_types: ["definition_dependency", "llm_inference"],
verified: false,
standard_relation: "PREREQUISITE_ON"
}]->(:KnowledgePoint)

// EduKG 标准关系（便于互操作）
(:KnowledgePoint)-[:PREREQUISITE_ON {
confidence: 0.85,
source: "llm"
}]->(:KnowledgePoint)

// ========== 候选前置关系（待验证，低置信度）==========
(:KnowledgePoint)-[:PREREQUISITE_CANDIDATE {
confidence: 0.65,
source: "llm_zero_shot",
evidence_types: ["llm_inference"],
status: "candidate"
}]->(:KnowledgePoint)

// ========== 知识点关联（TTL 原生 relateTo 数据）==========
(:KnowledgePoint)-[:RELATED_TO {
source: "edukg_relateTo"
}]->(:KnowledgePoint)

// ========== 难度递进关系（英语学科专用）==========
(:KnowledgePoint)-[:GRADED {
level: 1,                 // 难度等级
source: "textbook"
}]->(:KnowledgePoint)

// ========== 主题关联关系（历史/语文/地理/政治专用）==========
(:KnowledgePoint)-[:THEME {
theme_name: "中国近代史",
source: "llm"
}]->(:KnowledgePoint)

设计说明：
● TEACHES_BEFORE：教材教学顺序，不等于学习依赖。如"勾股定理"在教材中先于"圆"，但学圆不需要先学勾股定理。
● PREREQUISITE：真正的学习依赖（不学A就学不懂B），由定义依赖抽取 + LLM 多模型投票生成。
● PREREQUISITE_CANDIDATE：低置信度候选关系，待后续验证。
● PREREQUISITE_ON：EduKG 标准关系，方便未来互操作。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§二、数据模型设计（知识点层级结构）（续））
