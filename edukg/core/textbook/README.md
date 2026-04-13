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
- **知识点标准化**：LLM 推断教材知识点名称为标准数学概念，提高匹配率
- **知识点匹配**：向量检索 + 双模型投票匹配教材知识点到图谱知识点
- **向量索引预构建**：支持预构建向量索引，避免每次匹配重复加载模型

## 知识点匹配完整流程

采用**三阶段匹配**策略，解决教材名称与 EduKG 概念的语义差距：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          知识点匹配完整流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Phase 1: 标准化预处理                                                        │
│  ├─ 输入: 教材知识点名称（1350条）                                             │
│  ├─ 操作: LLM 推断标准数学概念名称                                             │
│  ├─ 输出: normalized_kps_complete.json                                       │
│  │         {"original": "1-5的认识", "best_match": "自然数", ...}            │
│  ├─ 缓存: normalizer_cache/（断点续传）                                       │
│  └─ 效果: "秒的认识" → "秒"，直接匹配 EduKG ✓                                  │
│                                                                              │
│  Phase 2: 向量检索                                                            │
│  ├─ 输入: best_match 字段（标准化概念名）                                      │
│  ├─ 操作: 用 "自然数" 向量检索 EduKG（bge-small-zh-v1.5）                      │
│  ├─ 输出: top-20 候选概念（含相似度分数）                                      │
│  └─ 缓存: vector_index/（预构建索引）                                         │
│                                                                              │
│  Phase 3: LLM双模型投票                                                        │
│  ├─ 输入: 教材知识点 + top-20候选                                              │
│  ├─ 操作: GLM-4-flash + DeepSeek 双模型投票                                   │
│  ├─ 输出: 是否匹配 + 置信度                                                   │
│  ├─ 缓存: llm_cache/（断点续传）                                              │
│  └─ 优化: 早停 + 阈值过滤 + 调用限制（50x提速）                                 │
│                                                                              │
│  Phase 4: 输出结果                                                             │
│  ├─ 输出: matches_kg_relations.json                                          │
│  │         {"textbook_kp": "...", "kg_kp": "自然数", "matched": true}        │
│  └─ 用于: Neo4j MATCHES_KG 关系导入                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**流程对比**：

| 方案 | 匹配方式 | 匹配率 |
|------|---------|-------|
| **旧流程** | 教材名称 → 向量检索 → LLM投票 | 17%（小学知识点无法匹配）|
| **新流程** | 教材名称 → 标准化 → 向量检索 → LLM投票 | 预计 60%+ |

**效果示例**：

```
旧流程：
  "1-5的认识" → 向量检索 → 无匹配（语义差距大）

新流程：
  "1-5的认识" → 标准化 → "自然数" → 向量检索 → 自然数 (0.711) ✓
```

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
├── kp_normalizer.py          # 知识点标准化器（LLM预处理）
├── vector_index_manager.py   # 向量索引管理器
├── README.md                 # 本文档
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

采用 **标准化 + 向量检索 + 双模型投票** 三阶段匹配：

```
教材知识点 → 标准化(best_match) → 向量检索(top-20候选) → LLM双模型投票 → 匹配结果
```

**核心改进（采纳 DeepSeek 建议）**:

| 改进项 | 说明 | 优先级 |
|--------|------|--------|
| **标准化集成** | 自动使用 `best_match` 进行向量检索，提高命中率 | 高 |
| **向量检索** | 使用 `BAAI/bge-small-zh-v1.5` 进行语义粗筛 | 高 |
| **统计并发安全** | 返回 (result, match_type) 元组，主流程汇总（方案 C） | 🔴 高 |
| **进度立即持久化** | 每个任务完成后立即保存，避免崩溃丢失 | 🟡 中 |
| **等待逻辑简化** | 直接从检查点读取结果，避免死锁风险 | 🟡 中 |
| **缓存文件锁保护** | `_get_cached_result` / `_save_cached_result` 加锁 | 🟡 中 |
| **精确匹配标准化** | 名称标准化（大小写、空格、括号）+ 同义词映射 | 低 |
| **同义词完整词匹配** | 防止过度匹配（"加法交换律"不扩展为"加法"） | 低 |
| **异常处理** | LLM调用失败继续下一个候选 | 低 |
| **未匹配记录** | 输出所有知识点，增加 `matched` 字段 | 低 |
| **并发处理** | Semaphore + asyncio.Lock 保护（可选） | 低 |

