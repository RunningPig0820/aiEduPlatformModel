# 模块定位与核心价值

> summary: 模块定位与核心价值
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-01-模块定位与核心价值.md
> 类别：项目介绍

本文档为 AI 教育平台集成 EduKG 知识图谱的设计阶段素材（design-python-2026-03-28-integrate-edukg-knowledge-graph，2026-03-28 设计稿），同时包含已落地、构想未实现、待决策内容；业务真实实现请以权威度 0.8 的 canonical 真相源文档为准。

## 知识图谱在项目中的角色

AI 教育平台当前已有 LLM Gateway 服务，支持智谱、DeepSeek、阿里百炼等多模型调用。现新增知识图谱能力，以支持三大业务场景：
- AI 答疑时识别知识点
- 学生学习进度可视化
- 教师备课推荐

现有服务技术基线：FastAPI + Python 3.11，LLM 集成用 LangChain 框架，配置管理用 Pydantic Settings。

## 目标（Goals）

1. 集成 Neo4j 图数据库，支持知识图谱存储和查询
2. 实现 TTL 文件导入 Neo4j 的工具
3. 提供知识点实体查询 API
4. 实现文本实体链接服务
5. 支持学科知识树可视化数据输出
6. 预留向量数据库接口

## 非目标（Non-Goals）

- 本期不实现向量数据库集成（下一阶段）
- 不实现前端可视化（仅提供 API）
- 不实现自定义知识点编辑（后续扩展）
- 不实现知识图谱增量更新（后续扩展）

## 模块安全与回滚

- Neo4j 数据通过 TTL 文件可重建
- 知识图谱模块独立，不影响现有 LLM 服务
- 可通过配置开关关闭知识图谱功能
