# 向量存储 Python 桥

> summary: COS 无 Java SDK，向量操作走 Python 桥，Java 经端口 HTTP 调用不碰 SDK/embedding，vector_type 必填路由。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-question-type-mastery-backend-D5-向量存储Python桥.md
> 类别：架构设计

---

### Decision 5：向量存储 = Python 桥（COS Vector Bucket，无 Java SDK 方案）

> 检索摘要：COS 无 Java SDK，向量操作走 Python 桥，Java 经端口 HTTP 调用不碰 SDK/embedding，vector_type 必填路由。

**前提**：COS 向量检索只有 Python/Go SDK（`CosVectorsClient`/`VectorService`），**无 Java SDK**——排除「Java 直调 SDK」。

- **架构**：向量操作全在 Python 侧（复用已有 Java↔Python 桥模式，如 `TutoringLlmPort`）：
  - Python 提供向量端点：`POST /api/tutoring/vector/put`（题型名+metadata → dashscope embedding → `CosVectorsClient.put_vectors`）、`POST /api/tutoring/vector/query`（题型名+top_k → embedding → `query_vectors` → 返回 hits）。**query 响应字段名 `vectors`（非 `hits`）**——对齐 COS `query_vectors` 返回结构；Java 桥解析 `{"vectors":[{key,metadata,distance}]}`。
  - **`vector_type` 必填路由键（Python 契约已定稿）**：每次 put/query 后端显式声明写/查哪个索引，**无缺省、无跨索引查询**；本期唯一合法值 `"topic"`（题型名向量索引）。未知 `vector_type` → Python 400 → **Java 降级**（回退字符规则 + 原样落库，正常失败路径）。后端不感知 COS 索引名——Python 内部 `COS_VECTORS_INDEXES` 路由表（本期 1 条，`question`/`rag` 为纯配置占位，后续加索引零代码改动）。
  - **embedding 在 Python 侧**（复用 gateway 的 dashscope 配置，text-embedding-v3，768 维）。
  - Java 通过 `TopicVectorStore` 端口 HTTP 调 Python，**不碰 embedding API / COS SDK**。
- **为什么 Python 桥而非自研**：① 用上已开通的 Vector Bucket（数据量上来能力强）② embedding 复用 Python 现有 dashscope 配置（密钥不散到 Java）③ **后续 RAG 复用同一套向量基础设施**（用户拍板：业务后续要做 RAG，需打通）。
- **备选**：MySQL 自研（全 Java 零依赖，但不用 Vector Bucket、后续 RAG 要另起）；Java 直调 REST（自实现 COS 签名，成本高）。
- **注意**：COS 是对象存储，**Vector Bucket 是独立的向量存储桶类型**，不是「对象存储 + 向量插件」。
- **写入异步生效（spike 实测，Java 桥必须知道）**：`put_vectors` 后索引 **~10s 异步**构建，**立即 `query` 会 miss**（空 `vectors`）——首题建锚后**无需立查**（本来无近邻）；聚集编排「put 后查」路径要容忍延迟/留重试；联调预期：建锚 put 后 ≥10s，后续题目 query 才可见近邻。
- **Python 侧改动范围**：仅**新增**向量服务端点（`vector_type` 路由 + embedding + put/query；decide/信号链路仍零改动）。**已交付**，241 测试绿。

> 证据：详见 `2.OpenSpec design 决策/design-backend-question-type-mastery-backend.md`（§Decision 5）｜ 语雀-决策记录.md D13 ｜ 完善文档 03-架构与微服务分工.md ｜ 坑档案 J-QT1
