# 三端架构分工

> summary: 三端架构分工（design-java-rag-project-intro-assistant）：模块id闭集三端统一、sessionId前端生成Java聚合、查看原文走Java source代理前端不直连Python
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-15-三端架构分工.md
> 类别：架构设计

---

### D-A. 模块 id 闭集(三端统一)

> 检索摘要：模块id闭集三端统一：ai-tutoring/knowledge-graph/question-analysis/rag-system，弃用rag-project/question-type，语料按tags.module过滤，candidates为字符串id数组

闭集 = `ai-tutoring`(AI答疑)/ `knowledge-graph`(知识图谱)/ `question-analysis`(题型分析)/ `rag-system`(RAG 项目)。**弃用** `rag-project`、`question-type`。语料选池按块级 metadata `tags.module == anchor` 过滤(**不依赖目录同名**);`slice_corpus` 的 module 参数化(不再硬编码)。clarify `candidates` 为**字符串 id 数组**,中文 label 由前端 `pageModuleMap` 维护(Python 不产 label、契约零改动),点选候选以 id 作 `currentProject` 重发原问。

### D-C. sessionId 由前端生成

> 检索摘要：sessionId由前端挂载UUID生成整场复用，Java以sessionId为键累计token，ask未知session按新会话，close未知返回10002

前端面板挂载生成 UUID(复用 `generateSessionId` 模式)整场复用;Java 以 sessionId 为键累计 token;ask 未知 session 按新会话(累计从 0),close 未知 session → 10002。

### D-D. 查看原文走 Java 代理

> 检索摘要：查看原文走Java代理：GET source转发Python file_path，前端不直连Python，file_path走query传参避免容器拒

新增 `GET /api/rag/assistant/source?path=<urlencoded>`(STUDENT 角色门)转发 Python `/api/rag/source/{file_path}`;Python 保留挂载作转发目标,前端**不直连 Python**。file_path 走 query 传参(不走 path,避免特殊字符被容器拒)。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§D-A/D-C/D-D）
