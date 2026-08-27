# embedding 维度绑定
> summary: COS 向量索引维度必须等于 embedding 输出维度，建好后不可改；text-embedding-v3 需显式 dimensions=768，spike 顺序必须先验证维度再建索引。
> 权威度: 0.8
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/语雀/语雀-边界场景清单-场景23-embedding维度绑定.md
> 类别：开发难点
> 状态：✅

---

### 场景23：embedding 维度绑定（索引维度建好后不可改）
> 状态：✅
> 检索摘要：COS 向量索引维度必须等于 embedding 输出维度，建好后不可改；text-embedding-v3 需显式 dimensions=768，spike 顺序必须先验证维度再建索引。

| 属性 | 内容 |
|---|---|
| 业务场景 | embedding 维度绑定约束 |
| 触发条件 | 索引维度与 embedding 输出维度不一致，或误用默认 1024 维度 |
| 当前处理 | text-embedding-v3 显式 dimensions=768 写死常量；topic-index 控制台已建 768 维 cosine |
| 兜底降级策略 | 维度建好后不可改；qwen3.7 与 text-embedding-v3 同为 768 兼容，未来切模型只换模型名索引不重建 |
| 残余风险 | 若误建错维度需重建索引 + 全量重入 |
| 证据 | design-python-question-type-mastery-python D2 |

> 证据：详见 `1.语雀/语雀-边界场景清单.md`（§场景23）｜ 完善文档 06-题型动态聚集与向量.md ｜ 坑档案.md J-QT4 ｜ OpenSpec design-python-question-type-mastery-python D2（历史设计文档，请核对代码确认实际落地）