**标准化效果示例**:

```
旧流程（无标准化）:
  "1-5的认识" → 向量检索 → 无匹配（语义差距大）

新流程（自动标准化）:
  "1-5的认识" → 标准化(best_match="自然数") → 向量检索 → "自然数"(0.711) ✓
  "连加连减" → 标准化(best_match="加法") → 向量检索 → "加法"(0.65) ✓
```

```python
from edukg.core.textbook import KPMatcher

# 默认使用向量检索 + 自动标准化
matcher = KPMatcher(use_vector_retrieval=True, candidate_top_n=20)

# 获取标准化名称（手动查询）
best_match = matcher.get_best_match("1-5的认识", "小学", "一年级")
# 返回: "自然数"

# 批量匹配（自动使用标准化名称）
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

### 7. VectorIndexManager - 向量索引管理器

**用途**：预构建 EduKG 知识点向量索引，避免每次匹配时重新加载模型和计算向量。

```python
from edukg.core.textbook import VectorIndexManager

manager = VectorIndexManager()

# 构建向量索引（从 Neo4j 加载知识点）
manager.build_index(kg_concepts)

# 保存索引到文件
manager.save_index()
# 输出:
#   kg_vectors.npy: 向量矩阵 (N, 512)
#   kg_texts.json: 知识点文本列表
#   kg_concepts.json: 知识点元数据
#   index_meta.json: 索引元数据（含 checksum）

# 加载预构建索引
vectors, texts, concepts = manager.load_index()

# 检查索引是否过期（checksum 校验）
is_valid = manager.is_index_valid(current_concepts)
```

**索引文件说明**：

| 文件 | 说明 | 大小 |
|------|------|------|
| `kg_vectors.npy` | 向量矩阵 (10250, 512) | ~20 MB |
| `kg_texts.json` | 知识点文本列表 | ~1.4 MB |
| `kg_concepts.json` | 知识点元数据 (uri, label) | ~2.5 MB |
| `index_meta.json` | 元数据（模型、checksum） | ~200 B |

### 8. KPNormalizer - 知识点标准化器

**用途**：将教材知识点名称推断为标准数学概念名称，提高与 EduKG 的匹配率。

**问题背景**：
- 教材知识点命名贴近教学场景：如 "1-5的认识"、"连加连减"、"秒的认识"
- EduKG 知识点是抽象数学概念：如 "自然数"、"加减混合运算"、"秒"
- 直接向量匹配效果差：教材名称与概念名称语义差距大

**解决方案**：
```
教材知识点 → LLM推断(标准名称) → 向量检索 → LLM投票 → 匹配结果
```

```python
from edukg.core.textbook import KPNormalizer

normalizer = KPNormalizer()

# 标准化单个知识点
result = await normalizer.normalize("1-5的认识", "小学", "一年级")
# 返回: {
#     "original": "1-5的认识",
#     "concepts": ["自然数", "数", "整数"],
#     "best_match": "自然数",  # 用于向量检索
#     "confidence": 0.9,
#     "reason": "一年级数的认识课程",
#     "from_cache": False
# }

# 批量标准化（并发处理）
results = await normalizer.normalize_batch(kps, max_concurrent=5)
```

**效果验证**：

| 教材知识点 | LLM推断(best_match) | EduKG匹配结果 |
|-----------|--------------------|---------------|
| "1-5的认识" | 自然数 | 自然数 (0.711) ✓ |
| "连加连减" | 加法 | 减法 (0.655) ✓ |
| "秒的认识" | 秒 | 秒 (0.830) ✓ |
| "平行四边形的性质" | 平行四边形 | 平行四边形 (0.853) ✓ |

**数据位置**：

```
output/
├── normalizer_cache/           # 标准化缓存（断点续传）
│   ├── abc123.json             # 单条标准化结果
│   └── ...                     # 1255 个文件
│
└── normalized_kps_complete.json # 汇总结果（完整）
                                # 用于后续向量检索
