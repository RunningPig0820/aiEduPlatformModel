## Context

### 项目背景

知识图谱数据处理项目已完成数学学科的核心数据导入：
- Neo4j schema 初始化（节点标签、唯一性约束）
- EduKG 数据导入（Class 39, Concept 1,295, Statement 2,932）
- 关系导入（RELATED_TO 10,183, SUB_CLASS_OF 38, PART_OF 298, BELONGS_TO 619）
- 教材数据生成（Textbook 21, Chapter 138, Section 549, TextbookKP 299）

### 当前问题

**1. 教学知识点数据不完整**：

| 学段 | 知识点数 | 问题 |
|------|---------|------|
| 小学1-2年级 | 47 | 部分有知识点 |
| 小学3-6年级 | **0** | **knowledge_points 全空** |
| 初中7-9年级 | 252 | 较完整 |
| 高中必修 | **0** | **仅有综合测试标记** |

**2. 教材知识点与知识图谱割裂**：

```
教材数据 (本地 JSON)              知识点数据 (Neo4j EduKG)
┌─────────────────────┐          ┌─────────────────────┐
│ 学段: 初中          │          │ uri: instance#1047  │
│ 年级: 七年级        │    ??    │ label: 余弦定理     │
│ 教材: 上册          │ ───────▶ │ type: 数学定理      │
│ 章节: 有理数        │          │ source: EduKG       │
│ 知识点: 正数和负数  │          │ relatedTo: 三角形   │
└─────────────────────┘          └─────────────────────┘
```

**名称不一致问题**：
- 教材：`正数和负数的概念` vs EduKG：`正数的定义`
- 精确匹配率仅 6% (24/346)

### 设计约束

1. **输出 JSON 文件**：不直接导入 Neo4j，由人工验证后手动导入
2. **核心代码放入 edukg/core**：scripts 只做命令行入口
3. **复用双模型推理**：依赖 kg-math-prerequisite-inference 的投票机制
4. **所有 LLM 任务支持断点续传**：使用 llmTaskLock 模块

## Goals / Non-Goals

**Goals:**
1. 解析教材 JSON 数据，输出标准格式 JSON
2. LLM 推断补全缺失的教学知识点（小学3-6年级、初中、高中）
3. 使用双模型推理匹配教材知识点到 EduKG Concept
4. 输出所有关系数据（CONTAINS, IN_UNIT, MATCHES_KG）
5. 数据清洗：清理"通用"标签、规范 Section 标签
6. 知识点属性扩展：难度、重要性、认知维度、专题分类

**Non-Goals:**
1. 不直接导入 Neo4j（人工验证后手动导入）
2. 不处理其他学科（仅数学）
3. 不实现新的 LLM 推理机制（复用 kg-math-prerequisite-inference）
4. 不修改已有的 EduKG 节点数据
5. 不实现前置关系推断（由 kg-math-prerequisite-inference 负责）
6. 不实现多版本教材对比（未来迭代）

## Decisions

### D1: 目录结构设计

**核心代码放入 `edukg/core/textbook/`**：

```
edukg/core/textbook/
├── __init__.py
├── config.py                # 配置（路径、URI版本等）
├── uri_generator.py         # URI 生成器
├── filters.py               # 知识点过滤规则
├── data_generator.py        # 数据生成器
├── kp_matcher.py            # 知识点匹配器
└── README.md                # 模块文档
```

**LLM 推断复用 `edukg/core/llm_inference/`**：

```
edukg/core/llm_inference/
├── dual_model_voter.py      # 双模型投票
├── textbook_kp_inferer.py   # 教学知识点推断（新增）
├── prompt_templates.py      # 提示词加载
└── prompts/
    ├── textbook_kg.txt      # 教学知识点推断提示词
    └── kp_match.txt         # 知识点匹配提示词
```

**scripts 只做命令行入口**：

```
edukg/scripts/kg_data/
├── generate_textbook_data.py   # 数据生成入口
├── infer_textbook_kp.py        # 教学知识点推断入口（新增）
└── match_textbook_kp.py        # 知识点匹配入口
```

### D2: 两阶段流程设计

**第一阶段：数据生成（无 LLM）**
- 输入：教材原始 JSON
- 输出：标准化 JSON 文件
- 过滤非知识点标记

