# 数据加工流水线 Phase0：人教版数学教材目录爬虫

> summary: 数据加工流水线
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-textbook-crawler-04-数据加工流水线.md
> 类别：操作流程

---

> 检索摘要：教材目录爬虫是全量图谱流水线的 Phase0 爬取阶段，脚本位于 edukg/scripts/textbook_data/，数据按 学科-教材-学段-年级 四级目录存 edukg/data/textbook/，同时输出 JSON 与兼容 main.ttl 的 TTL，选用 Python+requests+BeautifulSoup4 从入口页面分层爬取。

**流水线定位**：教材目录爬取是知识图谱数据加工流水线的 Phase0（爬取阶段），为后续知识点推断、匹配、导入提供小学、初中、高中的教材章节目录与知识点原始数据。本块描述该爬虫的实现方案。

**爬虫文件位置**

爬虫脚本放在 `edukg/scripts/textbook_data/` 目录下，明确标明是人教版数学：

```
edukg/
└── scripts/
    └── textbook_data/                      # 教材数据处理脚本
        ├── __init__.py
        ├── renjiaoshe_math_crawler.py      # 人教版数学教材爬虫
        └── textbook_parser.py              # 目录解析器（通用）
```

理由：与现有项目结构保持一致；`scripts/` 目录用于存放工具脚本；`textbook_data/` 子目录明确表示教材数据相关脚本；文件名 `renjiaoshe_math_crawler.py` 明确标明是人教版数学。

**数据保存位置**

数据保存在 `edukg/data/textbook/` 目录下，按 学科-教材-学段-年级 四级目录组织：

```
edukg/data/
└── textbook/                                # 教材目录数据根目录
    └── math/                                # 学科：数学
        ├── renjiao/                         # 教材：人教版
        │   ├── primary/                     # 学段：小学（grade1-grade6，每级 shang.json/xia.json）
        │   │   └── primary_textbook.json    # 小学数学合并文件
        │   ├── middle/                      # 学段：初中（grade7-grade9）
        │   │   └── middle_textbook.json     # 初中数学合并文件
        │   ├── high/                        # 学段：高中（bixiu1-xuanxiu 必修+选修）
        │   │   └── high_textbook.json       # 高中数学合并文件
        │   ├── k12_math_textbook.ttl        # TTL 格式（与 main.ttl 兼容）
        │   └── README.md                    # 数据说明文档
        └── ...                              # 其他教材版本（预留）
```

层级说明：学科 subject（math/physics/chemistry 等）、教材 textbook（renjiao 人教版、beijingshi 北京版等）、学段 stage（primary/middle/high）、年级 grade（grade1-6、grade7-9、高中 bixiu1-xuanxiu）。理由：四级目录便于按学科、教材版本、学段、年级精确查询；扩展性强，后续可添加其他学科和教材版本；与现有 `edukg/data/edukg/` 目录风格一致。

**数据格式**

同时输出 JSON 和 TTL 两种格式。JSON 用于人工查看和验证；TTL 与 EDUKG main.ttl 格式完全兼容，可直接使用 n10s 导入 Neo4j。

JSON 格式示例：

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

TTL 格式示例（与 main.ttl 兼容，用于导入 Neo4j）：

```turtle
@prefix ns1: <http://edukg.org/knowledge/3.0/ontology/data_property/main#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://edukg.org/knowledge/3.0/instance/math#textbook-primary-00001>
    a <http://edukg.org/knowledge/3.0/ontology/class/main#KnowledgePoint> ;
    rdfs:label "数数" ;
    ns1:temp '{"book": "一年级数学上册", "chapter": "准备课", "section": "数一数", "mark": "1.1"}' .
```

TTL 将章节-小节-知识点层级与教材出处信息编码进 `ns1:temp` 属性，导入后可作为知识点节点及其教材出处依据。

**爬虫技术选型**

使用 Python + requests + BeautifulSoup4。理由：教师之家是静态页面，无需 JavaScript 渲染；BeautifulSoup4 解析 HTML 简单高效；与现有项目技术栈一致。

**URL 发现策略**

从入口页面解析教材目录链接，分层爬取：
1. 访问入口页面 `https://www.renjiaoshe.com/renjiaoshuxue/`，解析小学、初中、高中三个学段的目录区块
2. 提取每个学段下的教材册数链接（如"一年级上册"、"七年级上册"等）
3. 依次访问每个教材页面，提取章节目录和知识点列表

预期页面结构（需实际验证）：入口页面 → 学段区块 → 教材链接 → 章节目录 → 知识点。理由：入口页面集中展示所有学段教材目录，便于发现；动态解析链接，适应网站结构调整；可同时支持小学、初中、高中三个学段。

**数据模型**

沿用 build_textbook_data.py 定义的数据结构：

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
