# 选型4 匹配粗筛：bge-small-zh-v1.5 + numpy vs difflib
> summary: 知识点匹配粗筛用什么？bge-small-zh-v1.5 向量粗筛 top-20（采纳 DeepSeek 建议）替代 difflib，语义更准、准确率提升 10-20%。
> 权威度: 0.8
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/语雀/语雀-方案选型对比-选型4-为什么用bge粗筛不用difflib.md
> 类别：架构设计

| 方案 | 优点 | 缺点 | 结论 |
|---|---|---|---|
| bge-small-zh-v1.5 + numpy | 中文 SOTA/语义强/≤5000 条 <10ms/内存约 3.5GB | 需建索引（60s） | 采用 |
| difflib 字符串相似 | 简单 | 语义弱 | 否决 |
| 证据 | 证据：design-complete-graph D4.3 |  |  |

> 证据：详见 `1.语雀/语雀-方案选型对比.md`（选型4）
