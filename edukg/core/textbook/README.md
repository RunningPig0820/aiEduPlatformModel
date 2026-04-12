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
- **知识点匹配**：使用向量检索 + 双模型投票匹配教材知识点到图谱知识点

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
├── kp_attribute_inferer.py   # 知识点属性推断器
├── kp_matcher.py             # 知识点匹配器（含向量检索）
└── README.md                 # 本文档
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
#   textbook_kps.json: 1350 条（含 LLM 推断）
#   contains_relations.json: 684 条
#   in_unit_relations.json: 1350 条
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

**改进（采纳 DeepSeek 建议）**:

采用 **向量检索 + 双模型投票** 两阶段匹配：

```
教材知识点 → 向量检索(top-20候选) → LLM双模型投票 → 匹配结果
```

**核心改进**:

| 改进项 | 说明 |
|--------|------|
| **向量检索** | 使用 `BAAI/bge-small-zh-v1.5` 进行语义粗筛 |
| **精确匹配标准化** | 名称标准化（大小写、空格、括号）+ 同义词映射 |
| **同义词完整词匹配** | 防止过度匹配（"加法交换律"不扩展为"加法"） |
| **异常处理** | LLM调用失败继续下一个候选 |
| **未匹配记录** | 输出所有知识点，增加 `matched` 字段 |
| **进度回调修复** | 使用实际已完成数量而非循环索引 |

```python
from edukg.core.textbook import KPMatcher

# 默认使用向量检索
matcher = KPMatcher(use_vector_retrieval=True, candidate_top_n=20)

# 批量匹配
results = await matcher.match_all(textbook_kps, kg_concepts, resume=True)

# 统计信息
stats = matcher.get_stats()
# {'exact_match': 202, 'llm_match': 1148, 'unmatched': 0, 'cache_hits': 150}
```

**向量检索技术选型**:

| 组件 | 选择 | 说明 |
|------|------|------|
| Embedding 模型 | `BAAI/bge-small-zh-v1.5` | 中文小模型 SOTA，内存 2-4GB |
| 向量索引 | numpy 暴力搜索 | 图谱 ≤ 5000 条，< 10ms |
| 依赖库 | sentence-transformers | 首次需下载 300MB |

**资源占用**:

| 项目 | 内存 |
|------|------|
| 模型 | 2.5 GB |
| 向量存储 | ~10 MB |
| 其他 | < 1 GB |
| **总计** | **约 3.5 GB** |

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
# 成本估算
python edukg/scripts/kg_data/match_textbook_kp.py --dry-run

# 执行匹配（支持断点续传）
python edukg/scripts/kg_data/match_textbook_kp.py --resume

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

### infer_textbook_kp.py

```bash
# 分析缺失知识点章节
python edukg/scripts/kg_data/infer_textbook_kp.py --analyze

# 执行 LLM 推断（支持断点续传）
python edukg/scripts/kg_data/infer_textbook_kp.py --resume

# 查看进度
python edukg/scripts/kg_data/infer_textbook_kp.py --progress
```

### merge_inferred_kps.py

```bash
# 合并推断知识点
python edukg/scripts/kg_data/merge_inferred_kps.py

# 显示合并报告
python edukg/scripts/kg_data/merge_inferred_kps.py --stats
```

### enhance_inferred_kps.py

```bash
# 为推断知识点补充属性
python edukg/scripts/kg_data/enhance_inferred_kps.py

# 显示属性统计
python edukg/scripts/kg_data/enhance_inferred_kps.py --stats
```

## 输出文件

所有输出文件位于 `edukg/data/edukg/math/5_教材目录(Textbook)/output/`：

| 文件 | 说明 | 数量 |
|------|------|------|
| `textbooks.json` | 教材节点 | 21 |
| `chapters.json` | 章节节点（含 topic 字段） | 135 |
| `sections.json` | 小节节点（含 order_in_book 字段） | 549 |
| `textbook_kps.json` | 教材知识点节点（含属性字段） | 1350 |
| `contains_relations.json` | CONTAINS 关系 | 684 |
| `in_unit_relations.json` | IN_UNIT 关系 | 1350 |
| `matches_kg_relations.json` | MATCHES_KG 关系 | 待生成 |
| `textbook_kps_inferred.json` | LLM 推断的知识点 | 1052 |
| `merge_report.json` | 合并报告 | - |
| `progress/` | 断点续传进度文件 | - |
| `llm_cache/` | LLM 调用缓存 | - |

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

