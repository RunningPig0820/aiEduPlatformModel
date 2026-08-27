# 实体链接流程（无 Elasticsearch）
> summary: EntityLinker 初始化加载 entities/*.json 到内存构建字典并注入 jieba，输入文本经 jieba.lcut 分词后内存字典 O(1) 匹配输出实体。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-03-28-integrate-edukg-knowledge-graph-实体链接流程-无-elasticsearch.md
> 类别：操作流程

> 检索摘要：EntityLinker 初始化加载 entities/*.json 到内存构建字典并注入 jieba，输入文本经 jieba.lcut 分词后内存字典 O(1) 匹配输出实体。

```
┌─────────────────────────────────────────────────────────────────┐
│                    EntityLinker 初始化                           │
├─────────────────────────────────────────────────────────────────┤
│  1. 加载 entities/*.json 到内存 (~10MB)                          │
│  2. 构建 entity_dict = {label: {uri, subject}}                  │
│  3. 将所有 label 添加到 jieba 词典                               │
└─────────────────────────────────────────────────────────────────┘

输入文本: "一元二次方程的解法包括配方法、公式法"
    ↓
jieba.lcut() → ["一元二次方程", "的", "解法", "包括", "配方法", "、", "公式法"]
    ↓
内存字典匹配 → 命中: "一元二次方程", "配方法", "公式法"
    ↓
输出: [{label: "一元二次方程", uri: "..."}, ...]
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-03-28-integrate-edukg-knowledge-graph.md`（§实体链接流程（无 Elasticsearch））
