# vector_type 路由机制怎么设计的？Java 需要知道物理索引名吗？

> summary: vector_type 路由机制怎么设计的？Java 需要知道物理索引名吗？
> 权威度: 1.0
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/引导问题/引导问题-48-架构设计-vector_type路由Java需知物理索引.md
> 类别：架构设计

---

## 回答

**核心结论**：`vector_type` 是**必填逻辑名路由**——每次 put/query 后端显式声明写/查哪个索引，无缺省、无跨索引查询；**Java 不需要知道物理索引名**，只传逻辑名，Python 内部 `COS_VECTORS_INDEXES` 路由表映射物理索引。

**分层展开**：
- **路由机制**：`vector_type` 必填，本期唯一合法值 `"topic"` → 物理索引 `topic-index`（768 维 cosine）；`question`/`rag` 纯配置占位；未知 → ValueError → 400。（依据：完善文档 03 / 分析-06）
- **Java 不感知 COS**：Java 只知 `vector_type` 逻辑名，不知物理索引名；Python 管索引映射——将来加索引 Java 契约零改动，改名只动 Python 配置。（依据：完善文档 03 / 分析-02）
- **无缺省无跨索引**：每次调用显式声明索引，不允许缺省，不允许一次查询跨多个索引。（依据：完善文档 03）
- **路由表**：`settings.COS_VECTORS_INDEXES`（topic→默认桶；rag/rag-full/rag-slice→RAG 独立桶）。（依据：分析-02 / `settings.py:99-105`）

> 证据：详见 `7. 引导问题/问题列表.md`（第 48 问）｜ `4.完善文档/03-架构与微服务分工.md` ｜ `3.代码/分析-06-向量动态聚类.md`
