# 模块定位与核心价值

> summary: 模块定位与核心价值
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-backend-01-模块定位与核心价值.md
> 类别：项目介绍

---

> 检索摘要：kp-matching-lightup 解决 AI 答疑 decide 输出的自由文本题型标签落不到教材知识点 URI 的问题（掌握度链路断裂）；目标让题型可靠解析到教材知识点、沉淀题型库、掌握度主体翻转并派生层全自动维护，权威图谱 Neo4j 零写入。

**文档性质**：本文件为设计阶段素材，同时包含已落地、构想未实现、待决策内容；业务真实实现以权威度 0.8 的 canonical 真相源文档为准。本文件独立完整，内容不拆分到外部 canonical 文档。

**现状（Context）**：
- AI 答疑的 decide 已能输出自由文本知识点标签（question_kps / mastery_signals），但 TutoringKpResolverImpl 只做「精确 → LIKE → 未命中丢弃」，真实题型（鸡兔同笼）大量落不到图谱，掌握度链路断裂。
- 权威图谱：教育局下载，Neo4j 为主 + kg-sync 镜像 t_kg_knowledge_point（uri/label）。图谱节点带 URI，前端图谱页（KnowledgeGraph.jsx）能按 node.id 匹配。
- 掌握度：t_student_kp_mastery 按 kp_key(URI) UPSERT，GET /api/students/{id}/mastery 已存在，但前端 getStudentMastery 定义了没人调用，且学生端没有图谱页（只有 admin 图谱页）。
- 关键约束：权威图谱（Neo4j + kg-sync 镜像）零写入。题型空间无限、图谱节点有限，无限业务数据必须与有限权威结构分存。

**Goals**：
- 让 AI 题型可靠解析到教材知识点 URI（跨年级、可纠错、低置信挂起）。
- 从答疑数据沉淀「知识点的题型库」（个体派生 → 共现聚合 → 稳定），业务隔离。
- 掌握度主体翻转：题型直接观测落库（t_student_topic_mastery），知识点覆盖度运行时派生，学生端可见（绿/黄/红 + 疑似态）。
- 派生层全自动维护闭环（冲突检测 → 重判 → 回流先验），权威图零写入。

**Non-Goals**：
- 不写 Neo4j；不做 embedding 语义聚类（后续大数据手段）。
- 不做消费方：变式题生成、错题本分组、薄弱点溯源（LangGraph 阶段 2 复用）。
- 不改变掌握度单调策略（保持「只升、显式纠正才降」）。
- 本期不做掌握度自动迁移（错解析回退只打标 + 人工复核）。
- 本期不删除/迁移旧 KP 掌握度表 t_student_kp_mastery（并行过渡）。

**模块归属（DDD 域定位）摘要**：方案核心业务落在 learning 域；答疑入口与权威图谱边界——派生数据 3 表 + 掌握度 + 点亮 + 审核归 learning 域（数据落 ai_edu_learning）；解析管线 TutoringKpResolverImpl 归 infrastructure/ai/tutoring（答疑 AI 集成层）；权威图谱 Neo4j + kg-sync 镜像归 edukg 域（只读）。learning 域分 4 层落点：domain（com.ai.edu.domain.learning，DerivedKpObs / QuestionType / QuestionTypeKp 实体 + 仓储接口）、infrastructure（persistence.learning，MyBatis-Plus + Flyway）、application（service.learning，聚合/维护服务）、interface（interfaces.api.learning，resolve / pending / confirm / mastery 控制器）。tutoring 不是 domain 域，答疑 Java 网关在 infrastructure/ai/tutoring，属 AI 集成层而非业务域。
