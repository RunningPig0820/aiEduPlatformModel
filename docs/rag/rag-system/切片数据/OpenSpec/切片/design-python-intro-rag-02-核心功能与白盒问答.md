# 核心功能与白盒问答

> summary: 核心功能与白盒问答（design-python-project-intro-rag）：覆盖4个有内容模块+RAG自身介绍，文档完善→双池检索→页面锚定→两道门→生成带引用→token真算→追问上限→降级矩阵，每阶段有测试
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-02-核心功能与白盒问答.md
> 类别：操作流程

---

### Goals

> 检索摘要：项目介绍RAG的核心功能目标：覆盖知识图谱/AI答疑/组织中心/学生知识点分析四模块（RAG自身第5个介绍点），文档完善后双池检索、页面锚定、两道门、token真算、追问上限5轮、降级矩阵，每个关键阶段有测试

**Goals:**
- 覆盖 4 个有内容的模块:知识图谱 / AI答疑 / 组织中心 / 学生知识点分析(RAG 自身作为第 5 个介绍点)。
- 文档准备:语雀 + 代码 + OpenSpec → 完善成每模块「完善版设计文档」→ 切片 → 嵌入 → COS 索引。
- 双池检索:索引层池(预写 QA,可控)+ 源文档池(纯 RAG)。
- 页面锚定:前端传 `page`,页面模式锁页 / 全局模式跨页。
- 两道门:权限门(前置校验)+ 范围门(检索置信度 → 边界回答不硬编)。
- 生成带引用、按页标注;token 真算(usage 流结束更新)并展示成本。
- 追问上限 5 轮;逐环节降级矩阵。
- **每个关键阶段有测试**。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§Goals / Non-Goals —— Goals 部分）
