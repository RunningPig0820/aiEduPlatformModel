# 数据格式

> summary: 同时输出 JSON（人工验证）与 TTL（与 main.ttl 兼容、可用 n10s 导入 Neo4j）两种格式。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-textbook-crawler-D3-数据格式.md
> 类别：数据存储

---

### D3：数据格式

> 检索摘要：同时输出 JSON（人工验证）与 TTL（与 main.ttl 兼容、可用 n10s 导入 Neo4j）两种格式。

**决定**: 同时输出 JSON 和 TTL 两种格式

**JSON 格式** (用于人工查看和验证):
```json
{
  "subject": "math",
  "stage": "primary",
  "grade": "一年级",
  "semester": "上册",
  "publisher": "人民教育出版社",
  "edition": "人教版",
  "source_url": "https://www.renjiaoshe.com/jiaocai/19.html",
  "crawled_at": "2026-03-30T19:00:00",
  "chapters": [
    {
      "chapter_order": 1,
      "chapter_name": "准备课",
      "sections": [
        {
          "section_order": 1,
          "section_name": "数一数",
          "knowledge_points": ["数数", "一一对应"]
        },
        {
          "section_order": 2,
          "section_name": "比多少",
          "knowledge_points": ["比较", "多与少"]
        }
      ]
    }
  ]
}
```

**TTL 格式** (与 main.ttl 兼容，用于导入 Neo4j):
```turtle
@prefix ns1: <http://edukg.org/knowledge/3.0/ontology/data_property/main#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://edukg.org/knowledge/3.0/instance/math#textbook-primary-00001>
    a <http://edukg.org/knowledge/3.0/ontology/class/main#KnowledgePoint> ;
    rdfs:label "数数" ;
    ns1:temp '{"book": "一年级数学上册", "chapter": "准备课", "section": "数一数", "mark": "1.1"}' .
```

**理由**:
- JSON 便于人工查看、编辑和验证
- TTL 与 EDUKG main.ttl 格式完全兼容
- 可直接使用 n10s 导入 Neo4j

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-crawler.md`（§D3）
