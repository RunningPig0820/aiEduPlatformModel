# Context：单数据源现状与独立库诉求

> summary: Spring Boot 3.2.5 + MyBatis-Plus 3.5.5 当前单数据源 ai_edu_user，知识图谱 EduKG 需独立库 ai_edu_kg 物理隔离，无 JPA 无自定义 DataSource。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-datasource-Context.md
> 类别：项目介绍

---

### Context：单数据源现状与独立库诉求

> 检索摘要：Spring Boot 3.2.5 + MyBatis-Plus 3.5.5 当前单数据源 ai_edu_user，知识图谱 EduKG 需独立库 ai_edu_kg 物理隔离，无 JPA 无自定义 DataSource。

当前项目使用 Spring Boot 单数据源配置，所有 MyBatis-Plus Mapper 都连接到一个 MySQL 数据库 `ai_edu_user`。知识图谱（EduKG）需要独立数据库 `ai_edu_kg` 存储，实现物理隔离和独立扩展。项目使用 MyBatis-Plus 3.5.5 + Spring Boot 3.2.5，无 JPA/Hibernate，无自定义 DataSource 配置。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-datasource.md`（§Context）
