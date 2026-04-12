# 教材数据处理模块

从原始 JSON 文件提取节点和关系数据，生成标准格式 JSON。

## 功能概述

本模块提供教材数据处理能力，核心特性：

- **教材数据生成**：解析教材 JSON 文件，生成 Textbook、Chapter、Section、TextbookKP 节点
- **URI 生成**：生成 v3.1 版本 URI，避免与 EduKG v0.1/v0.2 冲突
- **知识点过滤**：过滤非知识点标记（如"数学活动"、"小结"等）
- **数据清洗**：清理"通用"标签、规范 Section 标签格式、保留序号到 `order_in_book` 字段
- **章节专题增强**：为 Chapter 增加 `topic` 字段，标注所属专题（数与代数、图形与几何、统计与概率、综合与实践）
- **知识点属性扩展**：为 TextbookKP 增加教学属性（difficulty、importance、cognitive_level）
- **知识点匹配**：使用双模型投票匹配教材知识点到图谱知识点

## 目录结构

```
edukg/core/textbook/
├── __init__.py               # 模块导出
├── config.py                 # 配置（路径、编码映射）
├── uri_generator.py          # URI 生成器
├── filters.py                # 知识点过滤规则
├── data_generator.py         # 数据生成器
├── data_cleaner.py           # 数据清洗器
├── chapter_enhancer.py       # 章节专题增强器
├── kp_attribute_inferer.py   # 知识点属性推断器（新增）
└── kp_matcher.py             # 知识点匹配器
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
#   chapters.json: 135 条（清洗后）
#   sections.json: 549 条
#   textbook_kps.json: 352 条
#   contains_relations.json: 684 条
#   in_unit_relations.json: 352 条
```

### 3. DataCleaner - 数据清洗器

```python
from edukg.core.textbook import DataCleaner

cleaner = DataCleaner()

# 分析数据质量
chapters, sections = cleaner.load_data()
report = cleaner.analyze(chapters, sections)
# 输出重复检测报告

# 清洗 Section 标签（序号保留到 order_in_book）
cleaner.clean_sections(sections)
# "3.1-5的认识和加减法" → label="5的认识和加减法", order_in_book="3.1"

# 清洗"通用"标签章节
cleaned, deleted = cleaner.clean_chapters(chapters, delete_generic=True)
```

### 4. ChapterEnhancer - 章节专题增强器

```python
from edukg.core.textbook import ChapterEnhancer

enhancer = ChapterEnhancer()

# 分配专题（规则匹配，无 LLM）
topic = enhancer.assign_topic("有理数")
# 返回: "数与代数"

topic = enhancer.assign_topic("三角形")
# 返回: "图形与几何"

# 批量增强
enhanced = enhancer.enhance_chapters(chapters)
# 每个 Chapter 增加 topic 字段

# 专题分布
distribution = enhancer.get_topic_distribution()
# {'数与代数': 62, '图形与几何': 47, '统计与概率': 13, '综合与实践': 13}
```

### 5. KPMatcher - 知识点匹配器

```python
from edukg.core.textbook import KPMatcher

matcher = KPMatcher()

# 批量匹配
results = await matcher.match_all(textbook_kps, kg_concepts)
```

### 6. KPAttributeInferer - 知识点属性推断器

```python
from edukg.core.textbook import KPAttributeInferer

inferer = KPAttributeInferer()

# 推断单个知识点属性
attrs = inferer.infer_attributes("有理数的加法", "七年级", "数与代数")
# 返回: {
#     "difficulty": 4,
#     "difficulty_source": "grade:七年级(3) + kw:应用(+1)",
#     "importance": "重要",
#     "importance_source": "默认",
#     "cognitive_level": "应用",
#     "cognitive_level_source": "kw:运算",
#     "topic": "数与代数",
#     "topic_source": "chapter_topic:数与代数"
# }

# 批量推断
enhanced = inferer.infer_batch(kps, chapters, sections)
# 每个 TextbookKP 增加 difficulty、importance、cognitive_level、topic 字段

# 属性分布统计
report = inferer.get_stats_report()
# {'difficulty_distribution': {1: 45, 2: 12, 3: 85, 4: 125, 5: 32}, ...}
```

**属性说明**：

| 属性 | 说明 | 来源 |
|------|------|------|
| `difficulty` | 难度等级 (1-5) | 年级基础 + 关键词调整 |
| `importance` | 重要性 (核心/重要/了解) | 关键词匹配 |
| `cognitive_level` | 认知层次 (识记/理解/应用/分析) | 知识点类型匹配 |
| `topic` | 所属专题 | 继承章节 topic |

### 7. 知识点过滤

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

### clean_textbook_data.py

```bash
# 分析数据质量
python edukg/scripts/kg_data/clean_textbook_data.py --analyze

# 执行清洗
python edukg/scripts/kg_data/clean_textbook_data.py --clean

# 显示清洗统计
python edukg/scripts/kg_data/clean_textbook_data.py --stats
```

### enhance_chapters.py

