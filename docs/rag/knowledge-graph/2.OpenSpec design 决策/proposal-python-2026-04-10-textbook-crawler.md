## Why

EDUKG 知识图谱只包含高中教材标注数据（main.ttl），缺失小学和初中的教材-知识点映射。需要从外部数据源获取小学初中教材目录，建立完整的 K-12 教材-知识点关联，支持按学段、年级查询知识点。

教师之家（renjiaoshe.com）提供了完整的人教版教材目录，包含章节名称和知识点列表，是获取教材目录的优质数据源。

## What Changes

- 新增爬虫脚本，从教师之家网站爬取人教版数学教材目录
- 从入口页面 `https://www.renjiaoshe.com/renjiaoshuxue/` 解析小学、初中、高中教材链接
- 提取章节结构和知识点列表
- 生成与 main.ttl 兼容的 TTL 格式数据
- 输出 JSON 格式便于后续处理和分析

## Capabilities

### New Capabilities

- `textbook-crawler`: 爬取教师之家人教版教材目录的能力
  - 支持从入口页面解析学段教材链接
  - 支持提取章节目录和知识点列表
  - 支持小学、初中、高中全学段
  - 输出 TTL 和 JSON 两种格式

### Modified Capabilities

- `knowledge-graph-data`: 扩展知识图谱数据，新增小学初中教材标注

## Impact

- **新增文件**:
  - `scripts/textbook_data/renjiaoshe_math_crawler.py` - 人教版数学教材爬虫脚本
  - `data/textbook/math/renjiao/primary/` - 小学数学教材目录
  - `data/textbook/math/renjiao/middle/` - 初中数学教材目录
  - `data/textbook/math/renjiao/high/` - 高中数学教材目录
  - `data/textbook/math/renjiao/k12_math_textbook.ttl` - K12 数学教材 TTL
- **依赖**: requests, beautifulsoup4, lxml