```

**提示词管理**：
- 提示词文件：`edukg/core/llm_inference/prompts/kp_normalizer.txt`
- 缓存目录：`output/normalizer_cache/`
- 支持断点续传：缓存标准化结果，避免重复 API 调用

**并发安全**（采纳 DeepSeek 建议）：
- `asyncio.Lock` 保护并发访问
- 原子写入缓存文件（临时文件 + rename）
- 批量并发处理（`gather` + `Semaphore`）
- 超时机制（等待其他协程最多30秒）

**标准化统计**：

| 项目 | 值 |
|------|-----|
| 唯一知识点 | 1237 个 |
| 标准化结果 | 1255 条 |
| 高置信度 (≥0.9) | 744 (59.3%) |
| 中等置信度 (0.7-0.9) | 511 (40.7%) |
| 低置信度 (<0.7) | 0 (0%) |

### 9. 知识点过滤

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

# 使用预构建索引（推荐，加速启动）
python edukg/scripts/kg_data/match_textbook_kp.py --use-prebuilt-index --resume

# 强制重建索引后匹配
python edukg/scripts/kg_data/match_textbook_kp.py --force-build-index --resume

# 禁用向量检索（回退到 difflib）
python edukg/scripts/kg_data/match_textbook_kp.py --no-vector-retrieval --resume

# 调整粗筛候选数量
python edukg/scripts/kg_data/match_textbook_kp.py --candidate-top-n 30 --resume

# 显示已有统计
python edukg/scripts/kg_data/match_textbook_kp.py --stats
```

**CLI 参数说明**：

| 参数 | 说明 |
|------|------|
| `--use-prebuilt-index` | 使用预构建向量索引（启动更快） |
| `--force-build-index` | 强制重建索引后再匹配 |
| `--no-vector-retrieval` | 禁用向量检索，使用 difflib |
| `--candidate-top-n N` | 粗筛候选数量（默认 20） |
| `--index-path PATH` | 预构建索引目录路径 |

### normalize_textbook_kp.py

**用途**：批量标准化教材知识点名称，生成标准化结果供后续匹配使用。

```bash
# 显示统计
python edukg/scripts/kg_data/normalize_textbook_kp.py --stats

# 执行标准化（断点续传）
python edukg/scripts/kg_data/normalize_textbook_kp.py --resume

# 指定并发数（默认5）
python edukg/scripts/kg_data/normalize_textbook_kp.py --resume --concurrency 10
```

**CLI 参数说明**：

| 参数 | 说明 |
|------|------|
| `--resume` | 断点续传，复用 normalizer_cache |
| `--stats` | 显示标准化统计 |
| `--concurrency N` | 并发数（默认 5） |

**输出文件**：

| 文件 | 说明 |
|------|------|
| `normalizer_cache/*.json` | 单条标准化缓存（断点续传） |
| `normalized_kps_complete.json` | 汇总结果（用于向量检索） |

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

### build_vector_index.py

**用途**：构建 EduKG 知识点向量索引，加速后续匹配流程。

```bash
# 构建索引（首次会下载 300MB 模型）
python edukg/scripts/kg_data/build_vector_index.py

# 查看索引状态
python edukg/scripts/kg_data/build_vector_index.py --status

# 强制重建索引
python edukg/scripts/kg_data/build_vector_index.py --force
```

**注意事项**：
- 首次运行需下载 `BAAI/bge-small-zh-v1.5` 模型（~300MB）
- 若网络不通 Hugging Face，使用镜像：`export HF_ENDPOINT=https://hf-mirror.com`
- 索引输出目录：`edukg/data/edukg/math/5_教材目录(Textbook)/output/vector_index/`

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
| `matches_kg_relations.json` | MATCHES_KG 关系 | 1350（匹配1042 + 未匹配308） |
| `unmatched_kps.json` | 未匹配知识点详情（供人工审核） | 308 |
| `unmatched_analysis.json` | 未匹配原因分析报告 | - |
| `topic_correction_report.json` | Topic修正报告 | 144修正 |
| `textbook_kps_inferred.json` | LLM 推断的知识点 | 1052 |
| `merge_report.json` | 合并报告 | - |
| **标准化相关** | | |
| `normalizer_cache/` | 知识点标准化缓存（断点续传） | 1255 |
| `normalized_kps_complete.json` | 标准化汇总结果（用于向量检索） | 1255 |
| **匹配相关** | | |
| `vector_index/` | 向量索引（预构建） | 4文件 |
| `llm_cache/` | LLM投票缓存（断点续传） | 动态 |
| `progress/` | 断点续传进度文件 | - |

