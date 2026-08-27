# Context：数据现状与决策方向

> summary: 知识图谱数据存远程Neo4j，Java后端无集成、前端无SPA；决策采用方案B：Neo4j知识点同步到MySQL，前端SPA读MySQL，先做数学学科人教版。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-Context.md
> 类别：项目介绍

> 检索摘要：知识图谱数据存远程Neo4j，Java后端无集成、前端无SPA；决策采用方案B：Neo4j知识点同步到MySQL，前端SPA读MySQL，先做数学学科人教版。

知识图谱数据已存储在远程 Neo4j，包含人教版 K-12 数学教材的完整结构。当前 Java 后端无 Neo4j 集成代码。前端为独立部署（尚无 SPA 项目）。

**决策方向**：用户选择方案 B — 将 Neo4j 知识点数据同步到 MySQL，前端 SPA 读取 MySQL。知识点全局存储，后续班级/老师/学生通过关联表引用知识点ID。

**数据范围**：当前阶段先做数学学科的人教版教材知识点同步 + 导航 + 知识体系。后续扩展多学科。

**前端职责**：后端负责 API 设计和接口实现，前端页面由前端同学根据 API 文档开发。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§Context：数据现状与决策方向）
