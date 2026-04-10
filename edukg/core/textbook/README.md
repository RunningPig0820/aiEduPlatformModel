# 教材数据处理模块

从原始 JSON 文件提取节点和关系数据，生成标准格式 JSON。

## 功能概述

本模块提供教材数据处理能力，核心特性：

- **教材数据生成**：解析教材 JSON 文件，生成 Textbook、Chapter、Section、TextbookKP 节点
- **URI 生成**：生成 v3.1 版本 URI，避免与 EduKG v0.1/v0.2 冲突
- **知识点过滤**：过滤非知识点标记（如"数学活动"、"小结"等）
- **知识点匹配**：使用双模型投票匹配教材知识点到图谱知识点

## 目录结构

```
edukg/core/textbook/
├── __init__.py          # 模块导出
├── config.py            # 配置（路径、编码映射）
├── uri_generator.py     # URI 生成器
├── filters.py           # 知识点过滤规则
├── data_generator.py    # 数据生成器
└── kp_matcher.py        # 知识点匹配器
```

## 核心组件

### 1. URIGenerator - URI 生成器

```python
from edukg.core.textbook import URIGenerator

generator = URIGenerator()

# 生成教材 ID
tb_id = generator.textbook_id("人民教育出版社", "一年级", "上册")
# 返回: "renjiao-g1s"

# 生成章节 ID
ch_id = generator.chapter_id(tb_id, 1)
# 返回: "renjiao-g1s-1"

# 生成 URI
uri = generator.textbook_uri(tb_id)
# 返回: "http://edukg.org/knowledge/3.1/textbook/math#renjiao-g1s"
```

### 2. TextbookDataGenerator - 数据生成器

```python
from edukg.core.textbook import TextbookDataGenerator

generator = TextbookDataGenerator()

# 生成所有数据
results = generator.generate_all()
# 输出:
#   textbooks.json: 21 条
#   chapters.json: 138 条
#   sections.json: 549 条
#   textbook_kps.json: 352 条
#   contains_relations.json: 687 条
#   in_unit_relations.json: 352 条
```

### 3. KPMatcher - 知识点匹配器

```python
from edukg.core.textbook import KPMatcher

matcher = KPMatcher()

# 批量匹配
results = await matcher.match_all(textbook_kps, kg_concepts)
```

### 4. 知识点过滤

```python
from edukg.core.textbook import is_valid_knowledge_point, filter_knowledge_points

# 判断是否为有效知识点
is_valid_knowledge_point("加法")  # True
is_valid_knowledge_point("数学活动")  # False
is_valid_knowledge_point("小结")  # False

# 批量过滤
kps = ["加法", "减法", "数学活动", "小结"]
filtered = filter_knowledge_points(kps)
# 返回: ["加法", "减法"]
```

## 配置说明

`config.py` 中的主要配置：

| 配置项 | 说明 |
|--------|------|
| `URI_VERSION` | URI 版本号（v3.1） |
| `DATA_DIR` | 数据目录路径 |
| `OUTPUT_DIR` | 输出目录路径 |
| `GRADE_ENCODING` | 年级编码映射 |
| `SEMESTER_ENCODING` | 学期编码映射 |

## 命令行工具

### generate_textbook_data.py

```bash
# 生成数据
python edukg/scripts/kg_data/generate_textbook_data.py

# 仅显示统计
python edukg/scripts/kg_data/generate_textbook_data.py --dry-run

# 显示已有统计
python edukg/scripts/kg_data/generate_textbook_data.py --stats
```

### match_textbook_kp.py

```bash
# 执行匹配
python edukg/scripts/kg_data/match_textbook_kp.py

# 估算成本
python edukg/scripts/kg_data/match_textbook_kp.py --dry-run

# 显示已有统计
python edukg/scripts/kg_data/match_textbook_kp.py --stats
```

## 输出文件

所有输出文件位于 `edukg/data/edukg/math/5_教材目录/output/`：

| 文件 | 说明 | 数量 |
|------|------|------|
| `textbooks.json` | 教材节点 | 21 |
| `chapters.json` | 章节节点 | 138 |
| `sections.json` | 小节节点 | 549 |
| `textbook_kps.json` | 教材知识点节点 | 352 |
| `contains_relations.json` | CONTAINS 关系 | 687 |
| `in_unit_relations.json` | IN_UNIT 关系 | 352 |
| `matches_kg_relations.json` | MATCHES_KG 关系 | 待生成 |
| `import_summary.json` | 导入统计摘要 | - |

## URI 设计

### URI 版本

- **v3.1**：教材数据（本模块）
- v0.1：EduKG 原始数据
- v0.2：小学新增数据

### URI 格式

| 节点类型 | URI 格式 | 示例 |
|---------|---------|------|
| Textbook | `{prefix}/textbook/math#{id}` | `renjiao-g1s` |
| Chapter | `{prefix}/chapter/math#{id}` | `renjiao-g1s-1` |
| Section | `{prefix}/section/math#{id}` | `renjiao-g1s-1-1` |
| TextbookKP | `{prefix}/instance/math#textbook-{stage}-{seq}` | `textbook-primary-00001` |

### ID 编码

| 年级 | 编码 | 学期 | 编码 |
|------|------|------|------|
| 一年级 | g1 | 上册 | s |
| 七年级 | g7 | 下册 | x |
| 必修第一册 | bixiu1 | - | - |

## 测试

```bash
# 运行单元测试
pytest tests/core/textbook/ -v

# 测试数量：20 个
# 覆盖：URI 生成、过滤规则、数据生成
```

## 相关 Change

- **kg-math-complete-graph**：教材数据导入（本模块）
- **kg-math-prerequisite-inference**：前置关系推断（提供 LLM 推理能力）