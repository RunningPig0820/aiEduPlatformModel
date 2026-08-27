# 风险与权衡

> summary: 列举向量桥运行风险（维度绑定/签名未知/权限/冷启动/端点不可用）与缓解手段，明细见正文。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-风险与权衡.md
> 类别：架构设计

---

### 风险与权衡

> 检索摘要：列举向量桥运行风险（维度绑定/签名未知/权限/冷启动/端点不可用）与缓解手段，明细见正文。

- [embedding 维度坑：text-embedding-v3 默认 1024，需显式 768，且索引建好后不可改] → spike 第一步验证维度 + 建索引，`dimensions=768` 写死在常量。
- [CosVectorsClient 初始化/put/query 签名未知] → spike 前置，官方 Python 示例跑通再写封装。
- [`query_vectors` 是否支持 metadata filter 不确定] → 多索引已规避（靠索引隔离，不靠 filter）；即使支持也不依赖。
- [建索引方式：控制台 vs SDK `create_index`] → 建议控制台建（`create_index` API 名不确定）；spike 定，两路都记。
- [子账号密钥权限不足] → 桶策略需授权向量桶操作；联调前确认（待提供参数清单）。
- [向量库冷启动（无近邻建新）] → 后端已设计首题建锚；Python 侧无感。
- [端点不可用拖慢主链路] → Java 桥 HTTP 超时短 + 降级；Python 正常错误码即可。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§风险与权衡）｜ 坑档案 J-QT4