**标准化数据结构**：

```json
{
  "original": "1-5的认识",
  "best_match": "自然数",
  "concepts": ["自然数", "数", "整数"],
  "confidence": 0.9,
  "reason": "一年级数的认识课程",
  "stage": "小学",
  "grade": "一年级",
  "from_cache": false
}
```

**后续流程使用**：

```
normalized_kps_complete.json → best_match 字段 → 向量检索 → LLM投票 → 匹配结果
```

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
- **vector-index-script**：向量索引构建脚本（✅ 已实现）

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
Phase 4: 知识点标准化 → normalize_textbook_kp.py --resume ✓
Phase 4: 构建向量索引 → build_vector_index.py ✓
Phase 4: 知识图谱匹配 → match_textbook_kp.py --use-prebuilt-index --resume ✓ (77.2%匹配率)
Phase 4: 未匹配导出 → unmatched_kps.json (308条) ✓
Phase 4: Topic修正 → 基于Class类型修正144个 ✓
Phase 5: 验证导入 → 人工验证后导入 Neo4j（待执行）
```

**关键步骤说明**：

| 步骤 | 说明 | 耗时 |
|------|------|------|
| 知识点标准化 | LLM推断标准名称，5并发 | ~8分钟（1255条） |
| 构建向量索引 | 首次需下载模型，后续复用 | ~30秒（首次） |
| 知识图谱匹配 | 使用标准化结果 + 预构建索引 | ~1-2小时 |

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
| 数与代数 | 891 | 66.0% |
| 图形与几何 | 315 | 23.3% |
| 统计与概率 | 94 | 7.0% |
| 综合与实践 | 50 | 3.7% |

**注**: Topic 分布已基于 EduKG Concept Class 类型修正（2026-04-13）

## 知识点匹配优化策略

### 问题背景

原始匹配逻辑效率低下：
- 遍历全部 20 个候选，每个候选调用 2 次 LLM（GLM + DeepSeek）
- 最坏情况：40 次 API 调用/知识点
- 实测：3.5 小时仅完成 290 个知识点（21.5%）

### 优化策略

采用 **早停 + 阈值过滤 + 调用限制** 三重优化：

```python
# kp_matcher.py 核心优化参数
LLM_CANDIDATE_LIMIT = 3      # 只对前 N 个候选做 LLM 投票
SIMILARITY_THRESHOLD = 0.5   # 相似度阈值，低于此值跳过
```

**优化后匹配流程**：

```
向量检索 → top-20 候选（含相似度分数）

for candidate in top-20:
    ① 相似度阈值检查
       if candidate.similarity < 0.5:
           continue  # 直接跳过，不调用 LLM

    ② LLM 调用上限检查
       if llm_calls >= 3:
           break  # 停止遍历，记录最佳候选待审核

    ③ LLM 双模型投票
       result = llm_vote(candidate)
       if result.matched:
           break  # 早停：匹配成功立即退出

    ④ 记录最佳未匹配候选
       best_unmatched = candidate  # 供人工审核
