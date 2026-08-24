# 坑档案

> summary: 解决落掌握度反射异常，删除SQL残留列
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: J2. 落掌握度 ReflectionException
> 模块: ai-tutoring ｜ 节: 坑档案

---

### J2. 落掌握度 ReflectionException
- **坑**：答疑落掌握度抛反射异常。
- **根因**：V21 删列后 SQL 残留 `evidence/last_session_id` 未同步。
- **解决**：`StudentTopicMasteryMapper` upsert 去残留列。
- **证据**：`139c03e`。
