# embedding 为什么复用 dashscope 而不进 LLMFactory？

> summary: embedding 为什么复用 dashscope 而不进 LLMFactory？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-52-架构设计-embedding复用dashscope不进LLMFactory.md
> 类别：架构设计

---

## 回答

**核心结论**：embedding 复用 Python 现成的 dashscope 配置（**不引入新密钥**），但**不进 LLMFactory**——因为语义不同：LLMFactory 管对话生成模型（智谱/DeepSeek/百炼），embedding 是向量化原语，职责独立，单独封装在 `vector_store.py`。

**分层展开**：
- **复用 dashscope**：embedding 用 dashscope `text-embedding-v3`（OpenAI 兼容端点），复用现成 dashscope 配置/密钥，不引入新密钥源。（依据：完善文档 03 / 分析-06）
- **为什么不进 LLMFactory**：LLMFactory 是 LLM Gateway（scene→model 对话模型），embedding 语义不同（向量化不是生成），独立封装 `core/tutoring/vector_store.py`（embed/put/query/_resolve_index）职责清晰。（依据：完善文档 03）
- **显式 768 维**：`text-embedding-v3` 默认 1024 维，必须显式 `dimensions=768` 与索引一致（坑档案 J-QT4）。（依据：分析-06 / 坑档案 J-QT4）
- **统一出口**：`vector_store.py` 是唯一核心向量模块，LLM 调 embedding 走它，不散落在各端点。（依据：完善文档 03 落地真相）

> 证据：详见 `7. 引导问题/问题列表.md`（第 52 问）｜ `4.完善文档/03-架构与微服务分工.md` ｜ `3.代码/分析-06-向量动态聚类.md`
