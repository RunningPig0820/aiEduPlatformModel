# 精确匹配增强

> summary: 精确匹配增强：名称标准化处理（去空格统一括号）加同义词映射SYNONYM_MAP，完整词匹配防止过度匹配。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D4-4-精确匹配增强.md
> 类别：数据关联

---

### D4.4：精确匹配增强

> 检索摘要：精确匹配增强：名称标准化处理（去空格统一括号）加同义词映射SYNONYM_MAP，完整词匹配防止过度匹配。

**标准化处理**:
```python
def _normalize_name(self, name: str) -> str:
    # 转小写、去空格、统一括号
    normalized = name.strip().lower()
    normalized = normalized.replace(' ', '').replace('　', '')  # 半角/全角空格
    normalized = normalized.replace('（', '(').replace('）', ')')
    return normalized
```

**同义词映射**（完整词匹配，防止过度匹配）:
```python
SYNONYM_MAP = {
    "加法": ["加", "加法运算", "相加", "求和"],
    "百分数": ["百分比", "百分率"],
    ...
}
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D4.4：精确匹配增强）
