# Goals / Non-Goals
> summary: 目标解析教材 JSON、匹配教材知识点与 Neo4j Concept、OCR+LLM 提取课标知识点并输出对比报告与 JSON/TTL；不自动导入、仅数学、不做作业切题。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/python-2026-04-10-textbook-concept-linking-Goals-Non-Goals.md
> 类别：项目介绍

> 检索摘要：目标解析教材 JSON、匹配教材知识点与 Neo4j Concept、OCR+LLM 提取课标知识点并输出对比报告与 JSON/TTL；不自动导入、仅数学、不做作业切题。

**Goals:**

1. 解析教材 JSON 数据，生成章节结构文件
2. 匹配教材知识点与 Neo4j Concept，生成匹配报告
3. OCR 识别课标 PDF（百度 OCR API，收费）
4. LLM 提取课标知识点（glm-4-flash 免费）
5. 对比课标知识点与 EduKG Concept，生成对比报告
6. 输出 JSON/TTL 格式文件

**Non-Goals:**

1. **不自动导入 Neo4j**（人工确认后手动导入）
2. 不处理其他学科（物理、化学）的教材，仅数学
3. 不实现作业切题功能（后续迭代）
4. 不实现学生学习状态跟踪（后续迭代）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-concept-linking.md`（§Goals / Non-Goals）
