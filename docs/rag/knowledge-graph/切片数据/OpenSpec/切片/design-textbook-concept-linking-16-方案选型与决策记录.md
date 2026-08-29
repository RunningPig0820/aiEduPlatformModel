# 方案选型与决策记录

> summary: 本设计的 6 项关键选型与决策
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-concept-linking-16-方案选型与决策记录.md
> 类别：架构设计

决策 1 数据处理服务（不导入 Neo4j）：生成 JSON/TTL 文件，不直接导入 Neo4j。理由：避免自动创建低质量 Concept；人工确认确保数据准确；匹配报告便于追踪；支持回滚和调整。替代方案：自动导入 Neo4j，可能创建重复/低质量节点且无法回滚。

决策 2 OCR 技术选型：百度 OCR API（收费服务）。理由：用户已有百度 OCR 账号；中文识别效果好；调用简单无需本地部署；支持 QPS 限制和重试。替代方案：PaddleOCR（需本地 GPU 部署、维护成本高）、PyMuPDF（仅提取已有文字，无法识别扫描版）。

决策 3 LLM 选型：智谱 glm-4-flash（免费）。理由：免费成本可控；中文理解能力强；支持 JSON 结构化输出；通过 LangChain 集成。替代方案：DeepSeek、百炼 qwen（均需付费）。

决策 4 模块架构：分为教材 + 课标两个独立模块，放在 edukg/core/ 目录。理由：两个独立数据源；职责单一便于测试；可独立运行也可整合；与现有项目结构保持一致。

决策 5 知识点匹配策略：精确匹配 + LLM 模糊匹配，输出报告。理由：精确匹配成本低先尝试；LLM 模糊匹配提高匹配率；输出报告供人工确认。

决策 6 知识点关系构建策略：LLM 推断关系结构，输出符合 Neo4j 导入格式的独立文件（classes/concepts/statements/relations）。理由：EduKG 有完整关系结构，补充知识点也需建立关系；LLM 能理解知识点语义推断正确关系；分开存储避免单文件过大、便于错误定位；符合 Neo4j 导入格式可直接复用现有导入脚本。URI 命名：版本 0.2，格式 `{label_pinyin}-{md5_32bit}`。
