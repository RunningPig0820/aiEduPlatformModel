# 数据模型

> summary: 数据模型沿用 build_textbook_data.py 定义结构，含 subject/stage/grade/chapters/sections/knowledge_points 字段。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-textbook-crawler-D6-数据模型.md
> 类别：数据存储

---

### D6：数据模型

> 检索摘要：数据模型沿用 build_textbook_data.py 定义结构，含 subject/stage/grade/chapters/sections/knowledge_points 字段。

**决定**: 沿用 build_textbook_data.py 定义的数据结构

```json
{
  "subject": "math",
  "stage": "primary|middle",
  "grade": "一年级|七年级",
  "semester": "上册|下册",
  "publisher": "人民教育出版社",
  "edition": "人教版",
  "isbn": "",
  "chapters": [
    {
      "chapter_order": 1,
      "chapter_name": "章节名称",
      "sections": [
        {
          "section_order": 1,
          "section_name": "小节名称",
          "knowledge_points": ["知识点1", "知识点2"]
        }
      ]
    }
  ]
}
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-crawler.md`（§D6）
