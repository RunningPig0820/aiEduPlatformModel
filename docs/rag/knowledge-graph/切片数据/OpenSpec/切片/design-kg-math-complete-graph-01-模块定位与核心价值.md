# 模块定位与核心价值

> summary: 模块定位与核心价值
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-01-模块定位与核心价值.md
> 类别：项目介绍

---

> 检索摘要：数学知识图谱完整数据管道解决什么问题？项目当前进度到哪？教材知识点与 EduKG 图谱割裂的现状与目标？

## 模块定位

数学知识图谱完整数据管道设计（kg-math-complete-graph）是知识图谱数据处理项目在数学学科上的落地设计。模块价值：把教材数据与 EduKG 知识图谱打通，解析教材 JSON 生成标准化的教材知识点节点与关系，用 LLM 双模型推断补全缺失知识点，并匹配到 EduKG Concept，输出 JSON 供人工验证后导入 Neo4j。本文件属设计阶段素材，同时包含已落地、构想未实现、待决策内容；真实业务实现以权威度 0.8 的 canonical 真相源文档为准。

## 项目背景（已完成的初始化数据）

数学学科核心数据已导入 Neo4j，项目进入知识点补全阶段：
- Neo4j schema 初始化（节点标签、唯一性约束）
- EduKG 数据导入：Class 39、Concept 1,295、Statement 2,932
- 关系导入：RELATED_TO 10,183、SUB_CLASS_OF 38、PART_OF 298、BELONGS_TO 619
- 教材数据生成：Textbook 21、Chapter 138、Section 549、TextbookKP 299

## 当前问题

**1. 教学知识点数据不完整**：小学 1-2 年级 47 个知识点（部分有）；小学 3-6 年级 knowledge_points 全空；初中 7-9 年级 252（较完整）；高中必修全空（仅有综合测试标记）。

**2. 教材知识点与知识图谱割裂**：教材数据在本地 JSON（学段/年级/教材/章节/知识点维度），知识点数据在 Neo4j EduKG（uri/label/type/source/relatedTo 维度），两者靠名称关联。名称不一致问题：教材「正数和负数的概念」vs EduKG「正数的定义」，精确匹配率仅 6%（24/346）。

## 设计约束

1. 输出 JSON 文件：不直接导入 Neo4j，由人工验证后手动导入
2. 核心代码放入 edukg/core：scripts 只做命令行入口
3. 复用双模型推理：依赖 kg-math-prerequisite-inference 的投票机制
4. 所有 LLM 任务支持断点续传：使用 llmTaskLock 模块

## Goals / Non-Goals

Goals：
1. 解析教材 JSON 数据，输出标准格式 JSON
2. LLM 推断补全缺失的教学知识点（小学 3-6 年级、初中、高中）
3. 使用双模型推理匹配教材知识点到 EduKG Concept
4. 输出所有关系数据（CONTAINS、IN_UNIT、MATCHES_KG）
5. 数据清洗：清理「通用」标签、规范 Section 标签
6. 知识点属性扩展：难度、重要性、认知维度、专题分类

Non-Goals：
1. 不直接导入 Neo4j（人工验证后手动导入）
2. 不处理其他学科（仅数学）
3. 不实现新的 LLM 推理机制（复用 kg-math-prerequisite-inference）
4. 不修改已有的 EduKG 节点数据
5. 不实现前置关系推断（由 kg-math-prerequisite-inference 负责）
6. 不实现多版本教材对比（未来迭代）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§Context / Goals-Non-Goals）