**第二阶段：LLM 增强**
- 输入：第一阶段输出 + Neo4j EduKG 数据
- 输出：推断的教学知识点 + 匹配关系
- 支持断点续传

### D3: 教学知识点推断设计

**问题**: 小学3-6年级、高中数据源 `knowledge_points` 为空

**解决方案**: LLM 推断补全

```python
# 调用 llm_inference.TextbookKPInferer
inferer = TextbookKPInferer(voter)

result = await inferer.infer_section(
    stage="小学",
    grade="三年级",
    semester="上册",
    chapter_name="时、分、秒",
    section_name="秒的认识",
    existing_kps=[]  # 为空则完全推断
)

# 输出
{
    "knowledge_points": ["秒的概念", "秒与分的关系", "时间的读写"],
    "confidence": 0.85,
    "notes": "依据人教版三年级上册时、分、秒单元内容"
}
```

**提示词 (textbook_kg.txt)**：

```
输入：
- 学段、年级、册次
- 章节名称、小节名称
- 已有知识点（如为空则需推断）

输出：
{
    "knowledge_points": [...],
    "confidence": 0.0-1.0,
    "notes": "推断依据"
}
```

### D4: 知识图谱匹配设计 (MATCHES_KG)

**目标**: 将 TextbookKP 匹配到 EduKG Concept

#### D4.1 匹配流程

```python
from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt

voter = DualModelVoter()

# 匹配教材知识点到知识图谱
prompt = format_kp_match_prompt(
    textbook_kp_name="正数和负数的概念",
    textbook_kp_description="大于0的数叫正数，小于0的数叫负数",
    kg_kp_name="正数",
    kg_kp_description="数学概念..."
)

result = await voter.vote(prompt)
if result['consensus'] and result['result']['is_match']:
    # 创建 MATCHES_KG 关系
```

**匹配阈值**：
- ≥ 0.9：MATCHES_KG
- 0.7 - 0.9：MATCHES_KG_CANDIDATE
- < 0.7：不匹配

#### D4.2 粗筛机制设计（采纳 DeepSeek 建议）

**问题**: 原方案遍历所有图谱知识点（5000+），LLM调用量爆炸

**解决方案**: 两阶段匹配

```
教材知识点 → 粗筛(top-20候选) → LLM双模型投票 → 匹配结果
```

**粗筛方式对比**:

| 方案 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **difflib** (原方案) | 字符相似度匹配 | 无依赖、速度快 | 语义理解弱 |
| **向量检索** (新方案) | Embedding语义匹配 | 自动理解同义词、语义强 | 需安装依赖 |

#### D4.3 向量检索方案（推荐采用）

**核心思想**: 将知识点转换为语义向量，通过余弦相似度找到语义最接近的候选

```python
class LocalVectorRetriever:
    """本地向量检索器"""

    def __init__(self, kg_concepts):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        self.texts = [f"{c['label']} {c.get('description','')}" for c in kg_concepts]
        self.vectors = self.model.encode(self.texts, show_progress_bar=True)
        self.concepts = kg_concepts

    def retrieve(self, query: str, top_k=20):
        q_vec = self.model.encode([query])[0]
        scores = np.dot(self.vectors, q_vec) / (np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(q_vec))
        top_idx = np.argsort(scores)[-top_k:][::-1]
        return [self.concepts[i] for i in top_idx]
```

**技术选型**:

| 组件 | 选择 | 理由 |
|------|------|------|
| Embedding 模型 | `BAAI/bge-small-zh-v1.5` | 中文小模型 SOTA，内存 2-4GB，维度 512 |
| 向量索引 | `numpy` 暴力搜索 | 图谱 ≤ 5000 条，暴力计算足够快（< 10ms） |
| 依赖库 | `sentence-transformers` | 一行代码加载模型，自动处理 tokenization |

**资源评估**:

| 项目 | 数值 | 说明 |
|------|------|------|
| 模型内存 | 2.5 GB | bge-small-zh-v1.5 实际占用 |
| 向量存储 | 5000 × 512 × 4字节 ≈ 10 MB | numpy float32 |
| 其他开销 | < 1 GB | 原有数据结构 |
| **总计** | **约 3.5 GB** | 远低于 8GB 限制 |

