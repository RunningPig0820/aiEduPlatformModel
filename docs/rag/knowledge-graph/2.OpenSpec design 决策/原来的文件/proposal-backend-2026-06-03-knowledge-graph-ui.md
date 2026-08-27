## Why

知识图谱（EduKG）数据已存储在 Neo4j 中（6,757 节点 / 20,887 关系），但当前系统无法面向用户展示。教师无法按教材/章节浏览知识点，学生无法查看知识体系。同时，Neo4j 是外部依赖，无法直接与 MySQL 中的用户/班级/作业数据关联。

本项目将 Neo4j 知识图谱同步到 MySQL，构建知识点导航页面和年级知识体系视图，为后续的班级掌握情况、学生学习进度、作业推荐等功能打下数据基础。

## What Changes

- 新增 Neo4j → MySQL 同步能力：一键同步教材/章节/小节/知识点节点及层级关系到 MySQL，URI 作为主键
- 新增维度配置表（`t_kg_dimension_config`）：通过类型区分学科/年级/学段，存储 Neo4j 约束值和同步属性，数据人工维护（相对固定）
- 新增知识点导航 API：支持学科→年级→教材→章节→小节→知识点 6 级逐级浏览，所有路径参数使用 URI
- 新增学科/年级下拉选项 API：前端同步对话框使用下拉选择器替代手动输入
- 新增年级知识体系 API：构建某年级完整知识结构
- 图谱关系（MATCHES_KG/PART_OF 等）不同步到 MySQL，后续通过 Neo4j 直接查询
- 为后续业务预留：知识点与作业/错题/班级的关联能力（通过 URI 引用）
- 后端负责 API 设计和 DTO 定义，前端页面由前端同学根据 API 文档开发

## Capabilities

### New Capabilities

- `kg-sync`: Neo4j 到 MySQL 的知识图谱数据同步能力，包括全量同步、同步状态查询、同步历史记录
- `kg-navigation`: 知识点导航查询能力，支持按学科→年级→教材→章节→小节→知识点逐级浏览，以及按学科/年级筛选
- `kg-knowledge-system`: 年级知识体系构建能力，返回某年级完整知识结构（含知识点难度/重要性/认知层级标签）
- `kg-dimension-config`: 维度配置管理能力，维护学科/年级/学段基础数据及 Neo4j 映射关系，为导航和同步提供下拉选项

### Modified Capabilities

<!-- 暂无修改已有 Capability 需求 -->

## Impact

- **Backend 新增模块**: `ai-edu-domain/edukg/` 增加实体、Repository 接口；`ai-edu-infrastructure/` 增加 Neo4j 客户端 + MySQL Repository 实现；`ai-edu-application/` 增加同步服务和查询服务
- **Database 新增表**: 4 张节点主表（uri 主键）+ 3 张层级关联表 + 1 张同步记录表 + 1 张维度配置表（t_kg_dimension_config）
- **Backend 新增 API**: `/api/kg/**` 接口组（同步 + 导航 + 知识体系 + 维度配置下拉选项）
- **Dependencies**: 新增 Neo4j Java Driver 依赖
