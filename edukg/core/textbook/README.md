# 教材数据处理模块

从原始教材 JSON 提取节点和关系数据，生成标准格式 JSON，匹配到 Neo4j 知识图谱。

## 功能概述

- **教材数据生成**：解析人教版 K12 数学教材 JSON，生成 Textbook、Chapter、Section、TextbookKP 节点
- **URI 生成**：v3.1 版本 URI，避免与 EduKG v0.1/v0.2 冲突
- **知识点过滤**：过滤非知识点标记（"数学活动"、"小结"、"整理和复习"等）
- **数据清洗**：规范 Section 标签格式
- **章节专题增强**：为 Chapter 增加 `topic` 字段（数与代数/图形与几何/统计与概率/综合与实践）
- **LLM 推断补全**：为无知识点的 Section 推断知识点（小学1-6年级 + 高中）
- **知识点属性扩展**：基于规则推断 difficulty/importance/cognitive_level/topic
- **知识点匹配**：向量检索 + 双模型投票匹配到 EduKG Concept

## 完整流程

```
Phase 1: 数据生成与处理
  ├─ generate_textbook_data.py  →  23 教材, 148 章节, 580 小节, 300 基础 KP
  ├─ clean_textbook_data.py     →  清洗不规范标签
  ├─ enhance_chapters.py        →  增加 topic 字段
  ├─ infer_textbook_kp.py       →  LLM 推断缺失 KP（小学1-6年级 + 高中）
  ├─ merge_inferred_kps.py      →  合并：300 基础 + 1440 推断 = 1740 KP
  └─ enhance_kp_attributes.py   →  增加 difficulty/importance/cognitive_level

Phase 2: 知识点匹配
  ├─ build_vector_index.py      →  为 EduKG Concept 构建向量索引
  ├─ kp_normalizer.py           →  DeepSeek 标准化：教材KP名称 → EduKG标准术语
  └─ match_textbook_kp.py       →  标准化名向量粗筛(top-20) + 加权投票(DS=0.6, GLM=0.4) → matches_kg_relations.json

Phase 3: Neo4j 导入
  ├─ import/import_textbooks.py         →  23 Textbook 节点
  ├─ import/import_chapters.py          →  148 Chapter 节点 + CONTAINS(Textbook→Chapter)
  ├─ import/import_sections.py          →  580 Section 节点 + CONTAINS(Chapter→Section)
  ├─ import/import_textbook_kps.py      →  1740 TextbookKP 节点
  ├─ import/import_in_unit_relations.py →  1740 IN_UNIT 关系
  └─ import/import_matches_kg.py        →  MATCHES_KG 关系
```

## 数据概览 (2026-04-14)

| 节点 | 数量 | 关系 | 数量 |
|------|------|------|------|
| Textbook | 23 | CONTAINS (Textbook→Chapter) | 148 |
| Chapter | 148 | CONTAINS (Chapter→Section) | 580 |
| Section | 580 | IN_UNIT (TextbookKP→Section) | 1740 |
| TextbookKP | 1740 | MATCHES_KG (TextbookKP→Concept) | ~1009 |

## 目录结构

```
edukg/core/textbook/
├── config.py                 # 配置（路径、编码映射）
├── uri_generator.py          # URI 生成器
├── filters.py                # 知识点过滤规则
├── data_generator.py         # 数据生成器
├── data_cleaner.py           # 数据清洗器
├── chapter_enhancer.py       # 章节专题增强器
├── kp_attribute_inferer.py   # 知识点属性推断器（规则匹配）
├── kp_matcher.py             # 知识点匹配器（向量检索 + LLM投票）
├── kp_normalizer.py          # 知识点标准化器（LLM预处理）
├── vector_index_manager.py   # 向量索引管理器
├── __init__.py               # 模块导出
└── README.md                 # 本文档
```

## 核心组件

### URIGenerator - URI 生成器

```python
from edukg.core.textbook import URIGenerator
generator = URIGenerator()
generator.textbook_id("人民教育出版社", "一年级", "上册")  # "renjiao-g1s"
generator.chapter_id("renjiao-g1s", 1)  # "renjiao-g1s-1"
```

### TextbookDataGenerator - 数据生成器

```python
from edukg.core.textbook import TextbookDataGenerator
generator = TextbookDataGenerator()
results = generator.generate_all()
# textbooks.json, chapters.json, sections.json, textbook_kps.json, ...
```

