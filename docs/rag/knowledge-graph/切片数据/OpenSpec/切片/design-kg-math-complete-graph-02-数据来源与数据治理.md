# 数据来源与数据治理

> summary: 数据来源与数据治理
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-02-数据来源与数据治理.md
> 类别：数据关联

---

> 检索摘要：数据从哪里来？教材 JSON 与 EduKG 数据的关系？怎么过滤非知识点、清洗「通用」标签、规范 Section 名称？

## 数据来源

本文档涉及两类数据源：
1. **EduKG 知识图谱数据**（Neo4j）：Class 39、Concept 1,295、Statement 2,932，关系 RELATED_TO 10,183、SUB_CLASS_OF 38、PART_OF 298、BELONGS_TO 619。本阶段不修改已有 EduKG 节点数据。
2. **教材 JSON 数据**（本地）：小学/初中/高中教材目录，Textbook 21、Chapter 138、Section 549、TextbookKP 299。当前阶段仅人教版，多版本（北师大/苏教版）作为 v3.2 规划。

数据可信度保障：输出 JSON 不直接导入 Neo4j，由人工验证后手动导入；数据清洗只清理冗余标签，不误删有效数据。

## 知识点过滤规则（D9）

防止把非知识点（"数学活动""例1"等）当知识点导入：
- 非知识点标记 NON_KNOWLEDGE_POINT_MARKERS："数学活动"、"小结"、"整理和复习"、"本章综合与测试"、"本节综合与测试"、"复习题"、"数学乐园"（源数据带星号前缀）等
- 非知识点前缀 NON_KNOWLEDGE_POINT_PREFIXES："阅读与思考 "、"信息技术应用 "、"例"（例1、例2）等（含全角空格变体）
- 正则模式 NON_KNOWLEDGE_POINT_PATTERNS：`^例\d`（例1、例2...）

## 数据清洗设计（D10）

问题：部分章节带"（通用）"字样，部分 Section 带序号前缀和不规范标点。

解决方案（DataCleaner）：
- "通用"标签处理：GENERIC_SUFFIXES = ["（通用）", "(通用)", "（综合）", "(综合)"]
- Section 标签清洗模式 SECTION_CLEANUP_PATTERNS：`^\d+\.\d+-` 移除前缀如 "3.1-"；`^\d+\.\d+\.\d+-` 移除前缀如 "18.1.1-"；`:$|：$` 移除末尾冒号
- clean_section_label：按模式逐个剔除序号前缀与末尾冒号后去空格
- detect_generic_duplicate：检测"通用"标签的重复数据（同名带/不带"通用"的章节），供人工确认

风险缓解（R5）：清理"通用"标签可能误删有效数据，先检测并列出候选重复数据，人工确认后再处理。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D9 / §D10 / §R5）