```

### 效果对比

| 场景 | 原始逻辑 | 优化后 | 提升 |
|------|----------|--------|------|
| 第1个候选匹配成功 | 40 次 API | 2 次 API | **20x** |
| 前3个候选都不匹配 | 40 次 API | 6 次 API | **6.7x** |
| 所有候选相似度都低 | 40 次 API | 0 次 API | **∞** |

**实测效果**：
- 原始：3.5 小时 → 290 知识点（0.14 知识点/分钟）
- 优化：4 秒 → 170 知识点（命中缓存）+ ~7 知识点/分钟（新知识点）
- **整体提速约 50x**

### LLM 缓存机制

每次 LLM 双模型投票结果自动缓存到本地文件：

```
llm_cache/
├── textbook_kp1__kg_kp1.json   # 缓存文件
├── textbook_kp1__kg_kp2.json
└── ...
```

**缓存内容**：
```json
{
    "decision": true/false,
    "reason": "匹配理由",
    "voters": {
        "glm": {"vote": true, "reason": "..."},
        "deepseek": {"vote": true, "reason": "..."}
    }
}
```

**缓存复用逻辑**：
- cache_key = `textbook_kp_label + kg_kp_label`
- 检查 `llm_cache/{cache_key}.json` 是否存在
- 存在 → 直接读取结果，跳过 API 调用
- 不存在 → 调用 GLM + DeepSeek，保存结果

### 未匹配知识点处理

优化后不再穷尽遍历所有候选，而是：

1. **记录最佳候选**：保存相似度最高但未匹配成功的候选
2. **标记待审核**：`method: "candidate_review"`，`matched: false`
3. **后续人工处理**：可批量审核这些待定知识点

```json
{
    "textbook_kp": "多项式乘多项式",
    "matched": false,
    "method": "candidate_review",
    "reason": "最佳候选待审核: 多项式乘法 (相似度 0.82)",
    "best_candidate": {
        "uri": "...",
        "label": "多项式乘法",
        "similarity": 0.82
    }
}
```

---

## 知识点匹配结果（2026-04-13）

### 匹配统计

| 类型 | 数量 | 占比 |
|------|------|------|
| 总知识点 | 1350 | 100% |
| 精确匹配 | 1025 | 75.9% |
| LLM 匹配 | 17 | 1.3% |
| 未匹配 | 308 | 22.8% |
| **匹配率** | **77.2%** | - |

### 未匹配原因分析

| 分类 | 数量 | 说明 |
|------|------|------|
| 颗粒度差异 | 297 | 教材知识点更细粒度，有候选但LLM投票不通过 |
| 图谱缺失 | 11 | EduKG 中无对应知识点候选 |

**未匹配样例**：
- 颗粒度差异："分数除法意义"、"三角形全等判定方法"
- 图谱缺失："田忌赛马故事背景"、"莫比乌斯带定义"、"24时计时法概念"

### Topic修正结果

基于匹配的 EduKG Concept 的 Class 类型修正知识点 topic：

| Class 类型 | Topic |
|-----------|-------|
| 代数概念、数、数学运算、函数 | 数与代数 |
| 几何概念、几何图形、面、线、角 | 图形与几何 |
| 统计概念、概率概念 | 统计与概率 |
| 逻辑概念、命题、数学问题 | 综合与实践 |

**修正效果**：144 个知识点 topic 被修正

### 后续处理：人工审核系统

未匹配的 308 个知识点已导出到 `unmatched_kps.json`，后续将导入 MySQL 进行人工审核。

**审核系统设计**（见 `kp-match-review-system` change）：
- MySQL 表：`textbook_kp_match_review`
- 审核流程：确认匹配 / 选择其他候选 / 拒绝匹配 / 创建新知识点
- 最终导入：审核通过后导入 Neo4j MATCHES_KG 关系

---

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
| 向量索引独立脚本 | ✅ 已实现 | `build_vector_index.py` |
| 索引过期检测 | ✅ 已实现 | checksum 校验 |
| 早停优化 | ✅ 已实现 | 匹配成功立即退出 |
| LLM 调用限制 | ✅ 已实现 | 只对 top-3 候选投票 |
| 相似度阈值过滤 | ✅ 已实现 | 低相似度候选跳过 |
| 最佳候选记录 | ✅ 已实现 | 未匹配知识点记录最佳候选 |
| 知识点标准化预处理 | ✅ 已实现 | `kp_normalizer.py` 提升匹配率 |

---

## 快速开始指南

### 1. 环境准备

```bash
# 安装依赖
pip install sentence-transformers numpy

# 设置 Hugging Face 镜像（若网络不通）
export HF_ENDPOINT=https://hf-mirror.com
```

### 2. 构建向量索引

```bash
# 构建索引（首次需下载 300MB 模型）
python edukg/scripts/kg_data/build_vector_index.py

# 查看索引状态
python edukg/scripts/kg_data/build_vector_index.py --status
```

### 3. 执行知识图谱匹配

```bash
# 使用预构建索引（推荐）
python edukg/scripts/kg_data/match_textbook_kp.py --use-prebuilt-index --resume
```

### 4. 查看匹配结果

```bash
# 显示匹配统计
python edukg/scripts/kg_data/match_textbook_kp.py --stats

# 结果文件位置
# edukg/data/edukg/math/5_教材目录(Textbook)/output/matches_kg_relations.json
```