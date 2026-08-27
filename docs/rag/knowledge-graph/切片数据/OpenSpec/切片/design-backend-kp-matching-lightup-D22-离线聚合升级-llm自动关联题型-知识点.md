# 离线聚合升级：LLM 自动关联题型↔知识点

> summary: 题型库聚合从纯计数升级为计数+LLM 自动关联题型→kp 分布，LLM 只做提名、第二独立信号才升 STABLE，题型库自我生长。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D22-离线聚合升级-llm自动关联题型-知识点.md
> 类别：操作流程

> 检索摘要：题型库聚合从纯计数升级为计数+LLM 自动关联题型→kp 分布，LLM 只做提名、第二独立信号才升 STABLE，题型库自我生长。

**决策**：现 `KpQuestionTypeAggregationService` 是纯计数聚合（同名题型命中≥N 建 CANDIDATE），冷启动慢、也无法纠错 LLM 误关联。升级为**计数 + LLM 自动关联**：

- **输入**：达阈值的题型名 + obs 共现的 `(kp_uri, 命中次数, 年级分布桶)`。
- **LLM 输出**：规范化的「题型 → kp 分布（ratio 归一化和=1）」+ 置信度。
- **产出**：建/更新 `t_kp_question_type` + `t_kp_question_type_kp`（CANDIDATE）。

**冷启动弱化沿 Decision 9**：LLM 关联结果不直接 STABLE；第二独立信号（多名学生共现 / 学生投票达标 / 做题结果佐证）才升 STABLE 进解析先验。LLM 只做「提名」，确定性靠「重复 + 客观信号」。

**归属**：`batch` 包（离线，大数据归宿），与 Decision 11 一致。

**理由**：题型库要「自我生长」而非初始化灌数据——在线阶段学生/LLM 把题目和知识点关联成 obs，离线阶段 LLM 从 obs 共现里归纳出可靠的题型→知识点映射，题型库逐步补充。这样第 0 天无题型库也能跑，靠 LLM 消歧冷启动 + 离线聚合慢慢长满。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D22 离线聚合升级：LLM 自动关联题型↔知识点）
