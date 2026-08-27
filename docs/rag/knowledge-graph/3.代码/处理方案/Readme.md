# 3.代码 处理方案

1. 深读模块代码（**Python edukg 管道 + Python ai-edu-ai-service 桥 + Java 同步/点亮 + 前端页面**）——**真读代码是第一铁律**，调用链/枚举/阈值/降级分支全部以实际读到的代码为准
2. 按问题表主题拆 11 大分析主题（见下）
3. 通过提示词 `提示词/代码深读-分析文档-提示词.md` 生成分析-XX 文档
   （含：高层业务调用链 mermaid(带异常分支)、枚举/常量/配置表格、隐性坑与注意事项、对账分类）
4. 产出供 RAG 切片池检索（`doc_type=code_analysis`，权威 0.8，不强制检索摘要）+ 完善文档"落地真相"节引用 + 方案-代码对账的输入

## 本模块 11 大分析主题（2026-08-27 全部完成 ✅）

> 编号调整：04=课标知识图谱构建（独立主线，原规划 04=教材结构化顺延为 05）；Java/前端不在本仓，分析-11 基于 design 撰写并标注"非代码真值"。

| 编号 | 主题 | 覆盖代码 |
|---|---|---|
| 01 | 知识图谱整体架构与数据链路 | edukg/ 全链路 + Neo4j + ai-service 桥 |
| 02 | TTL 数据拆分与 Neo4j Schema | scripts/kg_split/* + create_neo4j_schema |
| 03 | 数据清洗与实体规范化 | scripts/kg_data/textbook/clean_textbook_data、enhance_* |
| 04 | 课标知识图谱构建（curriculum） | core/curriculum/ 8 步流水线 + OCR |
| 05 | 教材数据结构化（Textbook/Chapter/Section） | generate_textbook_data、normalize_textbook_kp |
| 06 | 教材知识点 LLM 推断 | infer_textbook_kp、core/llm_inference、core/llmTaskLock |
| 07 | 知识点匹配与双模型投票 | match_textbook_kp、向量检索、双模型投票 |
| 08 | 前置依赖推断 | scripts/kg_inference/infer_prerequisites、validate_dag |
| 09 | 向量索引构建与校验 | build_vector_index、checksum 校验 |
| 10 | Neo4j 导入与关系构建 | import_*、verify_import、tools/* |
| 11 | Java 同步与前端页面（基于 design） | design-backend-* + design-frontend-*（代码不在本仓） |

> 参照 question-analysis Phase 6：三端一起读、业务描述与业务场景先行、元数据锚点。对账翻转见 `方案-代码对账.md`（24 项）。