**预期收益**:

| 指标 | 改进前 (difflib) | 改进后 (向量) |
|------|------------------|---------------|
| 候选语义相关性 | 低（仅字符匹配） | 高（理解同义词、语序） |
| 漏匹配风险 | 中（"勾股定理" vs "毕达哥拉斯定理"） | 极低 |
| LLM 调用次数 | 不变（仍为 top-20） | 不变 |
| 总体匹配准确率 | 基准 | **预计提升 10-20%** |

#### D4.4 精确匹配增强

**标准化处理**:
```python
def _normalize_name(self, name: str) -> str:
    # 转小写、去空格、统一括号
    normalized = name.strip().lower()
    normalized = normalized.replace(' ', '').replace('　', '')  # 半角/全角空格
    normalized = normalized.replace('（', '(').replace('）', ')')
    return normalized
```

**同义词映射**（完整词匹配，防止过度匹配）:
```python
SYNONYM_MAP = {
    "加法": ["加", "加法运算", "相加", "求和"],
    "百分数": ["百分比", "百分率"],
    ...
}
```

#### D4.5 异常处理和输出完整性

- LLM 调用失败时 `continue`，不中断整个知识点
- 输出所有教材知识点（含未匹配），增加 `matched` 字段

### D5: 断点续传设计（集成 llmTaskLock）

**决策**: 所有 LLM 任务必须支持断点续传

**需要断点续传的任务**：

| 任务 | 核心模块 | 命令行入口 | 进度文件 | 锁文件 |
|------|----------|-----------|----------|--------|
| **知识图谱匹配** | `edukg/core/textbook/kp_matcher.py` | `match_textbook_kp.py --resume` | `progress/match_kg_state.json` | `progress/match_kg.lock` |
| **教学知识点推断** | `edukg/core/llm_inference/textbook_kp_inferer.py` | `infer_textbook_kp.py --resume` | `progress/infer_kp_state.json` | `progress/infer_kp.lock` |

**不需要断点续传的任务**：
- 数据生成 (`generate_textbook_data.py`) - 纯 JSON 解析，无 LLM 调用
- 精确匹配 - 字符串比对，瞬时完成

**集成示例 (KPMatcher)**：

```python
from edukg.core.llmTaskLock import TaskState, CachedLLM, ProcessLock

class KPMatcher:
    def __init__(self):
        self.task_state = TaskState("kp_match")
        self.cached_llm = CachedLLM("kp_match_cache")
        self.process_lock = ProcessLock("kp_match.lock")

    async def match_batch(self, pairs, resume=True):
        # 加载进度
        if resume:
            completed = self.task_state.load()

        with self.process_lock:
            for pair in pairs:
                # 跳过已完成
                if pair['id'] in completed:
                    continue

                # 检查缓存
                cached = self.cached_llm.get(pair)
                if cached:
                    results.append(cached)
                    continue

                # 执行匹配
                result = await self._match_one(pair)

                # 缓存 + 记录
                self.cached_llm.set(pair, result)
                self.task_state.mark_done(pair['id'])

                # 定期保存
                if len(results) % 10 == 0:
                    self.task_state.save()

            self.task_state.save()
```

### D6: 输出文件结构

```
edukg/data/edukg/math/5_教材目录/output/
├── textbooks.json            # 教材节点
├── chapters.json             # 章节节点
├── sections.json             # 小节节点
├── textbook_kps.json         # 教材知识点节点
├── contains_relations.json   # CONTAINS 关系
├── in_unit_relations.json    # IN_UNIT 关系
├── matches_kg_relations.json # MATCHES_KG 关系（推理结果）
├── import_summary.json       # 导入统计摘要
└── progress/                 # 进度文件目录
    ├── infer_kp_state.json   # 教学知识点推断进度
    ├── match_kg_state.json   # 知识图谱匹配进度
    └── *.lock
```

### D7: 数据模型设计

**节点设计**：

| 节点类型 | 约束 | 属性 |
|---------|------|------|
| Textbook | `uri UNIQUE`, `id UNIQUE` | uri, id, label, stage, grade, semester, publisher, edition |
| Chapter | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order |
| Section | `uri UNIQUE`, `id UNIQUE` | uri, id, label, order, mark |
| TextbookKP | `uri UNIQUE` | uri, label, stage, grade |

