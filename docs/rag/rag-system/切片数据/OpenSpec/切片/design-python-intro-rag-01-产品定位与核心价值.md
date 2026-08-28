# 产品定位与核心价值

> summary: 产品定位与核心价值（design-python-project-intro-rag）：面试用的项目介绍RAG问答系统，一鱼两吃——产品讲清每个项目页面、RAG=证明能力的引擎，语料空模板须先完善文档再切片
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-python-intro-rag-01-产品定位与核心价值.md
> 类别：项目介绍

---

### Context:项目介绍 RAG 问答系统的背景与现状约束

> 检索摘要：面试用的项目介绍RAG问答系统要解决什么？用RAG引擎给面试官讲清每个项目页面（产品设计/为什么/数据流转/关注点），语料空模板、多版本矛盾、未发布草稿读不到，须先完善文档再切片；复用vector_store/ark_stream，定位不是纯RAG

面试用的**项目介绍 RAG 问答系统**:用 RAG 引擎驱动,给面试官讲清每个项目页面(产品设计 / 为什么这么设计 / 数据流转 / 关注点)。

现状约束:
- 语料来源(语雀文档)大量是**空模板**,同模块**多版本矛盾**,部分**未发布草稿**读不到 —— 必须先完善文档再切片。
- 已有基础设施可直接复用:`vector_store.py`(dashscope embedding 768 维 + COS 向量桶,`rag` 索引已预留)、`ark_stream.py`(doubao 流式,但**当前不采 usage**)、`settings.py`(COS_VECTORS_INDEXES / INTERNAL_TOKEN)、jieba(关键词)、降级模式(错误冒泡 / 吞异常降级 / 20s 内部超时)。
- 定位:**不是纯 RAG**。产品 = 项目介绍问答,RAG = 证明能力的引擎。RAG 本身也作为项目一个功能点被介绍。

设计依据:`docs/project-intro-rag-notes-2026-08-21.md`(讨论纪要,本设计的来源)。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-python-project-intro-rag.md`（§Context）
