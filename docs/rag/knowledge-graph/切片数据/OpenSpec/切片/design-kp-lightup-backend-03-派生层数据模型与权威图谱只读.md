# 派生层数据模型与权威图谱只读

> summary: 派生层数据模型与权威图谱只读
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-backend-03-派生层数据模型与权威图谱只读.md
> 类别：数据存储

---

> 检索摘要：题型派生层 3 张表（t_kp_derived_obs 个体观测 / t_kp_question_type 题型库主表 / t_kp_question_type_kp 题型↔知识点年级分布）全放 ai_edu_learning，Neo4j 与 kg-sync 镜像只读，以 kp_uri 为钩子「借」权威结构。

**D1 派生层只存 MySQL，权威图谱只读**：题型派生层 3 张表全部放 ai_edu_learning，Neo4j 与 kg-sync 镜像只读。理由：题型空间无限（鸡兔同笼、相遇、浓度……无穷），教材知识点有限（可数）。把无限挂到有限上会让图爆炸、污染权威结构。派生层以 kp_uri 为钩子「借」权威结构，图逻辑（兄弟/前置/关联）走现有 KgNeo4jService 只读展开。替代方案：派生节点物化进 Neo4j 扩展命名空间（ExtAlias + ALIAS_OF 边），拒绝——现阶段无图遍历需求（MySQL 键值够用），且增加权威图耦合；留待阶段 2 需图遍历时再评估。

**D3 三张表数据模型**：

t_kp_derived_obs（个体派生/观测，长期尾·无限）：

| 字段 | 说明 |
|---|---|
| id | 主键 |
| student_id | 学生 |
| topic_label | AI 题型/知识点原文（「鸡兔同笼」） |
| kp_uri | 解析结果（TextbookKP URI），可空（PENDING） |
| student_grade | 解析时学生年级（快照） |
| confidence | 解析置信度 0-100 |
| source | llm / mirror / catalog / curated / student_vote |
| status | NEW / WEAK / RESOLVED / CONFLICTED / READJUDICATED / HUMAN_REVIEW |
| occurrence_count | 同生+同题型+同URI 累计次数（去重，非重复行） |
| first_seen_at / updated_at | 时间线 |

UNIQUE(student_id, topic_label, kp_uri)。同生再次遇到同题型 → count+1，不建新行。

t_kp_question_type（聚合题型库主表，精选·有限）：

| 字段 | 说明 |
|---|---|
| id | 主键 |
| topic_label | 题型名（UNIQUE） |
| status | CANDIDATE / STABLE |
| definition | LLM/人工 补的定义（可空） |
| hit_students | 去重学生数 |
| hit_count | 总命中次数 |
| promoted_by | 首个触发学生（溯源） |
| created_at / updated_at | 时间线 |

t_kp_question_type_kp（题型↔知识点 年级分布，1:N）：

| 字段 | 说明 |
|---|---|
| id | 主键 |
| question_type_id | 指向题型主表 |
| kp_uri | 对应知识点 |
| grade_range | 该 kp 覆盖年级段（「4-6」） |
| hit_students / hit_count | 该分布桶统计 |
| ratio | 该 kp 占比（先验用） |

例：鸡兔同笼 → 假设法(4-6, 38) + 二元一次方程组(7-8, 21)。解析②查这张分布表按年级取占比最高。备选：分布存 JSON 列简化表数；选子表——便于按 kp_uri 查询（消费方/错题/变式题都需要按知识点反向找题型）。
