# 迁移策略：并行保留 + 派生覆盖

> summary: 旧 t_student_kp_mastery 本期保留不动，新增 t_student_topic_mastery 承接新题型信号，覆盖度查询优先题型派生、无映射回退旧表，旧表后续下线。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D20-迁移策略-并行保留-派生覆盖.md
> 类别：未来演进

> 检索摘要：旧 t_student_kp_mastery 本期保留不动，新增 t_student_topic_mastery 承接新题型信号，覆盖度查询优先题型派生、无映射回退旧表，旧表后续下线。

**决策**：旧 `t_student_kp_mastery`（student_id + kp_key）**本期保留不动**，错题本/既有掌握度查询不受影响；新增 `t_student_topic_mastery` 承接新题型信号。知识点覆盖度查询顺序：**优先题型派生** → 无题型映射的 kp 回退旧 KP 掌握度（过渡期兜底）→ 随题型库覆盖率提升逐步弱化旧表依赖。旧表归档/删除列为后续（需大数据侧 + 覆盖率达标后），本期不删。

**理由**：翻转是主键语义变更，一次性迁移破坏面大（错题本、掌握度追踪、历史数据）。并行两表 + 读时派生，可灰度、可回退、不锁旧链路；题型侧数据自然积累到覆盖旧表后，再择机下线旧表。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D20 迁移策略：并行保留 + 派生覆盖）