**关系设计**：

| 关系类型 | 起点 → 终点 | 语义 | 来源 |
|---------|------------|------|------|
| **CONTAINS** | Textbook → Chapter → Section | 目录层级 | 数据解析 |
| **IN_UNIT** | TextbookKP → Section | 知识点所属单元 | 数据解析 |
| **MATCHES_KG** | TextbookKP → Concept | 匹配图谱 | LLM 推断 |

### D8: URI 命名规范 (v3.1)

```
http://edukg.org/knowledge/3.1/{type}/math#{id}
```

| 节点类型 | ID 格式 | 示例 |
|---------|--------|------|
| Textbook | `{publisher}-{grade}{semester}` | `renjiao-g1s` |
| Chapter | `{textbook_id}-{order}` | `renjiao-g1s-1` |
| Section | `{chapter_id}-{order}` | `renjiao-g1s-1-1` |
| TextbookKP | `textbook-{stage}-{seq:05d}` | `textbook-primary-00001` |

### D9: 知识点过滤规则

```python
# 非知识点标记
NON_KNOWLEDGE_POINT_MARKERS = {
    "数学活动", "小结", "整理和复习", "本章综合与测试",
    "本节综合与测试", "复习题", "★数学乐园", ...
}

# 非知识点前缀
NON_KNOWLEDGE_POINT_PREFIXES = [
    "阅读与思考 ", "阅读与思考　",  # 全角空格
    "信息技术应用 ", "信息技术应用　",
    "例",  # 例1, 例2...
    ...
]

# 正则匹配
NON_KNOWLEDGE_POINT_PATTERNS = [
    r"^例\d",  # 例1, 例2...
]
```

### D10: 数据清洗设计（清理冗余标签）

**问题**: 部分章节带有"（通用）"字样，部分 Section 带有序号前缀和不规范标点

**解决方案**:

```python
# 清理规则
class DataCleaner:
    """数据清洗器"""

    # "通用"标签处理
    GENERIC_SUFFIXES = ["（通用）", "(通用)", "（综合）", "(综合)"]

    # Section 标签清洗
    SECTION_CLEANUP_PATTERNS = [
        r"^\d+\.\d+-",           # 移除前缀如 "3.1-"
        r"^\d+\.\d+\.\d+-",      # 移除前缀如 "18.1.1-"
        r":$|：$",               # 移除末尾冒号
    ]

    def clean_section_label(self, label: str) -> str:
        """清洗 Section 标签"""
        for pattern in self.SECTION_CLEANUP_PATTERNS:
            label = re.sub(pattern, "", label)
        return label.strip()

    def detect_generic_duplicate(self, chapters: List) -> List:
        """检测"通用"标签的重复数据"""
        duplicates = []
        # 检查是否有同名但带/不带"通用"的章节
        for chapter in chapters:
            if any(suffix in chapter['label'] for suffix in self.GENERIC_SUFFIXES):
                # 查找对应的非通用版本
                base_name = chapter['label'].replace("（通用）", "").replace("(通用)", "")
                duplicates.append({
                    'generic': chapter,
                    'base_name': base_name
                })
        return duplicates
```

### D11: 知识点属性扩展设计

**目标**: 为 TextbookKP 增加教学属性，支持精准教学应用

**新增属性**:

| 属性 | 类型 | 说明 | 来源 |
|------|------|------|------|
| `difficulty` | int (1-5) | 难度等级 | 规则推断（年级基础）+ 关键词调整 |
| `importance` | str | 核心/重要/了解 | 规则匹配（关键词） |
| `cognitive_level` | str | 识记/理解/应用/分析 | 规则匹配（知识点类型） |
| `topic` | str | 所属专题 | 继承章节 topic（无需推断） |

**设计原则**: 优先使用规则匹配，减少 LLM 调用成本

**推断策略**:

| 属性 | 推断方法 | 示例 |
|------|----------|------|
| `topic` | 继承所属 Section/Chapter 的 topic | Section 属于"数与代数"章节 → topic="数与代数" |
| `difficulty` | 年级基础 + 关键词调整 | 六年级=3，"综合应用"关键词+1 → 4 |
| `importance` | 关键词匹配 | 含"概念"、"定义"→ 核心；含"拓展"→ 了解 |
| `cognitive_level` | 知识点类型匹配 | 概念类→识记；运算类→应用；推理类→分析 |

