# 目标与非目标

> summary: 目标是爬取教师之家人教版数学教材目录，解析章节与知识点并生成兼容 main.ttl 的 TTL 及 JSON；不爬课件教案、不建前置关系。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-textbook-crawler-Goals-Non-Goals.md
> 类别：项目介绍

---

### 目标与非目标

> 检索摘要：目标是爬取教师之家人教版数学教材目录，解析章节与知识点并生成兼容 main.ttl 的 TTL 及 JSON；不爬课件教案、不建前置关系。

**Goals:**
- 从教师之家爬取人教版数学教材目录（小学+初中+高中）
- 解析章节结构和知识点列表
- 生成与 main.ttl 兼容的 TTL 格式数据
- 输出 JSON 格式便于验证和分析

**Non-Goals:**
- 不爬取课件、教案等具体内容
- 不爬取其他学科（仅数学）
- 不爬取其他版本教材（仅人教版）
- 不建立知识点前置关系（仅目录结构）

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-crawler.md`（§目标与非目标）
