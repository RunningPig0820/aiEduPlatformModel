# question-type-mastery-python 提案

## Why

后端方案 `question-type-mastery-backend` 的**题型动态聚集**需要向量相似度检索（把 LLM 猜的散题型名「鸡兔同笼/鸡兔同笼问题/假设法」归并成 canonical）。腾讯 COS **向量桶（Vector Bucket）只有 Python/Go SDK，没有 Java SDK** → 向量操作归 Python 侧做，Java 通过 HTTP 桥调用（复用现有 `TutoringLlmPort` 模式）。本期 Python 只需新增向量服务端点，decide/generate/question-understand 全部零改动。

## What Changes

- **新增 2 个向量端点（唯一改动）**：
  - `POST /api/tutoring/vector/put`：Java 传「文本 + key + metadata」→ Python embedding → 存进 COS 向量桶（key 相同 upsert 覆盖）。
  - `POST /api/tutoring/vector/query`：Java 传「文本 + top_k」→ Python embedding → 查最近邻 Top-K 返回。
- **embedding 在 Python 侧**：复用 gateway 现成 dashscope 配置（`DASHSCOPE_API_KEY` + `dashscope.aliyuncs.com/compatible-mode/v1`），`text-embedding-v3` **768 维**（显式指定，默认 1024）。
- **多索引 + vector_type 必填路由**：`vector_type` 是**每次 put/query 必填**的逻辑类型，Python 内部映射到物理索引；本期唯一合法值 `"topic"`（题型名向量）。`question`/`rag` 索引为配置占位，**后续加索引 Python 零代码改动**。
- **失败语义：错误冒泡**：端点异常返回 HTTP 错误码，Java 桥侧降级（回退字符规则 + 原样落库，不阻塞主链路）。**不复制 question-understand 的「吞异常降级空结果」模式**——向量是基础设施，让 Java 感知失败。
- **本期不落题目向量**（后端 Non-Goal「相似题本期不做」）：`question` 索引只留配置占位，不建索引、不做代码分支。
- **decide / generate / question-understand 明确不动**：掌握信号仍由 Java 从会话 `roundCount`/`answerRequestCount` 推断，不新增 decide 字段。

## Capabilities

### New Capabilities
- `vector-store`: 向量服务端点——dashscope embedding + CosVectorsClient（COS 向量桶 put/query），`vector_type` 索引路由，支撑后端题型动态聚集。

### Modified Capabilities
<!-- 无：纯新增能力，不动既有 spec -->

## Impact

- **新依赖**：`cos-python-sdk-v5`（`CosVectorsClient`）。
- **新文件**：
  - `core/tutoring/vector_store.py`（核心：embedding + put/query 封装，`vector_type` → 索引路由表）
  - `models/vector.py`（`VectorPutRequest`/`VectorQueryRequest`/`VectorHit` 等契约，独立于 `models/tutoring.py`）
  - `api/vector.py`（2 个端点，prefix=`/api/tutoring/vector`）
- **改文件**：
  - `config/settings.py`（+ `COS_VECTORS_SECRET_ID/KEY/REGION/BUCKET/INDEXES`）
  - `main.py`（注册 vector router）
  - `requirements.txt`（+ `cos-python-sdk-v5`）
  - `.env.example`（+ COS 配置注释）
- **配置**：`COS_VECTORS_SECRET_ID/KEY`（子账号密钥）、region、桶名、索引路由表；**复用 `DASHSCOPE_API_KEY`，无需新密钥**。
- **契约**：`vector_type` 必填（本期唯一值 `"topic"`）；snake_case；`x-internal-token` 鉴权。
- **跨仓库**：后端经 `TopicVectorStore` 端口调这两个端点，**Java 不碰 embedding API / COS SDK**。
