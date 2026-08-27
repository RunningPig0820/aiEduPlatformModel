# Goals / Non-Goals

> summary: 目标：一键同步Neo4j教材节点到MySQL、6级知识点导航、年级知识体系API、详情返回2层父级、下拉选择器；非目标：不做前端页面、不做Neo4j实时查询。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-Goals-Non-Goals.md
> 类别：项目介绍

> 检索摘要：目标：一键同步Neo4j教材节点到MySQL、6级知识点导航、年级知识体系API、详情返回2层父级、下拉选择器；非目标：不做前端页面、不做Neo4j实时查询。

**Goals:**
- 提供一键同步按钮，将 Neo4j 的 Textbook/Chapter/Section/TextbookKP 同步到 MySQL
- 提供知识点导航 API，支持学科→年级→教材→章节→小节→知识点 6 级逐级浏览
- 提供年级知识体系 API，构建某年级完整知识结构
- 知识点详情接口返回 2 层父级（小节 + 章节），不过度展示
- 知识点全局存储，预留关联引用字段供后续班级/老师/学生关联
- 提供前端可参考的 API 接口定义和 DTO 结构
- 同步对话框提供学科/年级/学段下拉选择器（从 t_kg_textbook 聚合查询），避免手动输入

**Non-Goals:**
- 不做前端页面开发（后端提供 API，前端自行开发）
- 不做 Neo4j 实时查询（同步到 MySQL 后，前端只读 MySQL）
- 不做知识图谱关系可视化（Statement/Class/PART_OF 等复杂关系）— **知识点图谱关系已通过 Neo4j 查询**
- 不做管理员审核/重跑功能（后续阶段）
- 不做 AI 批改/举一反三（Python 服务负责）
- 当前不实现权限控制（后续组织结构/权限模块补充）

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§Goals / Non-Goals）
