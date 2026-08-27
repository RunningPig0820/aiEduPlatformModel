# 迁移计划

> summary: 向量桥迁移：spike 验证→配置依赖→核心模块→端点→联调；回滚停用端点即可，Java 桥降级不阻塞主链路。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-迁移计划.md
> 类别：架构设计

---

### 迁移计划

> 检索摘要：向量桥迁移：spike 验证→配置依赖→核心模块→端点→联调；回滚停用端点即可，Java 桥降级不阻塞主链路。

1. **spike（前置）**：装 `cos-python-sdk-v5`，确认 `CosVectorsClient` 初始化 + `put_vectors`/`query_vectors` 签名；控制台建 `topic-index`（768 维 cosine）；`text-embedding-v3` 显式 768 验证维度；造 10 条近义题型名入库查 top-1 验证命中。
2. **配置 + 依赖**：`requirements.txt` + `cos-python-sdk-v5`；`settings.py` + `COS_VECTORS_*`；`.env.example` 同步；`.env` 填真实值。
3. **核心模块**：`models/vector.py`（契约，`vector_type` 必填）+ `core/tutoring/vector_store.py`（embedding + CosVectorsClient + 路由）。
4. **端点**：`api/vector.py`（2 端点，`x-internal-token`）+ `main.py` 注册。
5. **测试 + 联调**：单测（mock embedding/COS）+ 与后端 Java 桥联调（put → query 近邻命中）。
6. **回滚**：停用向量端点即可——Java 桥降级回退字符规则 + 原样落库，主链路（题目落库/掌握表/接口）不依赖向量（后端 design 风险项已确认）。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§迁移计划）
