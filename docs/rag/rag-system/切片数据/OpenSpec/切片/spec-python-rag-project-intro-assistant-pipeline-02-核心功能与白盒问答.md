# 核心功能与白盒问答
> summary: 核心功能与白盒问答
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-project-intro-assistant-pipeline-02-核心功能与白盒问答.md
> 类别：操作流程

---

## 文档说明
> 本文件由 OpenSpec 设计素材（spec-python-rag-project-intro-assistant-pipeline.md）按业务主题「核心功能与白盒问答」重切合并。
> 设计阶段素材：真实实现以权威度 0.8 的 canonical 真相源 + 代码为准（代码已部分落地）；含 已落地 / 构想未实现 / 待决策 内容，引用需核对代码。

### Purpose：白盒 RAG 链路引擎（一次完整问答的流水线）
> 检索摘要：Python 白盒 RAG 链路引擎的定位与各阶段流水线是什么？

Python 白盒 RAG 链路引擎：intent（LLM 结构化输出 + 关键词兜底）→ rewrite → recall（向量+BM25，按 anchor 选池，单路 2s 超时降级）→ rerank（RRF Top-K，仅回传精排块）→ generate（doubao 流式）。产出与后端契约一致的 SSE 事件与 done 结果。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-project-intro-assistant-pipeline.md`（§Purpose）
