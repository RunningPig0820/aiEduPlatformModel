# 坑档案

> summary: 解决落掌握度反射异常，删除SQL残留列
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J2. 落掌握度 ReflectionException
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J2. 落掌握度 ReflectionException
**1. 问题现象**：答疑落掌握度抛反射异常，掌握度写库失败。

**2. 触发流程**：`applyMasteryAndErrors` → `persistQuestionAttempt`（`TutoringAppService.java:784`）→ `studentTopicMasteryRepository.upsert(mastery)`（`:814`）→ `StudentTopicMasteryMapper.upsert`（MyBatis @Insert 注解 SQL）。

**3. 根因分析**：V21 迁移删了 `evidence`/`last_session_id` 两列（`V21__alter_t_student_topic_mastery_drop_evidence_last_session.sql:6-8`），但 upsert 的 @Insert SQL 仍引用 `#{evidence}`、`#{lastSessionId}` → 执行 SQL 报 Unknown column → MyBatis 抛 ReflectionException。本质是**迁移删列与 Mapper SQL 未同步**。

**4. 排查过程**：看异常堆栈是 ReflectionException（MyBatis 参数绑定）→ 对比 V21 迁移删的列与 upsert SQL 引用的列 → 确认残留 `evidence`/`last_session_id`。

**5. 解决方案 & 改动点**：`StudentTopicMasteryMapper.java:27-31` upsert SQL 去掉 `evidence`/`last_session_id` 的 INSERT 列和 `ON DUPLICATE KEY UPDATE` 项；`25` 行注释注明「evidence/last_session_id 已随 V21 迁移删除，不再读写」。

**6. 面试口述要点**：讲"**数据库迁移与 ORM 映射脱节的坑**"——删列只改迁移不改 Mapper，运行时报反射异常。踩坑收获：**迁移脚本与 DAO SQL 必须同步改**，最好有迁移后回归测试；MyBatis 反射异常要往"字段/列不匹配"方向查。

---