### ChapterEnhancer - 章节专题增强器

```python
from edukg.core.textbook import ChapterEnhancer
enhancer = ChapterEnhancer()
enhancer.assign_topic("有理数")  # "数与代数"
enhancer.assign_topic("三角形")  # "图形与几何"
```

### KPNormalizer - 知识点标准化器

使用 **DeepSeek** 将教材知识点名称转换为 EduKG 标准术语：

```python
from edukg.core.textbook import KPNormalizer
normalizer = KPNormalizer()
result = await normalizer.normalize("有理数的加法", "初中", "七年级")
# {"concepts": ["加法", "有理数"], "best_match": "加法", "confidence": 0.9, ...}
```

| 教材KP | 标准化结果(best_match) | 说明 |
|--------|----------------------|------|
| 1-5的认识 | 自然数 | "认识"类 → 核心概念 |
| 连加连减 | 加法 | 运算类 → 运算名称 |
| 秒的认识 | 秒 | 单位认识 → 单位 |
| 有理数的加法 | 加法 | 具体实例 → 上位概念 |

### KPMatcher - 知识点匹配器

```python
from edukg.core.textbook import KPMatcher
matcher = KPMatcher(use_vector_retrieval=True, candidate_top_n=20)
results = await matcher.match_all(textbook_kps, kg_concepts, resume=True)
```

**匹配流程**：DeepSeek 标准化 → 标准化名向量粗筛(top-20) → LLM 加权投票(DS=0.6, GLM=0.4)

**加权投票逻辑**：
- DeepSeek 权重 0.6，GLM 权重 0.4
- 两模型一致 → 匹配（高置信度）
- 仅 DeepSeek 认为匹配 → 匹配（中置信度）
- 仅 GLM 认为匹配 → 不匹配（DS 否决）
- 都不匹配 → 不匹配

### KPAttributeInferer - 知识点属性推断器

基于规则匹配推断属性，无需 LLM：

| 属性 | 说明 | 来源 |
|------|------|------|
| `difficulty` | 难度等级 (1-5) | 年级基础 + 关键词调整 |
| `importance` | 重要性 (核心/重要/了解) | 关键词匹配 |
| `cognitive_level` | 认知层次 (识记/理解/应用/分析) | 知识点类型匹配 |
| `topic` | 所属专题 | 继承章节 topic |

### VectorIndexManager - 向量索引管理器

预构建 EduKG 知识点向量索引，避免每次匹配重复加载模型。

```python
from edukg.core.textbook import VectorIndexManager
manager = VectorIndexManager()
manager.build_index(kg_concepts)
manager.save_index()
vectors, texts, concepts = manager.load_index()
```

索引文件：`kg_vectors.npy`, `kg_texts.json`, `kg_concepts.json`, `index_meta.json`

## 命令行工具

### Phase 1: 数据生成与处理

```bash
python edukg/scripts/kg_data/textbook/generate_textbook_data.py
python edukg/scripts/kg_data/textbook/clean_textbook_data.py --analyze --clean
python edukg/scripts/kg_data/textbook/enhance_chapters.py --analyze --enhance
python edukg/scripts/kg_data/textbook/infer_textbook_kp.py --resume
python edukg/scripts/kg_data/textbook/merge_inferred_kps.py
python edukg/scripts/kg_data/textbook/enhance_kp_attributes.py --enhance --merge
```

### Phase 2: 知识点匹配

```bash
# 1. 为 EduKG Concept 构建向量索引
python edukg/scripts/kg_data/textbook/build_vector_index.py

# 2. 执行匹配（DeepSeek 标准化 + 向量粗筛 + 加权投票）
python edukg/scripts/kg_data/textbook/match_textbook_kp.py --use-prebuilt-index --resume

# 3. 查看统计
python edukg/scripts/kg_data/textbook/match_textbook_kp.py --stats
```

匹配流程：
1. DeepSeek 标准化：教材KP名称 → EduKG 标准术语（如 "有理数的加法" → "加法"）
2. 向量粗筛：用标准化名称检索 top-20 候选
3. 加权投票：DeepSeek(0.6) + GLM(0.4)，阈值 0.5（即 DeepSeek 是裁决者）

### Phase 3: Neo4j 导入

