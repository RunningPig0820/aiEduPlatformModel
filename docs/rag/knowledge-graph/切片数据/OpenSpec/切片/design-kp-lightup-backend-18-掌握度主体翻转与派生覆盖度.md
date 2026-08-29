# 掌握度主体翻转与派生覆盖度

> summary: 掌握度主体翻转与派生覆盖度
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-backend-18-掌握度主体翻转与派生覆盖度.md
> 类别：数据关联

---

> 检索摘要：掌握度信号主键从 kp_key(URI) 翻转为 topic_key（归一化题型名），新增 t_student_topic_mastery 承接题型信号，知识点覆盖度运行时派生不冗余落库；coverage(kp)=clamp(Σ topic_mastery×ratio, 0, 75)；旧 t_student_kp_mastery 并行保留过渡。

**D16 掌握度主体翻转：题型直接观测，知识点派生**

学生掌握的是题型（「鸡兔同笼」）不是知识点（「二元一次方程组」）——学会鸡兔同笼 ≠ 掌握二元一次方程组。因此：
- 掌握度信号主键从 kp_key(URI) 翻转为 topic_key（归一化题型名）。
- 新增 t_student_topic_mastery（题型掌握度）承接信号落库；知识点覆盖度改为运行时派生。

学生做题 → 题型掌握度（topic_key + 0/25/50/75 四档）→ 题型→知识点映射（QuestionTypeKp.ratio / 未聚合时 obs 单观测 ratio=1）→ 知识点派生覆盖度 coverage(kp) = Σ(覆盖该 kp 的题型掌握度 × ratio)

t_student_topic_mastery（题型掌握度主表）——结构镜像 t_student_kp_mastery（只存确定掌握度，status/confidence 读时从 obs 关联，不冗余落库）：

| 字段 | 说明 |
|---|---|
| id | 主键 |
| student_id | 学生 |
| topic_key | 归一化题型标识（UNIQUE with student_id） |
| topic_label | 题型展示名（规范 label） |
| mastery_level | 0/25/50/75 四档（复用 MasteryLevel） |
| evidence | 证据（JSON：命中步骤、错误事件 id 列表） |
| last_session_id | 最近一次答疑会话 |
| updated_at | 更新时间 |

UNIQUE(student_id, topic_key)。同生再次遇到同题型 → 取 max 单调不减（同旧 KP 掌握度策略）。status(RESOLVED/PENDING) 与 confidence 读时组装：RESOLVED 项来自本表 + obs 置信度；PENDING 项来自 obs（kp_uri 为空）并入「待确认」。理由：题型是学生的直接认知对象（这道题会不会做），知识点是题型背后的抽象。直接观测题型 + 派生知识点，既符合认知，也避免「把无限题型硬塞到有限知识点上」导致掌握度粒度错位。知识点覆盖度是「读时计算」，不冗余落库，单一事实源仍是题型掌握度 + 题型→kp 映射。

**D17 topic_key 归一化（题型标识主键）**：题型标识用归一化后的题型名 topic_key 作主键，topic_label 只作展示。归一化函数落 domain（TopicKeyNormalizer），规则：Unicode NFKC 全角→半角、trim + 空白折叠、去末尾标点（「鸡 兔 同 笼」/ 全角写法 / 带标点 → 同一 key）。SHALL NOT 剥离「问题/题型」等后缀——「相遇问题/追及问题/工程问题」里的「问题」是题型名固有部分，剥离会丢语义（同义词聚类留大数据阶段）。理由：题型空间无限且命名不规整（LLM 随手输出），自由文本直接作主键会导致同题型裂成多行、掌握度分散。归一化收敛到稳定 key，又与 t_kp_derived_obs.topic_label / t_kp_question_type.topic_label 对齐（题型库晋升后按 topic_key 关联）。冷启动首次遇到题型即可落掌握度，无需等题型库聚合——这是选 topic_key 而非 question_type_id 外键的核心原因（外键会冷启动断裂）。

**D18 知识点派生覆盖度计算**：coverage(kp) = clamp(Σ_{topic→kp} (topic_mastery × ratio), 0, 75)。
- ratio 来源：优先 t_kp_question_type_kp.ratio（聚合后跨学生分布）；该题型尚未聚合时，用 t_kp_derived_obs 该生单观测（topic→kp，ratio 隐式 1）。
- coverage：连续值 0-75（封顶，题型四档顶 75）；masteryLevel：离散四档（≥75→advanced / ≥50→intermediate / ≥25→beginner / 否则 0），列表与图谱着色用。两者都返回。
- status/confidence：取覆盖该 kp 的题型中最高 confidence；存在任一 status=PENDING 的题型则整项标疑似态。

理由：覆盖度是「该知识点被学生已掌握题型覆盖的程度」，连续值供详情展示、离散档供图谱着色。封顶 75 与题型四档顶对齐，避免多个题型叠加同一 kp 时溢出成无意义高分（多题型覆盖同 kp 的叠加语义留待大数据阶段细调，本期 clamp 保守）。

**D20 迁移策略：并行保留 + 派生覆盖**：旧 t_student_kp_mastery（student_id + kp_key）本期保留不动，错题本/既有掌握度查询不受影响；新增 t_student_topic_mastery 承接新题型信号。知识点覆盖度查询顺序：优先题型派生 → 无题型映射的 kp 回退旧 KP 掌握度（过渡期兜底）→ 随题型库覆盖率提升逐步弱化旧表依赖。旧表归档/删除列为后续（需大数据侧 + 覆盖率达标后），本期不删。理由：翻转是主键语义变更，一次性迁移破坏面大（错题本、掌握度追踪、历史数据）。并行两表 + 读时派生，可灰度、可回退、不锁旧链路；题型侧数据自然积累到覆盖旧表后，再择机下线旧表。
