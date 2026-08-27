# D4：配置（settings.py）

> summary: COS_VECTORS_* 配置（region/bucket/indexes 路由表），DASHSCOPE_API_KEY 复用无需新增。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-python-question-type-mastery-python-D4-配置.md
> 类别：数据存储

---

### D4：配置（settings.py）

> 检索摘要：COS_VECTORS_* 配置（region/bucket/indexes 路由表），DASHSCOPE_API_KEY 复用无需新增。

```python
# ============ COS 向量桶 ============
COS_VECTORS_SECRET_ID: str = ""
COS_VECTORS_SECRET_KEY: str = ""
COS_VECTORS_REGION: str = "ap-guangzhou"
COS_VECTORS_BUCKET: str = ""                # "xxx-125xxxx"
COS_VECTORS_INDEXES: dict = {               # 逻辑类型 → 物理索引
    "topic": "topic-index",
    # "question": "question-index",         # 相似题, 预留不建
    # "rag": "rag-index",                   # RAG, 预留不建
}
```

`DASHSCOPE_API_KEY` 复用现成项，无需新增。

> 证据：详见 `2.OpenSpec design 决策/design-python-question-type-mastery-python.md`（§D4）｜ 完善文档 06-题型动态聚集与向量.md