```bash
python edukg/scripts/kg_data/import/import_textbooks.py
python edukg/scripts/kg_data/import/import_chapters.py
python edukg/scripts/kg_data/import/import_sections.py
python edukg/scripts/kg_data/import/import_textbook_kps.py
python edukg/scripts/kg_data/import/import_in_unit_relations.py
python edukg/scripts/kg_data/import/import_matches_kg.py
```

## 输出文件

位置：`edukg/data/edukg/math/5_教材目录(Textbook)/output/`

| 文件 | 说明 | 数量 |
|------|------|------|
| `textbooks.json` | 教材节点 | 23 |
| `chapters.json` | 章节节点（含 topic） | 148 |
| `sections.json` | 小节节点 | 580 |
| `textbook_kps.json` | 知识点（含属性） | 1740 |
| `contains_relations.json` | CONTAINS 关系 | 728 |
| `in_unit_relations.json` | IN_UNIT 关系 | 1740 |
| `matches_kg_relations.json` | MATCHES_KG 关系 | ~1009 |
| `textbook_kps_inferred.json` | LLM 推断的知识点 | 1440 |
| `topic_distribution.json` | 专题分布报告 | - |
| `kp_attributes_distribution.json` | 属性分布报告 | - |
| `merge_report.json` | 合并报告 | - |

### 缓存目录

| 目录 | 说明 |
|------|------|
| `llm_cache/` | LLM 投票缓存（匹配可复用） |
| `normalizer_cache/` | 知识点标准化缓存 |
| `vector_index/` | 向量索引（约 10MB） |
| `progress/` | 断点续传进度 |

## URI 设计

```
http://edukg.org/knowledge/3.1/{type}/math#{id}
```

| 节点 | ID 格式 | 示例 |
|------|--------|------|
| Textbook | `{publisher}-{grade}{semester}` | `renjiao-g1s` |
| Chapter | `{textbook_id}-{order}` | `renjiao-g1s-1` |
| Section | `{chapter_id}-{order}` | `renjiao-g1s-1-1` |
| TextbookKP | `textbook-{stage}-{seq:05d}` | `textbook-primary-00001` |

年级编码：小学 g1-g6 | 初中 g7-g9 | 高中 bixiu1-5
学期编码：上册 s | 下册 x | 高中无学期

## 知识点属性分布

### 难度分布

| 难度 | 数量 | 占比 |
|------|------|------|
| 1 | 259 | 14.9% |
| 2 | 454 | 26.1% |
| 3 | 630 | 36.2% |
| 4 | 358 | 20.6% |
| 5 | 39 | 2.2% |

### 重要性分布

| 重要性 | 数量 | 占比 |
|--------|------|------|
| 核心 | 787 | 45.2% |
| 重要 | 951 | 54.7% |
| 了解 | 2 | 0.1% |

### 认知层次分布

| 层次 | 数量 | 占比 |
|------|------|------|
| 识记 | 243 | 14.0% |
| 理解 | 933 | 53.6% |
| 应用 | 488 | 28.0% |
| 分析 | 76 | 4.4% |

### 专题分布

| 专题 | 数量 | 占比 |
|------|------|------|
| 数与代数 | 999 | 57.4% |
| 图形与几何 | 465 | 26.7% |
| 统计与概率 | 99 | 5.7% |
| 综合与实践 | 81 | 4.7% |
| 其他 | 96 | 5.5% |

## 快速开始

```bash
# 1. 环境准备
pip install sentence-transformers numpy
export HF_ENDPOINT=https://hf-mirror.com  # 如需镜像

# 2. 构建向量索引（首次下载 ~300MB 模型）
python edukg/scripts/kg_data/textbook/build_vector_index.py

# 3. 知识点标准化预处理（DeepSeek，仅首次或缓存清空后）
python edukg/core/textbook/kp_normalizer.py  # demo 模式

# 4. 执行匹配（自动调用 DeepSeek 标准化 + 向量检索 + 加权投票）
python edukg/scripts/kg_data/textbook/match_textbook_kp.py --use-prebuilt-index --resume

# 5. 查看结果
python edukg/scripts/kg_data/textbook/match_textbook_kp.py --stats
```

## 相关文档

- `edukg/data/edukg/math/5_教材目录(Textbook)/README.md` - 完整数据流和 Neo4j 导入指南
- `edukg/scripts/kg_data/import/` - Neo4j 导入脚本
