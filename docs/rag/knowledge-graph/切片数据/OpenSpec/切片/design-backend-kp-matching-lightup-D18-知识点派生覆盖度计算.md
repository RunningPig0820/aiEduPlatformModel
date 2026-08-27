# 知识点派生覆盖度计算

> summary: coverage(kp)=clamp(Σ topic_mastery×ratio,0,75)，ratio 优先题型库分布否则单观测 ratio=1，返回连续 coverage 与离散 masteryLevel 双视图。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D18-知识点派生覆盖度计算.md
> 类别：数据存储

> 检索摘要：coverage(kp)=clamp(Σ topic_mastery×ratio,0,75)，ratio 优先题型库分布否则单观测 ratio=1，返回连续 coverage 与离散 masteryLevel 双视图。

**决策**：`coverage(kp) = clamp(Σ_{topic→kp} (topic_mastery × ratio), 0, 75)`。

- **ratio 来源**：优先 `t_kp_question_type_kp.ratio`（聚合后跨学生分布）；该题型尚未聚合时，用 `t_kp_derived_obs` 该生单观测（topic→kp，ratio 隐式 1）。
- **coverage**：连续值 0-75（封顶，题型四档顶 75）；**masteryLevel**：离散四档（≥75→advanced / ≥50→intermediate / ≥25→beginner / 否则 0），列表与图谱着色用。两者都返回。
- **status/confidence**：取覆盖该 kp 的题型中最高 confidence；存在任一 `status=PENDING` 的题型则整项标疑似态。

**理由**：覆盖度是"该知识点被学生已掌握题型覆盖的程度"，连续值供详情展示、离散档供图谱着色。封顶 75 与题型四档顶对齐，避免多个题型叠加同一 kp 时溢出成无意义高分（多题型覆盖同 kp 的叠加语义留待大数据阶段细调，本期 clamp 保守）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D18 知识点派生覆盖度计算）
