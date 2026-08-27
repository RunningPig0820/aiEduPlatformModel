# 数据保存位置

> summary: 教材数据存 edukg/data/textbook/，按 学科-教材-学段-年级 四级目录组织，便于精确查询与扩展其他版本。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-textbook-crawler-D2-数据保存位置.md
> 类别：数据存储

---

### D2：数据保存位置

> 检索摘要：教材数据存 edukg/data/textbook/，按 学科-教材-学段-年级 四级目录组织，便于精确查询与扩展其他版本。

**决定**: 数据保存在 `edukg/data/textbook/` 目录下，按照 **学科-教材-学段-年级** 层级结构组织

**目录结构**:
```
edukg/data/
└── textbook/                             # 教材目录数据根目录
    └── math/                              # 学科：数学
        ├── renjiao/                       # 教材：人教版
        │   ├── primary/                   # 学段：小学
        │   │   ├── grade1/                # 年级：一年级
        │   │   │   ├── shang.json         # 上册
        │   │   │   └── xia.json           # 下册
        │   │   ├── grade2/                # 二年级
        │   │   │   ├── shang.json
        │   │   │   └── xia.json
        │   │   └── ...
        │   │   ├── grade6/                # 六年级
        │   │   │   ├── shang.json
        │   │   │   └── xia.json
        │   │   └── primary_textbook.json  # 小学数学合并文件
        │   ├── middle/                    # 学段：初中
        │   │   ├── grade7/                # 七年级
        │   │   │   ├── shang.json
        │   │   │   └── xia.json
        │   │   └── ...
        │   │   ├── grade9/                # 九年级
        │   │   │   ├── shang.json
        │   │   │   └── xia.json
        │   │   └── middle_textbook.json   # 初中数学合并文件
        │   ├── high/                      # 学段：高中
        │   │   ├── bixiu1/                # 必修第一册
        │   │   │   └── textbook.json
        │   │   ├── bixiu2/                # 必修第二册
        │   │   │   └── textbook.json
        │   │   └── ...
        │   │   └── high_textbook.json     # 高中数学合并文件
        │   ├── k12_math_textbook.ttl      # TTL 格式（与 main.ttl 兼容）
        │   └── README.md                  # 数据说明文档
        └── ...                            # 其他教材版本（预留）
```

**层级说明**:
- **学科 (subject)**: math, physics, chemistry 等
- **教材 (textbook)**: renjiao (人教版), beijingshi (北京版) 等
- **学段 (stage)**: primary (小学), middle (初中), high (高中)
- **年级 (grade)**: grade1-grade6 (小学), grade7-grade9 (初中), bixiu1-xuanxiu (高中)

**理由**:
- 四级目录结构便于按学科、教材版本、学段、年级精确查询
- 扩展性强，后续可添加其他学科和教材版本
- 与现有 `edukg/data/edukg/` 目录风格一致

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-textbook-crawler.md`（§D2）