## LLM 推断说明

### 教学知识点推断

针对小学3-6年级、高中数据缺失的知识点，使用 LLM 推断补全：

| 模型 | 用途 |
|------|------|
| GLM-4-flash | 免费模型，第一票 |
| DeepSeek-chat | 第二票，双模型投票 |

**推断结果**:

| 项目 | 数值 |
|------|------|
| 缺失章节 | 295 个 |
| 推断知识点 | 1052 个 |
| 平均置信度 | 0.93 |
| 合并后知识点总数 | 1350 个 |

### 知识点匹配

两阶段匹配流程：

```
Phase 1: 向量检索（语义粗筛）
  - 模型: BAAI/bge-small-zh-v1.5
  - 候选: top-20

Phase 2: LLM 双模型投票
  - 模型: GLM-4-flash + DeepSeek-chat
  - 决策: 两模型达成共识则匹配
```

**同义词映射**（精确匹配增强）:

```python
SYNONYM_MAP = {
    "加法": ["加", "加法运算", "相加", "求和"],
    "百分数": ["百分比", "百分率"],
    "长方形": ["矩形", "长方形图形"],
    ...
}
```

**标准化处理**:

```python
# 名称标准化（大小写、空格、括号）
"有理数（概念）" → "有理数(概念)"
"加 法" → "加法"
```

## 测试

```bash
# 运行单元测试
pytest tests/core/textbook/ -v

# 测试数量：20+ 个
# 覆盖：URI 生成、过滤规则、数据生成、数据清洗、章节增强、属性推断、向量检索
```

## 相关 Change

- **kg-math-complete-graph**：教材数据导入（本模块）
- **kg-math-prerequisite-inference**：前置关系推断（提供 LLM 推理能力）
- **vector-index-script**：向量索引构建脚本（待实现）

## 执行顺序

按照 Phase 顺序执行：

```
Phase 1: 数据生成 → generate_textbook_data.py ✓
Phase 2: 数据清洗 → clean_textbook_data.py --analyze → --clean ✓
Phase 2: 章节增强 → enhance_chapters.py --analyze → --enhance ✓
Phase 3: 属性扩展 → enhance_kp_attributes.py --enhance → --merge ✓
Phase 4: LLM 推断 → infer_textbook_kp.py --resume ✓
Phase 4: 合并知识点 → merge_inferred_kps.py ✓
Phase 4: 补充属性 → enhance_inferred_kps.py ✓
Phase 4: 知识图谱匹配 → match_textbook_kp.py --resume（待执行）
Phase 5: 验证导入 → 人工验证后导入 Neo4j（待执行）
```

## 知识点属性分布统计

基于规则匹配推断（无 LLM）：

### 难度分布

| 难度 | 数量 | 占比 |
|------|------|------|
| 1 | 45 | 3.3% |
| 2 | 12 | 0.9% |
| 3 | 881 | 65.6% |
| 4 | 373 | 27.7% |
| 5 | 39 | 2.9% |

### 重要性分布

| 重要性 | 数量 | 占比 |
|--------|------|------|
| 核心 | 138 | 10.3% |
| 重要 | 1201 | 88.9% |
| 了解 | 11 | 0.8% |

### 认知层次分布

| 认知层次 | 数量 | 占比 |
|----------|------|------|
| 识记 | 26 | 1.9% |
| 理解 | 901 | 66.7% |
| 应用 | 391 | 29.0% |
| 分析 | 32 | 2.4% |

### 专题分布（知识点）

| 专题 | 数量 | 占比 |
|------|------|------|
| 数与代数 | 855 | 63.3% |
| 图形与几何 | 359 | 26.6% |
| 统计与概率 | 78 | 5.8% |
| 综合与实践 | 58 | 4.3% |

## 改进历史

### DeepSeek 建议（已采纳）

| 建议 | 状态 | 说明 |
|------|------|------|
| 向量检索替代 difflib | ✅ 已实现 | 语义理解更强 |
| 精确匹配标准化 | ✅ 已实现 | 名称标准化 + 同义词映射 |
| 同义词完整词匹配 | ✅ 已实现 | 防止过度匹配 |
| 异常处理 | ✅ 已实现 | LLM调用失败继续 |
| 未匹配记录 | ✅ 已实现 | 输出所有知识点 |
| 进度回调修复 | ✅ 已实现 | 使用实际已完成数量 |
| 向量索引独立脚本 | 📋 待实现 | 预构建索引，复用缓存 |