**规则映射表**:

```python
# 年级 → 基础难度
GRADE_BASE_DIFFICULTY = {
    "一年级": 1, "二年级": 1, "三年级": 2,
    "四年级": 2, "五年级": 3, "六年级": 3,
    "七年级": 3, "八年级": 4, "九年级": 4,
    "必修第一册": 4, "必修第二册": 4, "必修第三册": 5,
}

# 难度调整关键词
DIFFICULTY_KEYWORDS = {
    "+1": ["综合", "应用", "拓展", "探究", "复杂"],
    "-1": ["认识", "初步", "简单", "基础"],
}

# 重要性关键词
IMPORTANCE_KEYWORDS = {
    "核心": ["概念", "定义", "定理", "公式", "法则", "性质", "原理"],
    "重要": ["运算", "计算", "方法", "技巧", "应用"],
    "了解": ["拓展", "阅读", "活动", "兴趣", "课外"],
}

# 认知层次映射（知识点类型 → 认知层次）
COGNITIVE_LEVEL_MAP = {
    "概念类": "识记",    # 定义、概念、术语
    "理解类": "理解",    # 性质、关系、规律
    "运算类": "应用",    # 计算、运算、求解
    "推理类": "分析",    # 证明、推导、推理
}
```

**推断流程**:

```python
class KPAttributeInferer:
    """知识点属性推断器（规则匹配）"""

    def infer_attributes(self, kp_name: str, grade: str, section_topic: str) -> dict:
        # 1. topic：直接继承章节
        topic = section_topic

        # 2. difficulty：年级基础 + 关键词调整
        base = GRADE_BASE_DIFFICULTY.get(grade, 3)
        for keyword, adjust in DIFFICULTY_KEYWORDS.items():
            if keyword in kp_name:
                base += adjust
        difficulty = max(1, min(5, base))

        # 3. importance：关键词匹配
        importance = "重要"  # 默认
        for level, keywords in IMPORTANCE_KEYWORDS.items():
            if any(kw in kp_name for kw in keywords):
                importance = level
                break

        # 4. cognitive_level：知识点类型推断
        cognitive_level = "理解"  # 默认
        if any(kw in kp_name for kw in ["概念", "定义", "认识"]):
            cognitive_level = "识记"
        elif any(kw in kp_name for kw in ["计算", "运算", "求解", "应用"]):
            cognitive_level = "应用"
        elif any(kw in kp_name for kw in ["证明", "推导", "推理"]):
            cognitive_level = "分析"

        return {
            "difficulty": difficulty,
            "importance": importance,
            "cognitive_level": cognitive_level,
            "topic": topic,
        }
```

**人工审核点**:

在代码执行前，需要人工审核以下内容：
1. 规则映射表是否覆盖主要知识点类型
2. 难度调整关键词是否合理
3. 重要性关键词是否完整
4. 认知层次映射是否符合教学实际

### D12: 单元/专题层级设计

**背景**: 教材的"章"过大、"节"过细，缺少中间的"单元"概念

**设计方案**:

```
当前层级：教材 → 章 → 节 → 知识点
新增层级：教材 → 章 → 单元(Unit) → 节 → 知识点
```

**实现方式**:

| 方案 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **A: 新增 Unit 节点** | 创建 Unit 节点类型，建立 CONTAINS 关系 | 结构清晰，支持跨年级专题 | 需要修改现有数据模型 |
| **B: Chapter 增加 topic 字段** | 为 Chapter 增加 topic 属性，标注所属专题 | 改动小，不影响现有关系 | 无法细化到节级别 |
| **C: Section 增加 unit_id 字段** | 为 Section 增加所属单元标识 | 简单，不改变节点结构 | 需要人工或 LLM 划分 |

**建议**: 采用方案 B（Chapter 增加 topic 字段），后续迭代可扩展为方案 A

