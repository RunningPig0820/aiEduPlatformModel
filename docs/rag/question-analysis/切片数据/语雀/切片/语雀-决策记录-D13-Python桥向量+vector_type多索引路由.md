# Python桥向量+vector_type多索引路由
> summary: Java 不直接调用 COS 与 Embedding，通过 HTTP 桥调用 Python 服务；vector_type 参数做多索引路由，支持后续扩展 question、rag 索引。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-决策记录-D13-Python桥向量+vector_type多索引路由.md
> 类别：架构设计

---

### D13 Python 桥向量 + vector_type 多索引路由
> 检索摘要：Java 不直接调用 COS 与 Embedding，通过 HTTP 桥调用 Python 服务；vector_type 参数做多索引路由，支持后续扩展 question、rag 索引。

| 属性 | 内容 |
|---|---|
| 背景 | COS 向量检索无 Java SDK；Java 不碰 embedding API / COS SDK |
| 演进 | 定稿方案，Python 侧统一接管向量操作 |
| 拍板理由 | Java 经 TopicVectorStore 桥 HTTP 调 Python；vector_type 必填路由（本期 topic，question/rag 占位） |
| 系统影响 | 向量操作全在 Python 侧；多索引加索引零代码改动 |
| 证据 | api/vector.py；design-python Decision 1/5 |

> 证据：详见 `1.语雀/语雀-决策记录.md`（§D13）｜ 完善文档 03-架构与微服务分工.md
