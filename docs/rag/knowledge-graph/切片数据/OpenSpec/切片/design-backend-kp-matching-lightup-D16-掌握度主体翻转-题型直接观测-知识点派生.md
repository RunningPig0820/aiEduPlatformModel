# 掌握度主体翻转：题型直接观测，知识点派生

> summary: 掌握度信号主键从 kp_key(URI) 翻转为 topic_key，新增 t_student_topic_mastery 承接题型信号，知识点覆盖度运行时派生不冗余落库。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D16-掌握度主体翻转-题型直接观测-知识点派生.md
> 类别：数据存储

> 检索摘要：掌握度信号主键从 kp_key(URI) 翻转为 topic_key，新增 t_student_topic_mastery 承接题型信号，知识点覆盖度运行时派生不冗余落库。

**决策**：学生掌握的是**题型**（"鸡兔同笼"）不是**知识点**（"二元一次方程组"）——学会鸡兔同笼 ≠ 掌握二元一次方程组。因此：

- 掌握度信号主键从 `kp_key`(URI) 翻转为 `topic_key`（归一化题型名）。
- 新增 `t_student_topic_mastery`（题型掌握度）承接信号落库；知识点覆盖度改为**运行时派生**。

```
学生做题 → 题型掌握度（topic_key + 0/25/50/75 四档）
        → 题型→知识点映射（QuestionTypeKp.ratio / 未聚合时 obs 单观测 ratio=1）
        → 知识点派生覆盖度 coverage(kp) = Σ(覆盖该 kp 的题型掌握度 × ratio)
```

**`t_student_topic_mastery`（题型掌握度主表）**——结构镜像 `t_student_kp_mastery`（只存确定掌握度，`status`/`confidence` 读时从 obs 关联，不冗余落库）

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `student_id` | 学生 |
| `topic_key` | 归一化题型标识（UNIQUE with student_id） |
| `topic_label` | 题型展示名（规范 label） |
| `mastery_level` | 0/25/50/75 四档（复用 `MasteryLevel`） |
| `evidence` | 证据（JSON：命中步骤、错误事件 id 列表） |
| `last_session_id` | 最近一次答疑会话 |
| `updated_at` | 更新时间 |

> UNIQUE(`student_id`, `topic_key`)。同生再次遇到同题型 → 取 max 单调不减（同旧 KP 掌握度策略）。
> `status`(RESOLVED/PENDING) 与 `confidence` 读时组装：RESOLVED 项来自本表 + obs 置信度；PENDING 项来自 obs（kp_uri 为空）并入「待确认」。

**理由**：题型是学生的直接认知对象（这道题会不会做），知识点是题型背后的抽象。直接观测题型 + 派生知识点，既符合认知，也避免"把无限题型硬塞到有限知识点上"导致掌握度粒度错位。知识点覆盖度是"读时计算"，不冗余落库，单一事实源仍是题型掌握度 + 题型→kp 映射。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D16 掌握度主体翻转：题型直接观测，知识点派生）
