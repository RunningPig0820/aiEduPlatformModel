# D4 模块架构
> summary: 分为 textbook 教材模块与 curriculum 课标模块放 edukg/core/，各自职责单一便于测试，可独立运行也可整合运行。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/python-2026-04-10-textbook-concept-linking-D4-模块架构.md
> 类别：架构设计

> 检索摘要：分为 textbook 教材模块与 curriculum 课标模块放 edukg/core/，各自职责单一便于测试，可独立运行也可整合运行。

**决策**: 分为两个独立模块（教材 + 课标），放在 `edukg/core/` 目录

```
edukg/core/
├── textbook/                    # 教材模块
│   ├── parser.py                # 解析教材 JSON
│   ├── matcher.py               # 匹配知识点
│   └── main.py                  # 主脚本
│
└── curriculum/                  # 课标模块
    ├── pdf_ocr.py               # 百度 OCR（收费）
    ├── kp_extraction.py         # LLM 提取
    ├── relation_builder.py      # 关系构建（Neo4j格式）
    ├── kp_comparison.py         # 对比分析
    └── main.py                  # 主脚本
```

**理由**:
- 教材和课标是两个独立的数据源
- 职责单一，便于测试
- 可独立运行，也可整合运行
- 放在 `edukg/core/` 与现有项目结构保持一致

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-concept-linking.md`（§D4 模块架构）
