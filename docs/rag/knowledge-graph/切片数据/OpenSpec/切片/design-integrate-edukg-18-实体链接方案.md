# 实体链接方案（jieba + 内存词典）

> summary: 实体链接方案（jieba + 内存词典）
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-integrate-edukg-18-实体链接方案.md
> 类别：架构设计

## 方案选择（D3）

使用结巴分词 + 内存词典匹配做文本→知识图谱实体的链接，不引入 Elasticsearch：
- 已验证效果良好；支持自定义词典；轻量级无需额外服务
- 内存占用仅约 20MB，远低于 Elasticsearch（1-2GB）

## 实体链接流程（无 Elasticsearch）

EntityLinker 初始化：
1. 加载 `entities/*.json` 到内存（约 10MB）
2. 构建 `entity_dict = {label: {uri, subject}}`
3. 将所有 label 添加到 jieba 词典

处理输入文本示例：
```
输入文本: "一元二次方程的解法包括配方法、公式法"
    ↓
jieba.lcut() → ["一元二次方程", "的", "解法", "包括", "配方法", "、", "公式法"]
    ↓
内存字典匹配 → 命中: "一元二次方程", "配方法", "公式法"
    ↓
输出: [{label: "一元二次方程", uri: "..."}, ...]
```

## 实现示例

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

## 准确率风险（R2）与缓解

风险：结巴分词 + 词典匹配可能有误识别。

缓解：
- 后续可引入 BERT/NER 模型提升
- 提供人工校正接口
