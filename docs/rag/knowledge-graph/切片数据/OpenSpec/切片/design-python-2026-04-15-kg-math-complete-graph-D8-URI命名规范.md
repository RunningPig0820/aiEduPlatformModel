# URI 命名规范 (v3.1)

> summary: URI命名规范v3.1：http://edukg.org/knowledge/3.1/{type}/math#{id}，Textbook/Chapter/Section/TextbookKP按层级编码。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D8-URI命名规范.md
> 类别：数据存储

---

### D8：URI 命名规范 (v3.1)

> 检索摘要：URI命名规范v3.1：http://edukg.org/knowledge/3.1/{type}/math#{id}，Textbook/Chapter/Section/TextbookKP按层级编码。

```
http://edukg.org/knowledge/3.1/{type}/math#{id}
```

| 节点类型 | ID 格式 | 示例 |
|---------|--------|------|
| Textbook | `{publisher}-{grade}{semester}` | `renjiao-g1s` |
| Chapter | `{textbook_id}-{order}` | `renjiao-g1s-1` |
| Section | `{chapter_id}-{order}` | `renjiao-g1s-1-1` |
| TextbookKP | `textbook-{stage}-{seq:05d}` | `textbook-primary-00001` |

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D8：URI 命名规范 (v3.1)）
