# 为什么向量能力要放 Python 桥，而不是 Java 直调 COS？

> summary: 为什么向量能力要放 Python 桥，而不是 Java 直调 COS？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-47-架构设计-向量能力放Python桥Java不直调.md
> 类别：架构设计

---

## 回答

**核心结论**：三个原因——① 腾讯 COS 向量检索**只有 Python/Go SDK，无 Java SDK**，Java 没法直调；② embedding 密钥不能散到 Java，Python 复用现成 dashscope 配置；③ 后续 RAG 复用同一套向量基础设施。Java 只持 `vector_type` 逻辑名，不碰 COS。

**分层展开**：
- **SDK 限制**：COS 向量检索无 Java SDK（只有 Python/Go），Java 后端没法直调——这是架构的硬约束。（依据：完善文档 03 / 分析-02）
- **密钥安全**：embedding 密钥不散到 Java——Python 复用现有 dashscope 配置，不进 LLMFactory。（依据：完善文档 03）
- **复用性**：后续 RAG 复用同一套向量基础设施（`vector_type` 已预留 rag/rag-full/rag-slice 路由）。（依据：完善文档 03 / 分析-06）
- **契约隔离**：Java 只传 `vector_type` 逻辑名（topic），Python `settings.COS_VECTORS_INDEXES` 路由物理索引——改名只动 Python 配置，Java 契约零改动。（依据：完善文档 03 / 分析-02）

> 证据：详见 `7. 引导问题/问题列表.md`（第 47 问）｜ `4.完善文档/03-架构与微服务分工.md` ｜ `3.代码/分析-02-微服务分工.md`