```python
# 方案 B 实现
class ChapterEnhancer:
    """章节专题增强"""

    # 人教版数学专题分类
    MATH_TOPICS = {
        "数与代数": ["有理数", "整式的加减", "一元一次方程", ...],
        "图形与几何": ["几何图形初步", "相交线与平行线", "三角形", ...],
        "统计与概率": ["数据的收集与整理", "概率初步", ...],
        "综合与实践": ["数学活动", "课题学习", ...]
    }

    def assign_topic(self, chapter_name: str) -> str:
        """为章节分配专题"""
        for topic, keywords in self.MATH_TOPICS.items():
            for keyword in keywords:
                if keyword in chapter_name:
                    return topic
        return "其他"
```

### D13: 多版本教材支持设计

**未来扩展**: 支持北师大版、苏教版等多版本教材

**URI 设计调整**:

```
当前：renjiao-g1s（隐含版本）
未来：{edition}-{grade}{semester}
  - renjiao-g1s（人教版）
  - bnu-g1s（北师大版）
  - sujiao-g1s（苏教版）
```

**数据模型扩展**:

| 属性 | 当前 | 扩展后 |
|------|------|--------|
| `publisher` | 固定"人民教育出版社" | 动态配置 |
| `edition` | 固定"人教版" | 动态配置 |
| `version_code` | 无 | 新增，用于版本对比 |

**当前阶段**: 不实现，记录在 Non-Goals

## Risks / Trade-offs

### R1: 知识点匹配率低
**风险**: LLM 匹配可能不准确
**缓解**: 双模型投票 + 置信度阈值 + 候选关系保留

### R2: 教学知识点推断质量
**风险**: LLM 推断的知识点可能不准确
**缓解**: 使用教研员角色提示词 + 保留置信度 + 人工验证

### R3: 手动导入验证成本
**风险**: 人工验证 JSON 数据需要时间
**缓解**: 输出详细统计摘要 + 提供 Cypher 模板 + 分批验证导入

### R4: 推理依赖
**风险**: 依赖 kg-math-prerequisite-inference 的推理机制
**缓解**: kg-math-prerequisite-inference 需要先完成

### R5: "通用"标签处理复杂度
**风险**: 清理"通用"标签可能误删有效数据
**缓解**: 先检测并列出候选重复数据，人工确认后再处理

### R6: 知识点属性推断一致性
**风险**: 不同章节推断的 difficulty/importance 可能不一致
**缓解**: 使用统一标准 + 建立属性校验规则

## Migration Plan

**执行步骤**：

1. **数据生成（已完成）**：
   - ✅ 运行 `generate_textbook_data.py`
   - ✅ 输出 textbooks.json, chapters.json, sections.json, textbook_kps.json
   - ✅ 输出 contains_relations.json, in_unit_relations.json

2. **教学知识点推断（待执行）**：
   - 运行 `infer_textbook_kp.py --resume`
   - 输出更新后的 `textbook_kps.json`
   - 重新生成 `in_unit_relations.json`

3. **知识图谱匹配（待执行）**：
   - 运行 `match_textbook_kp.py --resume`
   - 输出 `matches_kg_relations.json`

4. **数据清洗（新增）**：
   - 运行 `clean_textbook_data.py`
   - 清理"通用"标签、规范 Section 名称
   - 输出清洗报告

5. **知识点属性扩展（新增）**：
   - 运行 `enhance_kp_attributes.py --resume`
   - 推断 difficulty, importance, cognitive_level, topic
   - 输出增强后的 textbook_kps.json

6. **人工验证和导入**：
   - 检查输出文件数据质量
   - 执行 Cypher 导入
   - 验证导入结果

## Open Questions

1. **Q1**: 教学知识点推断的准确率如何评估？
   - 建议：人工抽查 + 与已知知识点对比

2. **Q2**: 未匹配到知识图谱的 TextbookKP 如何处理？
   - 建议：保留为孤立节点，后续可创建新 Concept

3. **Q3**: "通用"标签数据是否直接删除？
   - 建议：先生成重复检测报告，人工确认后再决定合并或删除

4. **Q4**: 单元/专题层级采用哪种方案？
   - 建议：当前阶段采用方案 B（Chapter.topic 字段），后续迭代可扩展

5. **Q5**: 知识点属性是否需要人工校验？
   - 建议：LLM 推断后生成报告，核心知识点人工复核

6. **Q6**: 多版本教材何时支持？
   - 建议：当前专注人教版，多版本作为 v3.2 版本规划