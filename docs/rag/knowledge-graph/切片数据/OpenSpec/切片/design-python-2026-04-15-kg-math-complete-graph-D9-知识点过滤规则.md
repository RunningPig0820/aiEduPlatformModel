# 知识点过滤规则

> summary: 知识点过滤规则：用非知识点标记、前缀与正则过滤"数学活动""例1"等，防止把非知识点当知识点导入。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D9-知识点过滤规则.md
> 类别：数据存储

---

### D9：知识点过滤规则

> 检索摘要：知识点过滤规则：用非知识点标记、前缀与正则过滤"数学活动""例1"等，防止把非知识点当知识点导入。

```python
# 非知识点标记
NON_KNOWLEDGE_POINT_MARKERS = {
    "数学活动", "小结", "整理和复习", "本章综合与测试",
    "本节综合与测试", "复习题", "★数学乐园", ...
}

# 非知识点前缀
NON_KNOWLEDGE_POINT_PREFIXES = [
    "阅读与思考 ", "阅读与思考　",  # 全角空格
    "信息技术应用 ", "信息技术应用　",
    "例",  # 例1, 例2...
    ...
]

# 正则匹配
NON_KNOWLEDGE_POINT_PATTERNS = [
    r"^例\d",  # 例1, 例2...
]
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D9：知识点过滤规则）
