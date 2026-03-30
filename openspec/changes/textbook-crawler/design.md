## Context

EDUKG 知识图谱的 main.ttl 只包含高中教材标注数据（28,438条），小学初中教材标注缺失。教师之家网站提供了完整的人教版教材目录，包含：

- 小学数学 1-6 年级（12册）
- 初中数学 7-9 年级（6册）
- 每册书的章节目录和知识点列表

sitemap.xml 地址：`https://www.renjiaoshe.com/sitemap.xml`

## Goals / Non-Goals

**Goals:**
- 从教师之家爬取人教版数学教材目录（小学+初中）
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

**决定**: 爬虫脚本放在 `edukg/scripts/crawler/` 目录下

**文件路径**:
```
edukg/
└── scripts/
    └── crawler/
        ├── __init__.py
        ├── renjiaoshe_crawler.py    # 主爬虫脚本
        └── textbook_parser.py       # 目录解析器
```

**理由**:
- 与现有项目结构保持一致
- `scripts/` 目录用于存放工具脚本
- `crawler/` 子目录便于后续扩展其他爬虫

### 2. 数据保存位置

**决定**: 数据保存在 `edukg/data/edukg/textbook/` 目录下

**目录结构**:
```
data/edukg/
├── textbook/                           # 教材目录数据
│   ├── primary_math/                   # 小学数学
│   │   ├── grade1_shang.json           # 一年级上册
│   │   ├── grade1_xia.json             # 一年级下册
│   │   └── ...
│   ├── middle_math/                    # 初中数学
│   │   ├── grade7_shang.json           # 七年级上册
│   │   └── ...
│   ├── primary_math_textbook.json      # 小学数学合并文件
│   ├── middle_math_textbook.json       # 初中数学合并文件
│   └── k12_math_textbook.ttl           # TTL 格式（与 main.ttl 兼容）
├── k12/                                # K-12 知识点（已有）
├── edukg/                              # EDUKG 原始数据（已有）
└── ...
```

**理由**:
- 与现有 `data/edukg/` 目录结构一致
- 按学段分目录便于管理
- 合并文件便于导入 Neo4j

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

**决定**: 直接访问教材目录页面，按 ID 顺序爬取

**教材 ID 映射**:
| 学段 | 教材 ID | 册数 |
|-----|--------|-----|
| 小学数学 | 19-30 | 12册 |
| 初中数学 | 31-36 | 6册 |

**URL 模式**:
```
https://www.renjiaoshe.com/jiaocai/{id}.html
```

**理由**:
- 发现教材 ID 是连续的，无需解析 sitemap
- 直接按 ID 爬取更简单可靠
- 总共只需爬取 18 个页面

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