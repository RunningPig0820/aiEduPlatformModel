# Migration Plan

> summary: Flyway 新增 ai_edu_learning 4 表，掌握度翻转/解析管线/学生图谱页/维护闭环灰度上线，维护任务最后上线，停任务+关路由即回滚。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-迁移计划.md
> 类别：架构设计

> 检索摘要：Flyway 新增 ai_edu_learning 4 表，掌握度翻转/解析管线/学生图谱页/维护闭环灰度上线，维护任务最后上线，停任务+关路由即回滚。

1. Flyway 迁移新增 4 表（`ai_edu_learning`）：`t_kp_derived_obs`、`t_kp_question_type`、`t_kp_question_type_kp`、`t_student_topic_mastery`。
2. 掌握度主体翻转灰度：`applyMasteryAndErrors` 改落题型掌握度 + 派生覆盖度接口；旧 `t_student_kp_mastery` 保留并行，覆盖度查询无题型映射时回退旧表。
3. 解析管线灰度：先只升级解析逻辑 + 落 obs（不接点亮），验证解析质量后再接点亮。
4. 学生端图谱页新路由，不动 admin 图谱页（复用组件，双入口）。
5. 维护闭环最后上线（依赖 obs/题型库稳定）。回滚：停维护任务 + 关闭学生图谱路由即回退。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§Migration Plan）
