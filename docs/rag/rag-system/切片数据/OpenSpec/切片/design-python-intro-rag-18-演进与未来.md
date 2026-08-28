# 演进与未来

> summary: 演进与未来（design-python-project-intro-rag）：Non-Goals边界（不做教育内容检索/不接真实角色/不做图谱召回/不做真mermaid/不做生产级部署），08-21源头设计后由08-25 spec部分反转
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-18-演进与未来.md
> 类别：未来演进

---

### Non-Goals

> 检索摘要：项目介绍RAG的非目标：不做教育领域内容检索（语料是方案文档不是教育数据）、不接真实角色体系（页面权限标签+demo学生最高权限）、不做图谱检索召回、不做真mermaid动态生成、不做生产级部署

**Non-Goals:**
- 不做教育领域内容检索(知识点/题库/答疑)——语料是本项目的方案文档,不是教育数据。
- 不接真实角色体系——权限为页面权限标签 + demo 学生=最高权限,前置校验机制保留。
- 不做图谱检索召回——本系统召回对象是文档(向量+BM25),不接 Neo4j。
- 不做真 mermaid 动态生成——预置为主,动态生成仅兜底。
- 不做生产级部署与鉴权扩展——内部演示系统,Java 桥侧调用沿用 `x-internal-token`。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§Goals / Non-Goals —— Non-Goals 部分）
