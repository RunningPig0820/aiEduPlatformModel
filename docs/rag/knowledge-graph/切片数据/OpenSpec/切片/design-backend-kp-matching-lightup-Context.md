# Context

> summary: AI 答疑 decide 已输出自由文本知识点标签但 TutoringKpResolverImpl 精确/LIKE 落不到图谱，权威图谱 Neo4j+kg-sync 镜像只读，掌握度链路断裂。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-Context.md
> 类别：项目介绍

> 检索摘要：AI 答疑 decide 已输出自由文本知识点标签但 TutoringKpResolverImpl 精确/LIKE 落不到图谱，权威图谱 Neo4j+kg-sync 镜像只读，掌握度链路断裂。

- **现状**：AI 答疑的 decide 已能输出自由文本知识点标签（`question_kps` / `mastery_signals`），但 `TutoringKpResolverImpl` 只做「精确 → LIKE → 未命中丢弃」，真实题型（鸡兔同笼）大量落不到图谱，掌握度链路断裂。
- **权威图谱**：教育局下载，Neo4j 为主 + kg-sync 镜像 `t_kg_knowledge_point`（uri/label）。图谱节点带 URI，前端图谱页（`KnowledgeGraph.jsx`）能按 `node.id` 匹配。
- **掌握度**：`t_student_kp_mastery` 按 `kp_key`(URI) UPSERT，`GET /api/students/{id}/mastery` 已存在，但前端 `getStudentMastery` 定义了没人调用，且学生端没有图谱页（只有 admin 图谱页）。
- **关键约束**：权威图谱（Neo4j + kg-sync 镜像）**零写入**。题型空间无限、图谱节点有限，无限业务数据必须与有限权威结构分存。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§Context）
