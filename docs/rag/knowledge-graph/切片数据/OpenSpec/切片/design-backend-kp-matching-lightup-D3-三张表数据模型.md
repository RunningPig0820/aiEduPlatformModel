# 三张表数据模型

> summary: 派生层三张表 t_kp_derived_obs（个体观测）/t_kp_question_type（题型库）/t_kp_question_type_kp（题型↔知识点年级分布），obs 按 student+topic+kp 去重计数。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D3-三张表数据模型.md
> 类别：数据存储

> 检索摘要：派生层三张表 t_kp_derived_obs（个体观测）/t_kp_question_type（题型库）/t_kp_question_type_kp（题型↔知识点年级分布），obs 按 student+topic+kp 去重计数。

**`t_kp_derived_obs`（个体派生/观测，长期尾·无限）**

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `student_id` | 学生 |
| `topic_label` | AI 题型/知识点原文（"鸡兔同笼"） |
| `kp_uri` | 解析结果（TextbookKP URI），可空（PENDING） |
| `student_grade` | 解析时学生年级（快照） |
| `confidence` | 解析置信度 0-100 |
| `source` | `llm`/`mirror`/`catalog`/`curated`/`student_vote` |
| `status` | `NEW`/`WEAK`/`RESOLVED`/`CONFLICTED`/`READJUDICATED`/`HUMAN_REVIEW` |
| `occurrence_count` | 同生+同题型+同URI 累计次数（去重，非重复行） |
| `first_seen_at` / `updated_at` | 时间线 |

> UNIQUE(`student_id`, `topic_label`, `kp_uri`)。同生再次遇到同题型 → count+1，不建新行。

**`t_kp_question_type`（聚合题型库主表，精选·有限）**

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `topic_label` | 题型名（UNIQUE） |
| `status` | `CANDIDATE` / `STABLE` |
| `definition` | LLM/人工 补的定义（可空） |
| `hit_students` | 去重学生数 |
| `hit_count` | 总命中次数 |
| `promoted_by` | 首个触发学生（溯源） |
| `created_at` / `updated_at` | 时间线 |

**`t_kp_question_type_kp`（题型↔知识点 年级分布，1:N）**

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `question_type_id` | → 题型主表 |
| `kp_uri` | 对应知识点 |
| `grade_range` | 该 kp 覆盖年级段（"4-6"） |
| `hit_students` / `hit_count` | 该分布桶统计 |
| `ratio` | 该 kp 占比（先验用） |

> 例：鸡兔同笼 → `假设法`(4-6, 38) + `二元一次方程组`(7-8, 21)。解析②就是查这张分布表按年级取占比最高。

> 备选：分布存 JSON 列简化表数；**选子表**——便于按 `kp_uri` 查询（消费方/错题/变式题都需要按知识点反向找题型）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D3 三张表数据模型）
