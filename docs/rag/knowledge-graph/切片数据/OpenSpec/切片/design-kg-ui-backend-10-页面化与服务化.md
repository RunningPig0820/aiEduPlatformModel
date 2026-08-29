# 页面化与服务化

> summary: 页面化与服务化
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-10-页面化与服务化.md
> 类别：操作流程

---

> 检索摘要：知识图谱页面化怎么做？为什么选方案 B 把 Neo4j 知识点同步到 MySQL？页面化的目标与非目标是什么？同步的数据范围有多大？

## 决策方向：方案 B（Neo4j 知识点同步到 MySQL，前端 SPA 读取）

知识图谱数据已存储在远程 Neo4j，包含人教版 K-12 数学教材的完整结构。当前 Java 后端无 Neo4j 集成代码。前端为独立部署（尚无 SPA 项目）。

用户选择方案 B：将 Neo4j 知识点数据同步到 MySQL，前端 SPA 读取 MySQL。知识点全局存储，后续班级/老师/学生通过关联表引用知识点 ID。

数据范围：当前阶段先做数学学科的人教版教材知识点同步 + 导航 + 知识体系，后续扩展多学科。

前端职责：后端负责 API 设计和接口实现，前端页面由前端同学根据 API 文档开发。

## 页面化目标（Goals）

- 提供一键同步按钮，将 Neo4j 的 Textbook/Chapter/Section/TextbookKP 同步到 MySQL
- 提供知识点导航 API，支持 学科→年级→教材→章节→小节→知识点 6 级逐级浏览
- 提供年级知识体系 API，构建某年级完整知识结构
- 知识点详情接口返回 2 层父级（小节 + 章节），不过度展示
- 知识点全局存储，预留关联引用字段供后续班级/老师/学生关联
- 提供前端可参考的 API 接口定义和 DTO 结构
- 同步对话框提供学科/年级/学段下拉选择器（从 t_kg_textbook 聚合查询），避免手动输入

## 页面化边界（Non-Goals）

- 不做前端页面开发（后端提供 API，前端自行开发）
- 不做 Neo4j 实时查询（同步到 MySQL 后，前端只读 MySQL）
- 不做知识图谱关系可视化（Statement/Class/PART_OF 等复杂关系）——知识点图谱关系已通过 Neo4j 查询
- 不做管理员审核/重跑功能（后续阶段）
- 不做 AI 批改/举一反三（Python 服务负责）
- 当前不实现权限控制（后续组织结构/权限模块补充）

## 同步数据方案决策要点（D1）

MySQL 存储核心节点属性和层级关系（用于导航和进度统计），图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等）不同步到 MySQL，后续通过 Neo4j 直接查询。

表设计共 8 张：节点主表 4 张（t_kg_textbook / t_kg_chapter / t_kg_section / t_kg_knowledge_point，URI 主键）+ 层级关系表 3 张（t_kg_textbook_chapter / t_kg_chapter_section / t_kg_section_kp）+ 同步记录表 1 张（t_kg_sync_record）。完整建表 SQL 见子块「同步表设计」。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（Context / Goals / Non-Goals / D1）
