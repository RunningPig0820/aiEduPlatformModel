## Context

EDUKG 知识图谱的 main.ttl 只包含高中教材标注数据（28,438条），小学初中教材标注缺失。教师之家网站提供了完整的人教版教材目录，包含：

- 小学数学 1-6 年级（12册）
- 初中数学 7-9 年级（6册）
- 高中数学（必修+选修）
- 每册书的章节目录和知识点列表

**入口页面**: `https://www.renjiaoshe.com/renjiaoshuxue/` 包含小学、初中、高中三个学段的教材目录链接。

## Goals / Non-Goals

**Goals:**
- 从教师之家爬取人教版数学教材目录（小学+初中+高中）
- 解析章节结构和知识点列表
- 生成与 main.ttl 兼容的 TTL 格式数据
- 输出 JSON 格式便于验证和分析

**Non-Goals:**
- 不爬取课件、教案等具体内容
- 不爬取其他学科（仅数学）
- 不爬取其他版本教材（仅人教版）
- 不建立知识点前置关系（仅目录结构）

## Decisions

### 1. 爬虫文件位置

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

### 2. 数据保存位置

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

### 3. 数据格式

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

### 4. 爬虫技术选型

**决定**: 使用 Python + requests + BeautifulSoup4

**理由**:
- 教师之家是静态页面，无需 JavaScript 渲染
- BeautifulSoup4 解析 HTML 简单高效
- 与现有项目技术栈一致

### 5. URL 发现策略

**决定**: 从入口页面解析教材目录链接，分层爬取

**入口页面**:
```
https://www.renjiaoshe.com/renjiaoshuxue/
```

**爬取流程**:
1. 访问入口页面，解析小学、初中、高中三个学段的目录区块
2. 提取每个学段下的教材册数链接（如 "一年级上册"、"七年级上册" 等）
3. 依次访问每个教材页面，提取章节目录和知识点列表

**预期页面结构** (需实际验证):
```
入口页面 → 学段区块 → 教材链接 → 章节目录 → 知识点
```

**理由**:
- 入口页面集中展示所有学段教材目录，便于发现
- 动态解析链接，适应网站结构调整
- 可同时支持小学、初中、高中三个学段

### 6. 数据模型

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

## Risks / Trade-offs

| 风险 | 缓解措施 |
|-----|---------|
| 网站结构变化导致爬虫失效 | 使用多种 CSS 选择器，增加容错 |
| 爬取频率过高被封禁 | 添加请求间隔（1-2秒），设置 User-Agent |
| 知识点命名不一致 | 建立知识点标准化映射表 |
| 页面解析失败 | 记录失败 URL，支持断点续爬 |