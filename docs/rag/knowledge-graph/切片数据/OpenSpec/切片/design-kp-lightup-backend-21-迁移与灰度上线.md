# 迁移与灰度上线

> summary: 迁移与灰度上线
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kp-lightup-backend-21-迁移与灰度上线.md
> 类别：操作流程

---

> 检索摘要：Flyway 新增 ai_edu_learning 4 表，掌握度翻转/解析管线/学生端图谱页/维护闭环四步灰度上线，维护任务最后上线；回滚=停维护任务 + 关闭学生图谱路由。

1. Flyway 迁移新增 4 表（ai_edu_learning）：t_kp_derived_obs、t_kp_question_type、t_kp_question_type_kp、t_student_topic_mastery。
2. 掌握度主体翻转灰度：applyMasteryAndErrors 改落题型掌握度 + 派生覆盖度接口；旧 t_student_kp_mastery 保留并行，覆盖度查询无题型映射时回退旧表。
3. 解析管线灰度：先只升级解析逻辑 + 落 obs（不接点亮），验证解析质量后再接点亮。
4. 学生端图谱页新路由，不动 admin 图谱页（复用组件，双入口）。
5. 维护闭环最后上线（依赖 obs/题型库稳定）。回滚：停维护任务 + 关闭学生图谱路由即回退。
