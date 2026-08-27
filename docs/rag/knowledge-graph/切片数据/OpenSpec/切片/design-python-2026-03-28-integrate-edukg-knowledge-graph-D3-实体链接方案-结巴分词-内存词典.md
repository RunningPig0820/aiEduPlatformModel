# D3 实体链接方案 → 结巴分词 + 内存词典
> summary: 实体链接用结巴分词+内存词典匹配，仅占约 20MB 内存远低于 Elasticsearch 1-2GB，O(1) 字典查找，启动时加载约 4 万实体。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-D3-实体链接方案-结巴分词-内存词典.md
> 类别：数据关联

> 检索摘要：实体链接用结巴分词+内存词典匹配，仅占约 20MB 内存远低于 Elasticsearch 1-2GB，O(1) 字典查找，启动时加载约 4 万实体。

**选择**: 使用结巴分词 + 内存词典匹配
**原因**:
- 已验证效果良好
- 支持自定义词典
- 轻量级，无需额外服务
- **内存占用仅 ~20MB**，远低于 Elasticsearch（1-2GB）

**流程**:
```
启动时加载实体词典到内存 (~40,000 实体, ~10MB)
    ↓
输入文本
    ↓
jieba.lcut() + 自定义词典
    ↓
内存字典匹配 (O(1) 查找)
    ↓
返回识别结果 [{label, uri, positions}]
```

**实现**:
```python
class EntityLinker:
    def __init__(self):
        # 加载所有实体到内存
        self.entity_dict = {}  # {label: {uri, subject}}
        # 加载到 jieba 词典
        for label in self.entity_dict:
            jieba.add_word(label)

    def link(self, text: str, subject: str = None):
        words = jieba.lcut(text)
        return [{"label": w, "uri": self.entity_dict[w]["uri"]}
                for w in words if w in self.entity_dict]
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§D3 实体链接方案 → 结巴分词 + 内存词典）
