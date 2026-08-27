# 数据模型设计
> summary: 图谱数据模型按 学科→学段→年级→教材→章节→知识点 六级层级组织知识点，是 Neo4j 建模基础。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-数据模型设计.md
> 类别：数据关联

---

### 二、数据模型设计（知识点层级结构）
> 检索摘要：图谱数据模型按 学科→学段→年级→教材→章节→知识点 六级层级组织知识点，是 Neo4j 建模基础。

#### 2.1 知识点层级结构
> 检索摘要：知识点按 学科→学段→年级→教材→章节→知识点 六级层级组织，是图谱建模骨架。

学科 (Subject)
└── 学段 (Stage: 小学/初中/高中)
└── 年级 (Grade)
└── 教材 (Textbook)
└── 章节 (Chapter)
└── 知识点 (KnowledgePoint)

### 2.2 Neo4j 节点模型
> 检索摘要：Neo4j 节点模型定义 Subject/Stage/Grade/Textbook/Chapter/KnowledgePoint 六类节点及属性，含教材版本、知识点难度与跨源映射ID。

// 学科节点
(:Subject {name: "数学", code: "math"})

// 学段节点
(:Stage {name: "高中", code: "high_school"})

// 年级节点
(:Grade {name: "高一", code: "g10", order: 1})

// 教材节点（包含版本信息）
(:Textbook {
name: "高中数学必修第一册A版",
isbn: "9787107335655",
subject: "math",
grade: "g10",
// 版本信息
curriculum_year: "2019",           // 课标年份: 2019 或 2003
curriculum_name: "普通高中课程标准（2017年版2020年修订）",
publisher: "人民教育出版社",        // 出版社
edition: "人教A版"                 // 教材版本
})

// 章节节点
(:Chapter {
name: "集合与函数概念",
order: 1,
textbook_isbn: "9787107336270"
})

// 知识点节点 (核心)
(:KnowledgePoint {
uri: "http://edukg.org/knowledge/0.1/instance/math#516",
external_id: "edukg_516",    // 新增：跨源映射ID
name: "一元二次方程",
subject: "math",
stage: "初中",
grade: "初三",          // 推断或标注
chapter: "一元二次方程",
type: "定义",           // 定义/性质/定理/公式
difficulty: 3,          // 1-5 难度等级
source: "edukg"         // 数据来源
})

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§二、数据模型设计（知识点层级结构））
