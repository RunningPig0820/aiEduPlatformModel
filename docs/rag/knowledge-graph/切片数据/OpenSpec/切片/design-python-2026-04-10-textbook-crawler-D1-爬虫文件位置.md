# 爬虫文件位置

> summary: 爬虫脚本放 edukg/scripts/textbook_data/ 目录，renjiaoshe_math_crawler.py 明确标明人教版数学，与项目结构保持一致。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-textbook-crawler-D1-爬虫文件位置.md
> 类别：架构设计

---

### D1：爬虫文件位置

> 检索摘要：爬虫脚本放 edukg/scripts/textbook_data/ 目录，renjiaoshe_math_crawler.py 明确标明人教版数学，与项目结构保持一致。

**决定**: 爬虫脚本放在 `edukg/scripts/textbook_data/` 目录下，明确标明是人教版数学

**文件路径**:
```
edukg/
└── scripts/
    └── textbook_data/                      # 教材数据处理脚本
        ├── __init__.py
        ├── renjiaoshe_math_crawler.py      # 人教版数学教材爬虫
        └── textbook_parser.py              # 目录解析器（通用）
```

**理由**:
- 与现有项目结构保持一致
- `scripts/` 目录用于存放工具脚本
- `textbook_data/` 子目录明确表示教材数据相关脚本
- 文件名 `renjiaoshe_math_crawler.py` 明确标明是人教版数学

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-crawler.md`（§D1）