```bash
# 分析专题分布
python edukg/scripts/kg_data/enhance_chapters.py --analyze

# 执行增强（更新 chapters.json）
python edukg/scripts/kg_data/enhance_chapters.py --enhance

# 显示专题统计
python edukg/scripts/kg_data/enhance_chapters.py --stats
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

### enhance_kp_attributes.py

```bash
# 分析属性分布（预览）
python edukg/scripts/kg_data/enhance_kp_attributes.py --analyze

# 执行属性增强
python edukg/scripts/kg_data/enhance_kp_attributes.py --enhance

# 强制重新生成
python edukg/scripts/kg_data/enhance_kp_attributes.py --enhance --force

# 合并到主文件
python edukg/scripts/kg_data/enhance_kp_attributes.py --merge

# 显示属性统计
python edukg/scripts/kg_data/enhance_kp_attributes.py --stats
```

## 输出文件

所有输出文件位于 `edukg/data/edukg/math/5_教材目录(Textbook)/output/`：

| 文件 | 说明 | 数量 |
|------|------|------|
| `textbooks.json` | 教材节点 | 21 |
| `chapters.json` | 章节节点（含 topic 字段） | 135 |
| `sections.json` | 小节节点（含 order_in_book 字段） | 549 |
| `textbook_kps.json` | 教材知识点节点（含属性字段） | 299 |
| `textbook_kps_enhanced.json` | 增强后的知识点（临时） | 299 |
| `contains_relations.json` | CONTAINS 关系 | 684 |
| `in_unit_relations.json` | IN_UNIT 关系 | 299 |
| `matches_kg_relations.json` | MATCHES_KG 关系 | 待生成 |
| `import_summary.json` | 导入统计摘要 | - |
| `duplicate_detection_report.json` | 数据清洗报告 | - |
| `clean_log.json` | 清洗日志 | - |
| `topic_distribution.json` | 专题分布统计 | - |
| `kp_attributes_distribution.json` | 知识点属性分布统计 | - |

## 数据清洗说明

### 清洗规则

1. **"通用"标签处理**：删除带"（通用）"、"（综合）"标签的章节（3 个）
2. **Section 序号保留**：将序号前缀保存到 `order_in_book` 字段
   - `3.1-5的认识和加减法` → `label="5的认识和加减法"`, `order_in_book="3.1"`
   - `18.1.1-平行四边形的性质` → `label="平行四边形的性质"`, `order_in_book="18.1.1"`
3. **标点清洗**：移除末尾冒号、多余空格、全角转半角

## 章节专题分类

### 专题分布

| 专题 | 数量 | 占比 |
|------|------|------|
| 数与代数 | 62 | 45.93% |
| 图形与几何 | 47 | 34.81% |
| 统计与概率 | 13 | 9.63% |
| 综合与实践 | 13 | 9.63% |

### 匹配规则

基于关键词匹配，无需 LLM：

```python
MATH_TOPICS = {
    "数与代数": ["有理数", "方程", "函数", ...],
    "图形与几何": ["三角形", "圆", "角", ...],
    "统计与概率": ["数据", "概率", "平均数", ...],
    "综合与实践": ["数学活动", "复习", ...],
}
```

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

# 测试数量：20+ 个
# 覆盖：URI 生成、过滤规则、数据生成、数据清洗、章节增强、属性推断
```

## 相关 Change

- **kg-math-complete-graph**：教材数据导入（本模块）
- **kg-math-prerequisite-inference**：前置关系推断（提供 LLM 推理能力）

## 执行顺序

按照 Phase 顺序执行：

```
Phase 1: 数据生成 → generate_textbook_data.py
Phase 2: 数据清洗 → clean_textbook_data.py --analyze → --clean
Phase 2: 章节增强 → enhance_chapters.py --analyze → --enhance
Phase 3: 属性扩展 → enhance_kp_attributes.py --analyze → --enhance → --merge ✓
Phase 4: LLM 推断 → infer_textbook_kp.py, match_textbook_kp.py（待执行）
Phase 5: 验证导入 → 人工验证后导入 Neo4j（待执行）
```

## 知识点属性分布统计

基于规则匹配推断（无 LLM）：

### 难度分布

| 难度 | 数量 | 占比 |
|------|------|------|
| 1 | 45 | 15.1% |
| 2 | 12 | 4.0% |
| 3 | 85 | 28.4% |
| 4 | 125 | 41.8% |
| 5 | 32 | 10.7% |

### 重要性分布

| 重要性 | 数量 | 占比 |
|--------|------|------|
| 核心 | 132 | 44.1% |
| 重要 | 165 | 55.2% |
| 了解 | 2 | 0.7% |

### 认知层次分布

| 认知层次 | 数量 | 占比 |
|----------|------|------|
| 识记 | 19 | 6.4% |
| 理解 | 174 | 58.2% |
| 应用 | 80 | 26.8% |
| 分析 | 26 | 8.7% |

### 专题分布（知识点）

| 专题 | 数量 | 占比 |
|------|------|------|
| 数与代数 | 144 | 48.2% |
| 图形与几何 | 130 | 43.5% |
| 统计与概率 | 25 | 8.4% |