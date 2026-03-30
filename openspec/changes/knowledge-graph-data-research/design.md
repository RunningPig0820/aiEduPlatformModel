知识图谱数据整理方案设计
一、目标
将现有数据整理成支持 AI 作业答疑业务的知识图谱：
● 按学科、年级组织知识点
● 建立知识点前置/后置依赖关系
● 支持学习路径推荐和知识缺陷诊断

二、数据模型设计
2.1 知识点层级结构
学科 (Subject)
└── 学段 (Stage: 小学/初中/高中)
└── 年级 (Grade)
└── 教材 (Textbook)
└── 章节 (Chapter)
└── 知识点 (KnowledgePoint)
2.2 Neo4j 节点模型
// 学科节点
(:Subject {name: "数学", code: "math"})

// 学段节点
(:Stage {name: "高中", code: "high_school"})

// 年级节点
(:Grade {name: "高一", code: "g10", order: 1})

// 教材节点
(:Textbook {
name: "高中数学必修第一册",
isbn: "9787107336270",
subject: "math",
grade: "g10"
})

// 章节节点
(:Chapter {
name: "集合与函数概念",
order: 1,
textbook_isbn: "9787107336270"
})

// 知识点节点 (核心)
(:KnowledgePoint {
uri: "http://edukg.org/knowledge/0.1/instance/math#516",
external_id: "edukg_516",    // 新增：跨源映射ID
name: "一元二次方程",
subject: "math",
stage: "初中",
grade: "初三",          // 推断或标注
chapter: "一元二次方程",
type: "定义",           // 定义/性质/定理/公式
difficulty: 3,          // 1-5 难度等级
source: "edukg"         // 数据来源
})
2.2.1 跨源映射表（新增）
建议来源：后续可能引入外部数据（如好未来数据），需建立跨源映射避免 URI 变化导致关系失效。
-- 跨源映射表（SQLite）
CREATE TABLE kp_source_mapping (
id INTEGER PRIMARY KEY,
canonical_uri TEXT NOT NULL,      -- 标准 URI（内部唯一标识）
external_id TEXT NOT NULL,        -- 外部数据源 ID
source_name TEXT NOT NULL,        -- 数据源名称（edukg/haoweilai/etc）
confidence REAL DEFAULT 1.0,      -- 匹配置信度
UNIQUE(canonical_uri, external_id, source_name)
);
2.3 关系模型（区分教学顺序与学习依赖）
// ========== 层级关系 ==========
(:Subject)-[:HAS_STAGE]->(:Stage)
(:Stage)-[:HAS_GRADE]->(:Grade)
(:Grade)-[:USE_TEXTBOOK]->(:Textbook)
(:Textbook)-[:HAS_CHAPTER]->(:Chapter)
(:Chapter)-[:CONTAINS]->(:KnowledgePoint)

// ========== 分类关系 ==========
(:KnowledgePoint)-[:BELONGS_TO]->(:Category)
(:KnowledgePoint)-[:SUB_CATEGORY]->(:KnowledgePoint)

// ========== 教学顺序（教材安排顺序，不是学习依赖）==========
(:KnowledgePoint)-[:TEACHES_BEFORE {
confidence: 0.85,
source: "textbook_chapter",
creator: "system",         // 新增：创建者（system/llm/teacher）
evidence: ["chapter_order"]
}]->(:KnowledgePoint)

// ========== 核心前置关系（真正的学习依赖）==========
// 业务查询用 PREREQUISITE，EduKG 标准用 PREREQUISITE_ON
(:KnowledgePoint)-[:PREREQUISITE {
confidence: 0.85,
source: "llm",           // llm/definition_extraction/teacher
creator: "llm_glm",      // 新增：具体创建者（便于审计）
evidence_types: ["definition_dependency", "llm_inference"],
verified: false,
standard_relation: "PREREQUISITE_ON"
}]->(:KnowledgePoint)

// EduKG 标准关系（便于互操作）
(:KnowledgePoint)-[:PREREQUISITE_ON {
confidence: 0.85,
source: "llm"
}]->(:KnowledgePoint)

// ========== 候选前置关系（待验证，低置信度）==========
(:KnowledgePoint)-[:PREREQUISITE_CANDIDATE {
confidence: 0.65,
source: "llm_zero_shot",
evidence_types: ["llm_inference"],
status: "candidate"
}]->(:KnowledgePoint)

// ========== 知识点关联（TTL 原生 relateTo 数据）==========
(:KnowledgePoint)-[:RELATED_TO {
source: "edukg_relateTo"
}]->(:KnowledgePoint)

// ========== 难度递进关系（英语学科专用）==========
(:KnowledgePoint)-[:GRADED {
level: 1,                 // 难度等级
source: "textbook"
}]->(:KnowledgePoint)

// ========== 主题关联关系（历史/语文/地理/政治专用）==========
(:KnowledgePoint)-[:THEME {
theme_name: "中国近代史",
source: "llm"
}]->(:KnowledgePoint)
设计说明：
● TEACHES_BEFORE：教材教学顺序，不等于学习依赖。如"勾股定理"在教材中先于"圆"，但学圆不需要先学勾股定理。
● PREREQUISITE：真正的学习依赖（不学A就学不懂B），由定义依赖抽取 + LLM 多模型投票生成。
● PREREQUISITE_CANDIDATE：低置信度候选关系，待后续验证。
● PREREQUISITE_ON：EduKG 标准关系，方便未来互操作。

三、数据来源与整合策略
3.1 数据源分析
数据源	版本	内容	用途
ttl/*.ttl	v0.1	知识点实例	✅ 主要数据源
relations/*.ttl	v0.1	知识点关系	✅ 关联/分类关系
main.ttl	v3.0	教材出处	⚠️ 年级/教材信息（已拆分为 split/main-{subject}.ttl）
entities/*.json	v0.1	实体列表	✅ 实体链接
好未来数据	-	小学数学	📖 层级参考
3.2 整合策略
Step 1: 以 ttl/*.ttl 为主数据源
↓
Step 2: 通过标签匹配 split/main-{subject}.ttl 获取教材信息（如数学使用 main-math.ttl）
↓
Step 3: 从教材信息推断年级
↓
Step 4: 导入 relations/*.ttl 的关联关系
↓
Step 5: 构建 PREREQUISITE 关系

四、年级推断规则
4.1 教材 → 年级映射
TEXTBOOK_TO_GRADE = {
# 高中
"必修第一册": ("高中", "高一"),
"必修第二册": ("高中", "高一"),
"必修1": ("高中", "高一"),
"必修2": ("高中", "高二"),
"必修3": ("高中", "高二"),
"必修4": ("高中", "高三"),
"选择性必修1": ("高中", "高二"),
"选择性必修2": ("高中", "高二"),
"选择性必修3": ("高中", "高三"),

    # 初中
    "七年级上册": ("初中", "初一"),
    "七年级下册": ("初中", "初一"),
    "八年级上册": ("初中", "初二"),
    "八年级下册": ("初中", "初二"),
    "九年级上册": ("初中", "初三"),
    "九年级下册": ("初中", "初三"),
}

# 学段反向推断（fallback）
STAGE_FALLBACK = {
"初中数学": ("初中", None),  # 年级需额外推断
"高中数学": ("高中", None),
}
4.2 章节 → 学期推断
# 从 main.ttl 的 mark 字段推断
# mark: "6.2.1" 表示 第6章 第2节 第1小节
# 通常上学期学1-4章，下学期学5-8章
4.2.1 mark 字段解析兼容（新增）
问题：mark 字段格式可能不统一（如 "6.2.1"、"6-2-1"、"第六章第二节"）。
import re

def parse_mark_field(mark: str) -> tuple:
"""
解析 mark 字段，返回 (章节, 小节, 小节序号)
支持多种格式：6.2.1, 6-2-1, 第六章第二节, Chapter 6.2.1
"""
if not mark:
return (None, None, None)

    # 格式1: 6.2.1 或 6-2-1
    match = re.match(r'(\d+)[.\-](\d+)(?:[.\-](\d+))?', mark)
    if match:
        chapter = int(match.group(1))
        section = int(match.group(2))
        subsection = int(match.group(3)) if match.group(3) else 0
        return (chapter, section, subsection)

    # 格式2: 第六章第二节
    chinese_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
                    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    match = re.match(r'第([一二三四五六七八九十]+)章(?:第([一二三四五六七八九十]+)节)?', mark)
    if match:
        chapter = chinese_nums.get(match.group(1), 0)
        section = chinese_nums.get(match.group(2), 0) if match.group(2) else 0
        return (chapter, section, 0)

    # 格式3: Chapter 6.2.1
    match = re.match(r'Chapter\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?', mark, re.IGNORECASE)
    if match:
        chapter = int(match.group(1))
        section = int(match.group(2)) if match.group(2) else 0
        subsection = int(match.group(3)) if match.group(3) else 0
        return (chapter, section, subsection)

    # 无法解析，返回 (0, 0, 0) 作为 fallback
    return (0, 0, 0)
Fallback 策略：若章节信息完全缺失，按教材序号作为顺序（第1章、第2章）。

五、前置依赖关系构建方案（多证据融合）
5.1 核心原则
教学顺序 ≠ 学习依赖
教材章节顺序是教学安排顺序，不一定等于学习依赖顺序。
● 例如："勾股定理"在教材中先于"圆"，但学圆不需要先学勾股定理
● 因此：教材顺序存为 TEACHES_BEFORE，真正的学习依赖存为 PREREQUISITE
5.2 证据来源分类
证据类型	说明	基础权重	Demo 阶段策略
教材章节顺序	同章节内按 mark 顺序	0.7	→ TEACHES_BEFORE
定义/定理依赖	从定义文本中抽取的关键概念	0.85	→ PREREQUISITE（实现）
LLM 多模型投票	GLM + DeepSeek 两模型一致	0.8	→ PREREQUISITE/CANDIDATE
教师标注	人工审核	1.0	Demo 阶段不做
5.3 教材章节顺序（仅生成 TEACHES_BEFORE）
仅生成同章节内的 TEACHES_BEFORE 关系，不直接转化为 PREREQUISITE。
def infer_teaches_before(knowledge_points):
"""
按教材和章节分组，按 mark 顺序生成 TEACHES_BEFORE 关系
注意：这是教学顺序，不是学习依赖
"""
teaches_before = []
for textbook, kps in group_by_textbook(knowledge_points):
sorted_kps = sort_by_chapter_and_mark(kps)
for i in range(1, len(sorted_kps)):
prev = sorted_kps[i-1]
curr = sorted_kps[i]
if prev.chapter == curr.chapter:  # 仅同章节
teaches_before.append({
'from': prev.uri,
'to': curr.uri,
'confidence': 0.85,
'source': 'textbook_chapter',
'evidence': ['chapter_order']
})
return teaches_before
5.4 定义依赖抽取（强证据）- 改进版
从知识点的定义文本中提取关键词，匹配其他知识点名称。
智谱建议改进：原方案使用简单字符串匹配（if other_kp.name in kp.definition），容易产生误报（如"指数"匹配"指数函数"、"合"匹配"集合"）。
5.4.1 词边界匹配 + 停用词表
import re

# 停用词表：过滤过于泛化的词汇
STOPWORDS = {
"方法", "概念", "问题", "性质", "定理", "公式", "定义",
"计算", "求解", "证明", "分析", "结论", "结果",
"方法", "技巧", "步骤", "过程", "情况", "条件"
}

def extract_definition_dependencies(knowledge_points):
"""
从知识点的 definition 文本中抽取出现的其他知识点名称
使用词边界匹配 + 停用词过滤，避免误报
"""
dependencies = []
for kp in knowledge_points:
if not kp.definition:
continue
# 预处理：清洗定义文本
clean_def = preprocess_definition(kp.definition)
for other_kp in knowledge_points:
if other_kp.uri == kp.uri:
continue
# 停用词过滤
if other_kp.name in STOPWORDS:
continue
# 词边界匹配（确保是完整词，非子串）
pattern = r'\b' + re.escape(other_kp.name) + r'\b'
if re.search(pattern, clean_def):
dependencies.append({
'from': other_kp.uri,
'to': kp.uri,
'confidence': 0.85,
'source': 'definition_extraction',
'evidence_types': ['definition_dependency'],
'reason': f'"{kp.name}"的定义中包含完整词汇"{other_kp.name}"'
})
return dependencies

def preprocess_definition(definition: str) -> str:
"""
预处理定义文本：
1. 移除 Markdown 格式标记
2. 统一中英文标点
3. 移除多余空白
"""
# 移除 markdown 链接、加粗等标记
clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', definition)
clean = re.sub(r'\*+([^*]+)\*+', r'\1', clean)
# 统一标点
clean = clean.replace('，', ', ').replace('。', '. ')
clean = re.sub(r'\s+', ' ', clean)
return clean.strip()
5.4.2 知识点类型标准化
问题：不同数据源对类型划分标准不一致（如"公理"、"定律"应统一为"定理"）。
# 类型映射表
TYPE_MAPPING = {
# 定理类
"公理": "定理",
"定律": "定理",
"原理": "定理",
"定理": "定理",
# 公式类
"公式": "公式",
"方程": "公式",
"表达式": "公式",
# 定义类
"定义": "定义",
"概念": "定义",
"术语": "定义",
# 性质类
"性质": "性质",
"特征": "性质",
"属性": "性质",
# 方法类
"方法": "方法",
"算法": "方法",
"技巧": "方法",
}

def standardize_type(raw_type: str) -> str:
"""统一知识点类型"""
return TYPE_MAPPING.get(raw_type, raw_type)  # 未映射的保留原值
5.4.3 同义词映射（新增）
问题：定义中可能使用同义词而非精确知识点名，如"方程"与"等式"。
# 同义词映射表（按学科）
SYNONYM_MAPPING = {
"math": {
"方程": ["等式", "方程式"],
"函数": ["映射", "对应关系"],
"直线": ["一次函数图像", "线性函数图像"],
"抛物线": ["二次函数图像"],
"绝对值": ["模"],
"平方": ["二次方"],
"立方": ["三次方"],
},
"physics": {
"速度": ["速率"],  # 注：严格来说不等价，但定义中常混用
"加速度": ["加速度矢量"],
"力": ["力的作用"],
},
# 其他学科...
}

def build_synonym_patterns(subject: str, knowledge_points: list) -> dict:
"""
构建同义词匹配模式
返回: {标准知识点名: [同义词列表]}
"""
synonyms = SYNONYM_MAPPING.get(subject, {})
kp_names = {kp.name for kp in knowledge_points}
patterns = {}

    for kp_name in kp_names:
        patterns[kp_name] = [kp_name]  # 包含自身
        if kp_name in synonyms:
            patterns[kp_name].extend(synonyms[kp_name])

    return patterns

def match_with_synonyms(definition: str, patterns: dict) -> list:
"""
使用同义词匹配定义中的知识点
"""
matched = []
for kp_name, synonyms in patterns.items():
for syn in synonyms:
pattern = r'\b' + re.escape(syn) + r'\b'
if re.search(pattern, definition):
matched.append(kp_name)
break  # 只记录一次
return matched
5.4.4 概念层级依赖（新增）
问题：如"整式方程"是"方程"的子类，若定义中出现"整式方程"，则间接依赖"方程"。
# 概念层级关系（子类 -> 父类）
CONCEPT_HIERARCHY = {
"math": {
"整式方程": "方程",
"分式方程": "方程",
"一元二次方程": "整式方程",  # 传递依赖：一元二次方程 -> 整式方程 -> 方程
"二元一次方程": "整式方程",
"二次函数": "函数",
"一次函数": "函数",
"正比例函数": "一次函数",
"反比例函数": "函数",
}
}

def infer_hierarchical_dependencies(matched_kps: list, subject: str) -> list:
"""
从匹配的知识点推断层级依赖
"""
hierarchy = CONCEPT_HIERARCHY.get(subject, {})
dependencies = set(matched_kps)

    for kp in matched_kps:
        # 向上追溯父类
        current = kp
        while current in hierarchy:
            parent = hierarchy[current]
            dependencies.add(parent)
            current = parent

    return list(dependencies)
示例：
● 知识点"一元二次方程"定义："含有一个未知数，且未知数的最高次数是 2 的整式方程"
● → 词边界匹配出"整式方程"、"方程"（"未知数"若不在知识库则不匹配）
● → 停用词表过滤掉"方法"、"概念"等泛化词
● → 同义词匹配可扩展"方程"为["等式", "方程式"]
● → 层级依赖推断："整式方程" → 依赖"方程"
5.5 LLM 多模型投票 - 改进版
配置：GLM-4-flash + DeepSeek 两模型投票
LLM_CONFIG = {
"providers": ["zhipu", "deepseek"],
"model": {"zhipu": "glm-4-flash", "deepseek": "deepseek-V3"},
"scene": "prerequisite_inference",
"temperature": 0.3,
"batch_size": 10,      # 调小批次，提高精度
"max_retries": 2,
# 新增：滑动窗口配置
"context_window": {
"prev_chapter_kps": 20,   # 前序章节核心知识点数
"same_chapter_kps": 50,   # 同章节知识点数
}
}
5.5.1 Few-Shot Prompting（智谱建议）
在 Prompt 中增加高质量标注示例，引导模型更精准输出：
你是一个教育领域专家，擅长分析知识点之间的逻辑依赖关系。

任务：判断知识点 A 是否是学习知识点 B 之前必须掌握的**核心前置知识**。
核心前置知识定义：如果不会 A，则无法理解或学会 B（无论教学顺序如何）。

请严格区分：
- 核心前置：必须学会才能学 B（概念依赖）
- 教学顺序：只是教材安排更早，但不是必须（时间依赖）

## 示例（数学学科）

**示例 1：正确判断**
| 知识点 | 类型 | 定义 |
|--------|------|------|
| 一元二次方程 | 定义 | 含有一个未知数，且未知数的最高次数是 2 的整式方程 |
| 二次函数 | 定义 | 形如 y = ax² + bx + c 的函数 |
| 方程 | 定义 | 含有未知数的等式 |

**分析**：
- "一元二次方程"的核心前置：["方程"]
    - reason: "方程"是"一元二次方程"定义的核心概念，不理解方程就无法理解一元二次方程
    - confidence: 0.95
- "二次函数"的核心前置：["函数"]
    - reason: 二次函数是函数的特例，必须先理解函数概念
    - confidence: 0.9

**示例 2：区分教学顺序**
| 知识点 | 类型 | 定义 |
|--------|------|------|
| 勾股定理 | 定理 | 直角三角形两直角边的平方和等于斜边的平方 |
| 圆的性质 | 性质 | 圆的直径所对的圆周角是直角 |

**分析**：
- "圆的性质"的核心前置：[]
    - reason: 虽然教材中勾股定理先教，但学圆的性质不需要先学勾股定理，两者独立
    - confidence: 0.8

**示例 3：反例警示（新增）**
❌ **错误示例**：因为"勾股定理"和"圆"出现在同一章，就认为"勾股定理"是"圆"的前置。
✅ **正确分析**：教学顺序 ≠ 学习依赖。需要判断"不学A是否真的无法理解B"。

❌ **错误示例**：将"方程"作为"二次函数"的前置。
✅ **正确分析**：二次函数的核心前置是"函数"，"方程"虽有辅助作用但不绝对必须。

## 当前任务

学科：{subject}
前序章节核心知识点（供参考）：
| 序号 | 名称 | 类型 |
|------|------|------|
{prev_chapter_table}

当前批次知识点：
| 序号 | 名称 | 类型 | 定义描述 |
|------|------|------|----------|
{knowledge_points_table}

请为每个知识点输出其核心前置知识点列表。输出严格 JSON **数组**格式：
```json
[
  {
    "target": "知识点名称",
    "prerequisites": ["前置知识点名称"],
    "reason": "简要说明为什么这些是核心前置",
    "confidence": 0.0-1.0
  }
]
注意：
● 只输出 JSON 数组，不要任何额外解释。
● 前置知识必须在上述知识点列表中（不能虚构）。
● 如果没有核心前置，prerequisites 输出空列表。
● 严格区分核心前置 vs 教学顺序：参考示例 3 的反例警示。

#### 5.5.2 滑动窗口上下文（智谱建议）

解决跨章节依赖识别问题：携带前序章节核心知识点作为上下文。

```python
def build_batch_with_context(kps_by_chapter, current_chapter, config):
    """
    构建带滑动窗口上下文的批次
    """
    # 获取前序章节（按教材顺序）
    prev_chapters = get_previous_chapters(current_chapter)

    # 提取前序章节核心知识点（高频引用、定义类型）
    prev_kps = []
    for chapter in prev_chapters[-2:]:  # 最近2个章节
        chapter_kps = kps_by_chapter[chapter]
        # 按引用频次排序，取前N个
        core_kps = sorted(chapter_kps, key=lambda kp: kp.ref_count)[:config['prev_chapter_kps']]
        prev_kps.extend(core_kps)

    # 当前章节知识点
    current_kps = kps_by_chapter[current_chapter][:config['same_chapter_kps']]

    return {
        'prev_context': prev_kps,
        'current_batch': current_kps
    }
核心知识点选取标准（新增）：
选取前序章节核心知识点时，按以下优先级排序：
优先级	条件	说明
①	定义类知识点	如"函数定义"、"方程定义"，是基础概念
②	高频被引用	从定义依赖统计，被多个知识点依赖
③	教材标注"重点"	如有元数据
④	向量相似度（可选）	当前章节核心定义与前序章节知识点计算相似度，取最相关
def select_core_knowledge_points(chapter_kps: list, config: dict) -> list:
    """
    选取核心知识点（按优先级）
    """
    scored_kps = []
    for kp in chapter_kps:
        score = 0
        # 优先级1: 定义类
        if kp.type == "定义":
            score += 100
        # 优先级2: 高频被引用
        score += min(kp.ref_count, 50)  # 上限50
        # 优先级3: 重点标注
        if getattr(kp, 'is_key_point', False):
            score += 30
        scored_kps.append((score, kp))

    # 按分数降序，取前N个
    scored_kps.sort(key=lambda x: x[0], reverse=True)
    return [kp for _, kp in scored_kps[:config['prev_chapter_kps']]]
5.5.3 幻觉检测 + JSON 容错（智谱建议）- 支持 JSON 数组格式
import json
import re

def parse_and_validate_llm_response(response: str, valid_kp_names: set) -> dict:
    """
    解析 LLM 响应，验证并过滤幻觉
    支持 JSON 数组格式（新）和对象格式（旧）
    """
    # 1. JSON 格式修复
    # 移除 markdown 代码块标记
    clean = re.sub(r'^```json\s*', '', response)
    clean = re.sub(r'\s*```$', '', clean)
    # 修复尾部逗号
    clean = re.sub(r',\s*}', '}', clean)
    clean = re.sub(r',\s*]', ']', clean)

    # 2. 解析 JSON
    try:
        parsed = json.loads(clean)
    except json.JSONDecodeError as e:
        logging.warning(f"JSON 解析失败: {e}, 尝试修复...")
        parsed = aggressive_json_repair(clean)

    # 3. 格式转换：数组格式 → 对象格式（统一处理）
    if isinstance(parsed, list):
        parsed = {item['target']: item for item in parsed if 'target' in item}

    # 4. 幻觉检测：过滤不存在知识点
    validated = {}
    for kp_name, info in parsed.items():
        # 校验知识点名称
        if kp_name not in valid_kp_names:
            logging.warning(f"幻觉检测: '{kp_name}' 不在合法集合中，丢弃")
            continue

        # 校验前置知识点名称
        valid_prereqs = [p for p in info.get('prerequisites', []) if p in valid_kp_names]
        if len(valid_prereqs) != len(info.get('prerequisites', [])):
            filtered = set(info['prerequisites']) - set(valid_prereqs)
            logging.warning(f"幻觉检测: 前置知识点 {filtered} 不合法，已过滤")

        validated[kp_name] = {
            'prerequisites': valid_prereqs,
            'reason': info.get('reason', ''),
            'confidence': info.get('confidence', 0.0)
        }

    return validated

def aggressive_json_repair(text: str) -> dict:
    """
    激进的 JSON 修复策略
    """
    # 尝试提取最后一个完整 JSON 对象
    # 匹配 {...} 模式
    matches = re.findall(r'\{[^{}]*\}', text)
    if matches:
        # 尝试拼接所有匹配
        combined = '{' + ', '.join(matches) + '}'
        try:
            return json.loads(combined)
        except:
            pass
    # 最终 fallback：返回空对象
    return {}
投票合并算法：
def llm_inference_with_voting(kp_batch):
    """
    两模型投票：至少两个模型输出一致才采纳
    """
    results = []
    for provider in LLM_CONFIG["providers"]:
        llm = LLMFactory.get_llm(scene="prerequisite_inference", provider=provider)
        response = llm.chat(prompt)
        parsed = parse_json(response)
        results.append(parsed)

    # 投票合并
    candidate_relations = {}
    for result in results:
        for target, info in result.items():
            for prereq in info["prerequisites"]:
                key = (prereq, target)
                if key not in candidate_relations:
                    candidate_relations[key] = []
                candidate_relations[key].append({
                    "confidence": info["confidence"],
                    "reason": info["reason"]
                })

    # 最终候选：两模型一致，取平均置信度
    final_candidates = []
    for (from_kp, to_kp), votes in candidate_relations.items():
        if len(votes) >= 2:  # 两模型一致
            avg_conf = sum(v["confidence"] for v in votes) / len(vote)
            final_candidates.append({
                "from": from_kp,
                "to": to_kp,
                "confidence": avg_conf,
                "evidence_types": ["llm_inference"],
                "source": "llm_multi_vote"
            })
    return final_candidates
5.6 多证据融合
def fuse_prerequisites(definition_deps, llm_candidates):
    """
    融合定义依赖 + LLM 多模型投票，生成最终 PREREQUISITE
    """
    EVIDENCE_WEIGHTS = {
        "definition_dependency": 0.85,
        "llm_inference": 0.8,
    }

    relations = {}

    # 定义依赖（强证据，直接生成 PREREQUISITE）
    for dep in definition_deps:
        key = (dep["from"], dep["to"])
        relations[key] = {
            "confidence": EVIDENCE_WEIGHTS["definition_dependency"],
            "evidence_types": ["definition_dependency"],
            "source": "definition_extraction"
        }

    # LLM 候选（两模型一致且置信度 >=0.8）
    for cand in llm_candidates:
        key = (cand["from"], cand["to"])
        if cand["confidence"] >= 0.8:
            if key in relations:
                # 已有定义依赖，提升置信度
                relations[key]["confidence"] = min(1.0, relations[key]["confidence"] + 0.1)
                relations[key]["evidence_types"].append("llm_inference")
            else:
                relations[key] = {
                    "confidence": cand["confidence"],
                    "evidence_types": ["llm_inference"],
                    "source": "llm_multi_vote"
                }
        else:
            # 低置信度存入 PREREQUISITE_CANDIDATE
            pass

    return relations
融合规则总结：
● 定义依赖：强证据，直接生成 PREREQUISITE
● LLM 候选：两模型一致 + 置信度 ≥0.8 → PREREQUISITE；否则 → PREREQUISITE_CANDIDATE
● 教材顺序：仅作为 TEACHES_BEFORE，不转化为 PREREQUISITE

六、实施步骤
阶段一：数据清洗与整合 (按学科逐个处理)
Step 1.1: 选择学科 (从数学开始)
Step 1.2: 解析 ttl/math.ttl → 提取知识点
Step 1.3: 解析 relations/math_relations.ttl → 提取关系
Step 1.4: 匹配 split/main-math.ttl → 获取教材信息
Step 1.5: 推断年级信息
Step 1.6: 数据验证
阶段二：导入 Neo4j
Step 2.1: 创建学科/学段/年级节点
Step 2.2: 创建教材/章节节点
Step 2.3: 创建知识点节点
Step 2.4: 创建分类关系 (BELONGS_TO)
Step 2.5: 创建关联关系 (RELATED_TO)
阶段三：构建前置依赖
Step 3.1: 基于教材章节顺序生成基础依赖
Step 3.2: 调用 LLM 补充跨章节依赖
Step 3.3: 合并去重，按置信度排序
Step 3.4: 导入 Neo4j (PREREQUISITE 关系)
Step 3.5: 提供人工审核接口
阶段四：验证与优化
Step 4.1: 抽查前置关系的合理性
Step 4.2: 验证学习路径的正确性
Step 4.3: 收集反馈，持续优化

七、预期产出
7.1 数据产物
产物	格式	说明
知识点标准数据	JSON/CSV	整合后的知识点列表，含年级、学科、类型
前置依赖关系	CSV	三元组 (from, to, confidence, source)
知识图谱数据库	Neo4j	可直接查询的图数据库
CSV 导出格式:
# 知识点标准数据 (knowledge_points.csv)
uri,name,subject,stage,grade,chapter,type,description,difficulty,source
http://edukg.org/...,一元二次方程,数学,初中,初三,一元二次方程,定义,含有一个未知数...,3,edukg

# 前置依赖关系 (prerequisites.csv)
from_uri,to_uri,confidence,source,reason
http://edukg.org/...,http://edukg.org/...,0.85,textbook_chapter,
注意: type 列必须导出，便于后续按类型查询和分析 |
7.2 代码产物
代码	说明
clean_data.py	数据清洗脚本
import_to_neo4j.py	Neo4j 导入脚本
build_prerequisites.py	前置关系构建脚本
llm_inference.py	LLM 推理调用脚本

八、分学科处理策略 (已确认)
8.1 学科类型划分
学科类型	学科	关系特点	处理策略	优先级
强逻辑链学科	数学、物理、化学、生物	前置关系明确，学习顺序固定	构建 PREREQUISITE 关系	P1
语言学科	英语	语法层级、词汇递进	构建语法/词汇层级	P2
主题关联学科	历史、语文、地理、政治	主题/时间关联，非学习依赖	构建主题分类关系	P3
8.2 处理顺序 (Phase by Phase)
Phase 1: 数学 (有关系数据，验证设计)
         - 知识点数: 4,490
         - relateTo: 9,870 (可直接使用)
         - subCategory: 328 (层级关系)
         - 目标: 验证整体流程可行性

Phase 2: 物理、化学、生物 (强逻辑链，需构建关系)
         - 物理: 3,385 知识点
         - 化学: 5,718 知识点
         - 生物: 15,209 知识点
         - 目标: 使用 LLM 构建前置关系

Phase 3: 英语 (语法层级)
         - 英语: 5,107 知识点
         - 目标: 构建语法/词汇层级

Phase 4: 历史、语文、地理、政治 (主题关联)
         - 历史: 4,850 知识点
         - 语文: 8,041 知识点
         - 地理: 4,682 知识点
         - 政治: 5,309 知识点
         - 目标: 构建主题分类，不做前置依赖
8.3 前置关系构建方案 (已确认: LLM 推理)
模型选择: GLM-4-flash (免费，主力)
# LLM 推理配置
LLM_CONFIG = {
    "provider": "zhipu",
    "model": "glm-4-flash",  # 免费，主力
    "scene": "prerequisite_inference",
    "batch_size": 50,  # 每批处理50个知识点
    "temperature": 0.3,  # 降低随机性，提高一致性
}
调用方式: 复用现有 LLM Gateway，新增 prerequisite_inference scene
推理流程:
1. 按学科分组知识点
2. 按章节/主题分批 (每批 50 个)
3. 调用 LLM 分析前置关系
4. 输出带置信度的关系数据
5. 置信度 < 0.7 直接丢弃，不做人工审核
relateTo 数据处理:
● relateTo → RELATED_TO（知识点关联，必须保留）
● Demo 阶段不做 LLM 验证补充，核心闭环跑通后再优化
8.4 分学科细化策略（新增）
8.4.1 强逻辑链学科（数理化生）
化学/生物定制停用词表：
# 学科专属停用词表
SUBJECT_STOPWORDS = {
    "math": ["数", "形", "运算", "计算", "求解"],  # 数学专属
    "physics": ["运动", "状态", "变化", "过程"],
    "chemistry": ["反应", "物质", "元素", "化合物", "离子"],  # 化学专属
    "biology": ["细胞", "生物", "生命", "遗传", "变异"],  # 生物专属
}

def get_subject_stopwords(subject: str) -> set:
    """获取学科专属停用词"""
    base_stopwords = STOPWORDS  # 通用停用词
    subject_stopwords = SUBJECT_STOPWORDS.get(subject, set())
    return base_stopwords | subject_stopwords
物理学科特殊处理：
# 物理公式符号前置关系
PHYSICS_SYMBOL_DEPENDENCIES = {
    "v = s/t": ["位移", "时间", "速度"],
    "F = ma": ["力", "质量", "加速度"],
    "E = mc²": ["能量", "质量", "光速"],
}

def extract_physics_formula_dependencies(kp):
    """
    物理公式类知识点特殊处理：
    公式中的符号含义需要前置
    """
    if kp.type != "公式":
        return []

    dependencies = []
    for formula, prereqs in PHYSICS_SYMBOL_DEPENDENCIES.items():
        if formula in kp.definition:
            dependencies.extend(prereqs)
    return dependencies
8.4.2 语言学科（英语）
英语 GRADED 关系：表示难度递进，而非学习依赖。
def build_english_graded_relations(knowledge_points: list) -> list:
    """
    构建英语难度递进关系
    词汇 → 短语 → 句型
    """
    # 词汇分级
    VOCAB_LEVELS = {
        "小学词汇": 1, "初中词汇": 2, "高中词汇": 3,
        "四级词汇": 4, "六级词汇": 5, "考研词汇": 6,
    }

    # 语法层级
    GRAMMAR_HIERARCHY = {
        "简单句": 1, "并列句": 2, "复合句": 3,
        "名词性从句": 4, "定语从句": 4, "状语从句": 4,
    }

    graded_relations = []
    for kp in knowledge_points:
        if kp.name in VOCAB_LEVELS:
            level = VOCAB_LEVELS[kp.name]
            # 同级词汇不建立关系
            # 跨级词汇建立 GRADED 关系
            pass
        elif kp.name in GRAMMAR_HIERARCHY:
            level = GRAMMAR_HIERARCHY[kp.name]
            # 语法层级关系
            pass

    return graded_relations
8.4.3 主题关联学科（历史、语文、地理、政治）
THEME 关系：用于主题聚类和推荐，非学习依赖。
def build_theme_relations(knowledge_points: list, subject: str) -> list:
    """
    构建主题关联关系
    """
    # 历史主题
    HISTORY_THEMES = {
        "中国近代史": ["鸦片战争", "太平天国", "洋务运动", "甲午战争", "戊戌变法"],
        "世界近代史": ["文艺复兴", "宗教改革", "启蒙运动", "工业革命"],
        "中国古代史": ["秦朝", "汉朝", "唐朝", "宋朝", "明朝", "清朝"],
    }

    # 语文主题
    CHINESE_THEMES = {
        "唐诗": ["李白", "杜甫", "白居易", "王维"],
        "宋词": ["苏轼", "辛弃疾", "李清照", "柳永"],
        "古文运动": ["韩愈", "柳宗元", "欧阳修"],
    }

    # 地理主题
    GEOGRAPHY_THEMES = {
        "中国地理": ["地形", "气候", "河流", "资源"],
        "世界地理": ["亚洲", "欧洲", "非洲", "美洲"],
    }

    themes_map = {
        "history": HISTORY_THEMES,
        "chinese": CHINESE_THEMES,
        "geography": GEOGRAPHY_THEMES,
    }

    themes = themes_map.get(subject, {})
    relations = []

    for kp in knowledge_points:
        for theme_name, theme_kps in themes.items():
            if kp.name in theme_kps:
                relations.append({
                    'from': kp.uri,
                    'to': theme_name,
                    'relation_type': 'THEME',
                    'source': 'rule_based'
                })

    return relations

九、验证方案 (Demo 阶段务实策略)
9.1 验证方式
方式	说明	Demo 阶段策略
自动验证	循环依赖检测、年级倒置检测（按跨度惩罚）	数据导入前自动执行
抽样测试	随机抽取检查合理性	≥70% 准确率即可满足 demo
人工审核	教师审核	不做，无相关人员参与
9.2 置信度处理
● 置信度 < 0.8 的 LLM 候选：存入 PREREQUISITE_CANDIDATE
● 定义依赖：直接生成 PREREQUISITE
● LLM 多模型投票一致 + 置信度 ≥0.8：生成 PREREQUISITE
● 新增：年级倒置按跨度惩罚置信度（智谱建议）
9.3 年级倒置的宽松处理（智谱建议）
问题：原方案将"高年级指向低年级"直接判定为异常。但在实际教学中，跨学段复习或螺旋式课程设计是合理的（如高二物理用到初三数学知识）。
改进方案：按年级跨度设置不同的置信度惩罚权重：
# 年级顺序映射
GRADE_ORDER = {
    "小学": {"一年级": 1, "二年级": 2, "三年级": 3, "四年级": 4, "五年级": 5, "六年级": 6},
    "初中": {"初一": 7, "初二": 8, "初三": 9},
    "高中": {"高一": 10, "高二": 11, "高三": 12},
}

def apply_grade_penalty(relation, from_kp, to_kp):
    """
    根据年级跨度惩罚置信度
    """
    from_order = get_grade_order(from_kp.grade, from_kp.stage)
    to_order = get_grade_order(to_kp.grade, to_kp.stage)

    if from_order is None or to_order is None:
        return relation  # 无法判断，保持原置信度

    span = from_order - to_order  # 前置知识的年级 - 目标知识的年级

    if span <= 0:
        # 前置年级 ≤ 目标年级：正常，不惩罚
        return relation

    # 年级倒置（前置知识年级更高）
    if span <= 2:
        # 同学段或相邻年级：合理（如高一数学 -> 初三数学基础）
        penalty = 0.95  # 置信度 * 0.95
        reason = "跨相邻年级，视为合理复习关联"
    elif span <= 3:
        # 跨 1 个学段（如高中->初中）：需确认
        penalty = 0.9
        reason = "跨学段关联，置信度降低"
    elif span <= 6:
        # 跨 2 个学段（如高中->小学）：可能错误
        penalty = 0.5
        reason = "跨多学段，存入 PREREQUISITE_CANDIDATE"
    else:
        # 跨度太大：几乎肯定错误
        penalty = 0.3
        reason = "年级跨度异常，存入 PREREQUISITE_CANDIDATE"

    relation['confidence'] *= penalty
    relation['grade_penalty_reason'] = reason

    # 置信度过低则降级为候选关系
    if relation['confidence'] < 0.6:
        relation['relation_type'] = 'PREREQUISITE_CANDIDATE'

    return relation
惩罚规则总结：
年级跨度	示例	置信度惩罚	处理方式
0-2（相邻）	高一→初三数学基础	×0.95	正常，保留 PREREQUISITE
3（跨1学段）	高二→初三	×0.9	合理但需确认
4-6（跨2学段）	高中→小学	×0.5	存入 PREREQUISITE_CANDIDATE
>6（跨度太大）	高三→小学一年级	×0.3	存入 PREREQUISITE_CANDIDATE
9.4 验证增强（新增）
9.4.1 循环依赖检测
问题：如果 A→B 且 B→A 同时存在，形成有向环，违背 DAG 要求。
def detect_cycles(prerequisites: list) -> list:
    """
    检测循环依赖
    返回: 环路列表
    """
    from collections import defaultdict, deque

    # 构建邻接表
    graph = defaultdict(list)
    for rel in prerequisites:
        graph[rel['from']].append(rel['to'])

    # 检测环（DFS）
    cycles = []
    visited = set()
    rec_stack = set()

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor, path + [node])
            elif neighbor in rec_stack:
                # 发现环
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [node, neighbor])

        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles

def resolve_cycles(prerequisites: list, cycles: list) -> list:
    """
    解决循环依赖：移除置信度最低的边
    """
    to_remove = set()
    for cycle in cycles:
        # 找到环中置信度最低的边
        cycle_edges = []
        for i in range(len(cycle) - 1):
            from_uri, to_uri = cycle[i], cycle[i+1]
            for rel in prerequisites:
                if rel['from'] == from_uri and rel['to'] == to_uri:
                    cycle_edges.append((rel['confidence'], from_uri, to_uri))
                    break
        if cycle_edges:
            # 移除置信度最低的边
            min_edge = min(cycle_edges)
            to_remove.add((min_edge[1], min_edge[2]))

    return [rel for rel in prerequisites if (rel['from'], rel['to']) not in to_remove]
9.4.2 孤立知识点检测
问题：没有任何 PREREQUISITE 关系，也没有被任何知识点依赖的知识点，可能是原子知识点或数据缺失。
def detect_isolated_kps(knowledge_points: list, prerequisites: list) -> dict:
    """
    检测孤立知识点
    返回: {'isolated': [...], 'potential_missing': [...]}
    """
    # 构建入度和出度
    in_degree = {kp.uri: 0 for kp in knowledge_points}
    out_degree = {kp.uri: 0 for kp in knowledge_points}

    for rel in prerequisites:
        out_degree[rel['from']] += 1
        in_degree[rel['to']] += 1

    isolated = []
    for kp in knowledge_points:
        if in_degree[kp.uri] == 0 and out_degree[kp.uri] == 0:
            isolated.append(kp)

    # 区分类型
    result = {
        'isolated': [kp for kp in isolated if kp.type in ['定义', '定理']],  # 真正孤立
        'potential_missing': [kp for kp in isolated if kp.type not in ['定义', '定理']]  # 可能缺失
    }
    return result
9.4.3 分层抽样评估（新增）
问题：按来源分层抽样，便于定位问题。
def stratified_sampling(prerequisites: list, sample_size: int = 100) -> dict:
    """
    按来源分层抽样
    """
    from collections import defaultdict
    import random

    # 按来源分组
    by_source = defaultdict(list)
    for rel in prerequisites:
        by_source[rel['source']].append(rel)

    # 分层抽样
    samples = {}
    for source, rels in by_source.items():
        n = max(1, int(sample_size * len(rels) / len(prerequisites)))
        samples[source] = random.sample(rels, min(n, len(rels)))

    return samples
评估标准细化：
类型	强合理	弱合理	不合理
定义依赖	定义中直接包含前置概念	定义中间接引用	匹配错误
LLM 推理	明确必须掌握	有较强辅助作用	完全无关
教材顺序	-	仅时间依赖	-
9.4.4 置信度校准（新增）
问题：模型输出置信度可能过于乐观或保守。
def calibrate_confidence(prerequisites: list, expert_scores: dict) -> dict:
    """
    置信度校准：对比专家打分
    expert_scores: {relation_id: expert_score_0_to_1}
    返回: {'overconfident': bool, 'calibration_factor': float}
    """
    model_scores = []
    human_scores = []

    for rel in prerequisites:
        if rel['id'] in expert_scores:
            model_scores.append(rel['confidence'])
            human_scores.append(expert_scores[rel['id']])

    if not model_scores:
        return {'overconfident': None, 'calibration_factor': 1.0}

    # 计算平均偏差
    avg_model = sum(model_scores) / len(model_scores)
    avg_human = sum(human_scores) / len(human_scores)

    calibration_factor = avg_human / avg_model if avg_model > 0 else 1.0

    return {
        'overconfident': avg_model > avg_human,
        'calibration_factor': calibration_factor,
        'avg_model_confidence': avg_model,
        'avg_human_score': avg_human
    }
9.5 图谱查询性能优化（智谱建议）
问题：多跳查询 [:PREREQUISITE*] 在大规模图谱（5万+节点）时可能变慢。
改进方案：
// 1. 深度限制：防止死循环或超长路径
MATCH (target:KnowledgePoint {uri: $uri})<-[r:PREREQUISITE*..10]-(prereq)
RETURN prereq, r

// 2. 学习路径查询（带深度限制）
MATCH (target:KnowledgePoint {uri: $target_uri})
MATCH path = (start)-[:PREREQUISITE*..10]->(target)
RETURN path ORDER BY LENGTH(path) ASC
离线预计算方案（可选）：
def compute_prerequisite_levels(knowledge_points):
    """
    离线计算每个知识点的"前置层级"属性
    存入节点，便于快速查询
    """
    for kp in knowledge_points:
        # BFS 计算最长前置路径长度
        max_depth = bfs_max_depth(kp, 'PREREQUISITE')
        kp.prerequisite_level = max_depth
        # 存入 Neo4j
        update_node_property(kp.uri, 'prerequisite_level', max_depth)
预计算后查询：
// 快速查询：直接按层级排序
MATCH (kp:KnowledgePoint {uri: $target_uri})
MATCH (prereq:KnowledgePoint)
WHERE prereq.prerequisite_level < kp.prerequisite_level
RETURN prereq ORDER BY prereq.prerequisite_level ASC
9.5 抽样测试量化标准
抽样方法:
● 从数学学科随机抽取 100-200 条 PREREQUISITE 关系
● 覆盖不同年级、不同类型（定义/公式/方法）
● 由内部人员（或参照教材、课程标准）判断是否合理
评估标准:
准确率 = 合理关系数 / 抽样总数
目标: ≥70%
调整策略（若低于阈值）:
1. 调整 Prompt 设计（增加 Few-Shot 示例）
2. 降低 temperature（如 0.2）
3. 提高置信度阈值（如 0.85）
9.6 图谱质量指标
指标	计算方法	目标值（demo）
前置关系覆盖率	有 PREREQUISITE 关系的知识点数 / 总知识点数	≥ 30%
DAG 合规率	无环的知识点比例（检测环的数量）	100%
平均前置链长度	所有知识点的最长前置路径长度的平均值	2~4 跳
年级倒置率	PREREQUISITE 关系出现高年级指向低年级的比例	≤ 5%（惩罚处理后）
置信度分布	高置信度（≥0.8）关系的占比	≥ 60%
9.7 Neo4j 部署配置
配置项	值
版本	Neo4j 社区版 4.4.x
部署	单机部署
内存	4G
存储	100G+
备份	CSV 文件全量备份
9.6 典型业务查询模板
// 1. 获取知识点的所有前置依赖（多跳）
MATCH (target:KnowledgePoint {uri: $uri})<-[r:PREREQUISITE*]-(prereq)
RETURN prereq, r

// 2. 获取知识点的直接教学顺序（前驱）
MATCH (target:KnowledgePoint {uri: $uri})<-[r:TEACHES_BEFORE]-(prev)
RETURN prev, r

// 3. 基于知识点集合，计算知识缺陷（未掌握的前置）
MATCH (kp:KnowledgePoint) WHERE kp.uri IN $mastered_kps
WITH COLLECT(kp) AS mastered
MATCH (target:KnowledgePoint {uri: $target_uri})<-[r:PREREQUISITE*]-(prereq)
WHERE NOT prereq IN mastered
RETURN prereq, r

// 4. 生成学习路径（拓扑排序）
MATCH (target:KnowledgePoint {uri: $target_uri})
MATCH path = (start)-[:PREREQUISITE*]->(target)
RETURN path ORDER BY LENGTH(path) ASC

// 5. 查询候选前置关系（待验证）
MATCH (kp:KnowledgePoint)-[r:PREREQUISITE_CANDIDATE]->(target)
WHERE r.confidence >= 0.6
RETURN kp, target, r
9.4 业务优先级（围绕 AI 引导式答疑）
优先级	业务场景	说明
P0	前置依赖查询	核心基础，方案核心目标
P1	知识点识别、知识缺陷诊断	Demo 必实现，支撑核心功能闭环
P2	学习路径推荐、年级/学科定位	可选迭代，核心跑通后补充

十、技术栈与开发规范
10.1 技术栈
技术项	选择	说明
Python 版本	3.10+	与主服务一致，避免环境冲突
TTL 解析库	rdflib	Python 生态最成熟的 RDF 解析库
Neo4j 驱动	neo4j-driver 4.4.x	与 Neo4j 版本严格匹配
LLM 调用	复用 Gateway	使用现有 core/gateway/factory.py
10.2 脚本目录结构
ai-edu-ai-service/scripts/kg_construction/
├── requirements-scripts.txt   # 脚本独立依赖，不污染主服务
├── clean_math_data.py         # 数学数据清洗
├── extract_textbook_info.py   # 教材信息提取
├── merge_math_data.py         # 数据合并
├── infer_prerequisites_llm.py # LLM 前置关系推理
├── merge_prerequisites.py     # 前置关系合并
├── import_math_to_neo4j.py    # Neo4j 导入
├── validate_prerequisites.py  # 自动验证脚本
└── logs/                      # 错误日志目录
10.3 LLM Gateway 配置
在 config/model_config.py 新增 scene 映射：
SCENE_MODEL_MAPPING = {
    # ... 现有配置
    "prerequisite_inference": {
        "provider": "zhipu",
        "model": "glm-4-flash",
        "temperature": 0.3,
    },
}

十一、风险与缓解
风险	缓解措施
v0.1 与 v3.0 数据不匹配	通过标签匹配，容忍部分缺失
LLM 推理不准确	置信度阈值过滤（<0.7 丢弃），≥70% 准确率满足 demo
年级推断不准确	提供人工修正接口（正式阶段）
数据量太大	按学科逐个处理，数学先行验证
relateTo 与 PREREQUISITE 语义混淆	严格区分，relateTo → RELATED_TO，LLM → PREREQUISITE

十二、数据更新机制（Demo 阶段）
方面	策略
基准数据	edukg 静态权威库，知识点永久冻结只读
维护规则	仅增量补充「题目-知识点」关联，不修改基准知识点
版本管理	CSV 文件命名区分（如 knowledge_points_v1.csv）
长期维护	Demo 阶段不考虑，正式迭代再设计

十三、任务执行与容错设计（工程化补充）
13.1 核心原则
● 幂等性：脚本可以重复执行，不会产生重复数据或重复调用 LLM
● 断点续传：任务中断后可从上次进度继续，避免从头开始
● 成本控制：对付费模型（DeepSeek-V3）的调用结果必须持久化，防止重复计费
● 版本管理：每次构建生成带版本号的数据快照，支持回滚
● 并发安全：防止误启动多进程，造成重复调用和数据冲突
13.2 状态管理（MySQL）
使用 MySQL 替代 SQLite，原因：
● 已有 MySQL 环境，无需额外安装
● 支持更好的并发性能
● 支持更丰富的运维工具
● 数据更安全（有备份机制）
13.2.0 数据库连接配置
# config/database.yaml
mysql:
  host: "localhost"
  port: 3306
  database: "ai_edu_kg"
  user: "${MYSQL_USER}"
  password: "${MYSQL_PASSWORD}"
  charset: "utf8mb4"
  pool_size: 5
# scripts/db_connection.py
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import yaml

class MySQLManager:
    def __init__(self, config_path: str = "config/database.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)['mysql']

        self.config = config
        self.pool = pymysql.ConnectionPool(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            charset=config['charset'],
            cursorclass=DictCursor,
            max_connections=config.get('pool_size', 5)
        )

    @contextmanager
    def get_connection(self):
        conn = self.pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self.pool.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

# 全局实例
db = MySQLManager()
状态表设计（MySQL 语法）：
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_edu_kg
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_edu_kg;

-- 处理状态表
CREATE TABLE IF NOT EXISTS processing_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL COMMENT '学科',
    version VARCHAR(50) NOT NULL COMMENT '版本号',
    step VARCHAR(100) NOT NULL COMMENT '步骤名称',
    batch_id VARCHAR(200) COMMENT '批次ID（LLM调用）',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/processing/completed/failed',
    result_file VARCHAR(500) COMMENT '结果文件路径',
    retry_count INT DEFAULT 0,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_step (subject, version, step, batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='处理状态表';

-- LLM 缓存表（付费模型结果）
CREATE TABLE IF NOT EXISTS llm_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cache_key VARCHAR(64) UNIQUE NOT NULL COMMENT 'SHA256 哈希',
    provider VARCHAR(50) NOT NULL COMMENT '模型提供商',
    model VARCHAR(50) NOT NULL COMMENT '模型名称',
    batch_uris JSON NOT NULL COMMENT '知识点 URI 列表（JSON 数组）',
    response JSON NOT NULL COMMENT 'LLM 响应（JSON）',
    tokens_used INT DEFAULT 0,
    cost_cents INT DEFAULT 0 COMMENT '成本（分）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cache_key (cache_key),
    INDEX idx_provider_model (provider, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM 缓存表';

-- 成本累积表
CREATE TABLE IF NOT EXISTS cost_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    total_tokens INT DEFAULT 0,
    total_cost_cents INT DEFAULT 0,
    call_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_provider (subject, version, provider, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成本累积表';

-- ========== 两层状态表（章节 + 子批次）==========

-- 章节状态表（业务层）
CREATE TABLE IF NOT EXISTS chapter_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    chapter_id VARCHAR(200) NOT NULL COMMENT '如 math_chapter3_一元二次方程',
    chapter_name VARCHAR(200) NOT NULL,
    total_kps INT DEFAULT 0 COMMENT '该章节知识点总数',
    processed_kps INT DEFAULT 0 COMMENT '已处理知识点数',
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/processing/completed/skipped/failed',
    priority INT DEFAULT 0 COMMENT '优先级（0=普通，1=优先处理）',
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_chapter (subject, version, chapter_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='章节状态表';

-- 子批次状态表（技术层）
CREATE TABLE IF NOT EXISTS subbatch_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    chapter_id VARCHAR(200) NOT NULL,
    batch_id VARCHAR(200) NOT NULL COMMENT '如 math_chapter3_batch1',
    kp_uris JSON NOT NULL COMMENT '知识点 URI 列表（JSON 数组）',
    kp_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/processing/completed/failed',
    cache_key VARCHAR(64) COMMENT 'SHA256 缓存键',
    result_file VARCHAR(500) COMMENT '结果文件路径',
    retry_count INT DEFAULT 0,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_batch (subject, version, batch_id),
    INDEX idx_chapter (chapter_id),
    INDEX idx_status (status),
    FOREIGN KEY (subject, version, chapter_id)
        REFERENCES chapter_state(subject, version, chapter_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='子批次状态表';

-- 进度视图（便于查询）
CREATE OR REPLACE VIEW progress_view AS
SELECT
    subject,
    version,
    COUNT(*) as total_chapters,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_chapters,
    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_chapters,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_chapters,
    ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 1) as progress_percent
FROM chapter_state
GROUP BY subject, version;

-- 失败批次表
CREATE TABLE IF NOT EXISTS failed_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    batch_id VARCHAR(200) NOT NULL,
    batch_uris JSON NOT NULL,
    error_type VARCHAR(50) NOT NULL COMMENT '错误类型分类',
    error_message TEXT,
    retry_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/retrying/resolved/abandoned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_retry_at DATETIME,
    INDEX idx_status (status),
    INDEX idx_error_type (error_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='失败批次表';
13.2.1 StateDB 类（MySQL 版）
# scripts/state_db.py
from db_connection import db
from typing import Optional, List, Dict, Any
import json

class StateDB:
    """MySQL 状态管理类"""

    def __init__(self):
        self.db = db

    # ========== 章节状态 ==========

    def get_chapter_status(self, chapter_id: str) -> Optional[str]:
        """获取章节状态"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM chapter_state
                    WHERE chapter_id = %s
                """, (chapter_id,))
                result = cursor.fetchone()
                return result['status'] if result else None

    def mark_chapter_processing(self, chapter_id: str):
        """标记章节处理中"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'processing', started_at = NOW()
                    WHERE chapter_id = %s
                """, (chapter_id,))
            conn.commit()

    def mark_chapter_completed(self, chapter_id: str):
        """标记章节完成"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'completed', completed_at = NOW()
                    WHERE chapter_id = %s
                """, (chapter_id,))
            conn.commit()

    def mark_chapter_failed(self, chapter_id: str, error: str = ""):
        """标记章节失败"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'failed', error_message = %s, completed_at = NOW()
                    WHERE chapter_id = %s
                """, (error, chapter_id))
            conn.commit()

    def skip_chapter(self, chapter_id: str, reason: str = ""):
        """跳过章节"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'skipped', error_message = %s, completed_at = NOW()
                    WHERE chapter_id = %s
                """, (f"手动跳过: {reason}", chapter_id))
            conn.commit()

    # ========== 子批次状态 ==========

    def is_subbatch_completed(self, batch_id: str) -> bool:
        """检查子批次是否完成"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM subbatch_state
                    WHERE batch_id = %s
                """, (batch_id,))
                result = cursor.fetchone()
                return result and result['status'] == 'completed'

    def mark_subbatch_completed(self, batch_id: str, cache_key: str, result_file: str):
        """标记子批次完成"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE subbatch_state
                    SET status = 'completed',
                        cache_key = %s,
                        result_file = %s,
                        completed_at = NOW()
                    WHERE batch_id = %s
                """, (cache_key, result_file, batch_id))
            conn.commit()

    def mark_subbatch_failed(self, batch_id: str, error: str):
        """标记子批次失败"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE subbatch_state
                    SET status = 'failed',
                        error_message = %s,
                        retry_count = retry_count + 1
                    WHERE batch_id = %s
                """, (error, batch_id))
            conn.commit()

    # ========== LLM 缓存 ==========

    def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """获取缓存的 LLM 响应"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT response, result_file FROM llm_cache
                    WHERE cache_key = %s
                """, (cache_key,))
                result = cursor.fetchone()
                if result:
                    return {
                        'response': result['response'],
                        'result_file': result['result_file']
                    }
                return None

    def save_cache(self, cache_key: str, provider: str, model: str,
                   batch_uris: List[str], response: Dict,
                   tokens: int = 0, cost: int = 0, result_file: str = ""):
        """保存 LLM 缓存"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO llm_cache
                    (cache_key, provider, model, batch_uris, response, tokens_used, cost_cents, result_file)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    response = VALUES(response),
                    tokens_used = VALUES(tokens_used),
                    cost_cents = VALUES(cost_cents)
                """, (cache_key, provider, model,
                      json.dumps(batch_uris), json.dumps(response),
                      tokens, cost, result_file))
            conn.commit()

    # ========== 进度查询 ==========

    def get_progress(self, subject: str, version: str) -> Dict:
        """获取处理进度"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM progress_view
                    WHERE subject = %s AND version = %s
                """, (subject, version))
                return cursor.fetchone() or {}

    def get_failed_chapters(self, subject: str, version: str) -> List[Dict]:
        """获取失败章节"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT chapter_id, chapter_name, error_message
                    FROM chapter_state
                    WHERE subject = %s AND version = %s AND status = 'failed'
                """, (subject, version))
                return cursor.fetchall()

    # ========== 成本追踪 ==========

    def track_cost(self, subject: str, version: str, provider: str,
                   model: str, tokens: int, cost: int):
        """记录成本"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO cost_tracking
                    (subject, version, provider, model, total_tokens, total_cost_cents, call_count)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                    total_tokens = total_tokens + VALUES(total_tokens),
                    total_cost_cents = total_cost_cents + VALUES(total_cost_cents),
                    call_count = call_count + 1,
                    updated_at = NOW()
                """, (subject, version, provider, model, tokens, cost))
            conn.commit()
13.2.2 按课程单元划分
设计原则：重跑最小单位 = 章节（业务认知），内部可拆分子批次（技术限制）。
def process_by_chapter(subject: str, version: str, state_db):
    """
    按章节处理，支持断点续传
    """
    chapters = get_chapters(subject)

    for chapter in chapters:
        chapter_id = f"{subject}_{chapter['id']}"

        # 1. 检查章节状态
        chapter_status = state_db.get_chapter_status(chapter_id)
        if chapter_status == 'completed':
            logging.info(f"跳过已完成章节: {chapter['name']}")
            continue
        if chapter_status == 'skipped':
            logging.info(f"跳过已标记跳过: {chapter['name']}")
            continue

        # 2. 标记章节处理中
        state_db.mark_chapter_processing(chapter_id)

        # 3. 获取该章节知识点
        kps = get_knowledge_points_in_chapter(chapter)

        # 4. 按 token 限制拆分子批次
        sub_batches = split_by_token_limit(kps, max_tokens=4000)

        chapter_failed = False
        for i, sub_batch in enumerate(sub_batches):
            batch_id = f"{chapter_id}_batch{i+1}"

            # 检查子批次状态
            if state_db.is_subbatch_completed(batch_id):
                continue

            # 处理子批次
            try:
                result = process_subbatch(sub_batch, batch_id, state_db)
                state_db.mark_subbatch_completed(batch_id, result['cache_key'], result['file'])
            except Exception as e:
                state_db.mark_subbatch_failed(batch_id, str(e))
                chapter_failed = True
                break

        # 5. 更新章节状态
        if chapter_failed:
            state_db.mark_chapter_failed(chapter_id)
        else:
            state_db.mark_chapter_completed(chapter_id)

    return state_db.get_progress(subject, version)
13.2.3 进度可视化
def show_progress(subject: str, version: str, state_db: StateDB):
    """
    显示处理进度
    """
    progress = state_db.get_progress(subject, version)

    if not progress:
        print("暂无进度数据")
        return

    print(f"\n{'='*50}")
    print(f"学科: {progress['subject']} | 版本: {progress['version']}")
    print(f"进度: {progress['progress_percent']}% ({progress['completed_chapters']}/{progress['total_chapters']} 章节)")
    print(f"处理中: {progress['processing_chapters']} | 失败: {progress['failed_chapters']}")
    print(f"{'='*50}\n")

    # 显示失败章节
    failed = state_db.get_failed_chapters(subject, version)

    if failed:
        print("失败章节:")
        for f in failed:
            print(f"  - {f['chapter_name']}: {f['error_message']}")

# 命令行入口
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--show-progress', action='store_true')
    parser.add_argument('--retry-failed', action='store_true')
    parser.add_argument('--skip-chapter', type=str, help='跳过指定章节')
    args = parser.parse_args()

    if args.show_progress:
        show_progress(subject, version, state_db)
    elif args.retry_failed:
        retry_failed_chapters(subject, version, state_db)
    elif args.skip_chapter:
        state_db.skip_chapter(args.skip_chapter)
13.2.4 手动跳过章节
def skip_chapter(state_db: StateDB, chapter_id: str, reason: str = ""):
    """
    手动跳过某章节（不处理）
    """
    state_db.skip_chapter(chapter_id, reason)
    logging.info(f"已跳过章节: {chapter_id}")
13.2.5 原子性操作保证
问题：如果结果文件写入成功，但状态更新失败怎么办？
解决方案：使用 MySQL 事务 + 两阶段提交。
def process_subbatch_with_atomic(sub_batch, batch_id, state_db: StateDB, cache_dir, provider, model):
    """
    原子性处理子批次（MySQL 事务）
    """
    cache_key = compute_cache_key(sub_batch)

    # 阶段1: 检查缓存
    cached = state_db.get_cached_response(cache_key)
    if cached:
        return {'cache_key': cache_key, 'file': cached['result_file']}

    # 阶段2: 调用 LLM
    result = call_llm(sub_batch)

    # 阶段3: 保存结果文件
    result_file = f"{cache_dir}/{cache_key}.json"
    with open(result_file, 'w') as f:
        json.dump(result, f)

    # 阶段4: 原子性更新（MySQL 事务）
    try:
        with state_db.db.transaction() as conn:
            with conn.cursor() as cursor:
                # 4.1 保存缓存记录
                cursor.execute("""
                    INSERT INTO llm_cache
                    (cache_key, provider, model, batch_uris, response, created_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                """, (cache_key, provider, model,
                      json.dumps([kp.uri for kp in sub_batch]),
                      json.dumps(result)))

                # 4.2 更新子批次状态
                cursor.execute("""
                    UPDATE subbatch_state
                    SET status = 'completed',
                        cache_key = %s,
                        result_file = %s,
                        completed_at = NOW()
                    WHERE batch_id = %s
                """, (cache_key, result_file, batch_id))

    except Exception as e:
        # 事务自动回滚
        logging.error(f"事务失败: {e}")
        raise

    return {'cache_key': cache_key, 'file': result_file}
关键保证：
● 事务失败 → 缓存未记录 → 下次重跑会重新调用（可能重复付费）
● 事务成功 → 缓存已记录 → 下次重跑直接使用缓存
更安全的做法：先写缓存，再处理业务状态。
def safer_process_subbatch(sub_batch, batch_id, state_db, cache_dir):
    """
    更安全的处理顺序：先保存缓存，再更新业务状态
    """
    cache_key = compute_cache_key(sub_batch)

    # 1. 调用 LLM
    result = call_llm(sub_batch)

    # 2. 立即保存缓存（独立事务，优先保证）
    result_file = save_cache_file(cache_dir, cache_key, result)
    state_db.save_cache(cache_key, result, result_file)  # 独立事务

    # 3. 更新业务状态（即使失败，缓存已保存）
    state_db.mark_subbatch_completed(batch_id, cache_key, result_file)

    return result
13.3 进程锁机制（跨平台支持）
防止误启动多进程或意外中断后重复启动。
13.3.1 文件锁（portalocker，推荐）
# pip install portalocker

import portalocker
import os

class ProcessLock:
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.lock_fd = None

    def acquire(self, timeout: int = 0) -> bool:
        """获取锁"""
        self.lock_fd = open(self.lock_file, 'w')
        try:
            portalocker.lock(self.lock_fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
            self.lock_fd.write(f"pid={os.getpid()}\n")
            return True
        except portalocker.LockException:
            self.lock_fd.close()
            return False

    def release(self):
        if self.lock_fd:
            portalocker.unlock(self.lock_fd)
            self.lock_fd.close()

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Another process is running")
        return self

    def __exit__(self, *args):
        self.release()
13.3.2 MySQL 表锁（替代方案）
class MySQLLock:
    """基于 MySQL 的分布式锁"""

    def __init__(self, db: MySQLManager):
        self.db = db
        self._ensure_lock_table()

    def _ensure_lock_table(self):
        """确保锁表存在"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS process_lock (
                        lock_name VARCHAR(100) PRIMARY KEY,
                        pid INT NOT NULL,
                        hostname VARCHAR(100),
                        acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_acquired (acquired_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
            conn.commit()

    def acquire(self, lock_name: str, timeout_seconds: int = 3600) -> bool:
        """
        获取锁
        timeout_seconds: 锁超时时间（防止死锁）
        """
        import socket
        hostname = socket.gethostname()
        pid = os.getpid()

        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                # 先清理过期锁
                cursor.execute("""
                    DELETE FROM process_lock
                    WHERE lock_name = %s
                    AND acquired_at < DATE_SUB(NOW(), INTERVAL %s SECOND)
                """, (lock_name, timeout_seconds))

                # 尝试获取锁
                try:
                    cursor.execute("""
                        INSERT INTO process_lock (lock_name, pid, hostname, acquired_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (lock_name, pid, hostname))
                    conn.commit()
                    return True
                except pymysql.IntegrityError:
                    # 锁已被占用
                    conn.rollback()
                    return False

    def release(self, lock_name: str):
        """释放锁"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM process_lock
                    WHERE lock_name = %s AND pid = %s
                """, (lock_name, os.getpid()))
            conn.commit()

    def get_lock_info(self, lock_name: str) -> Optional[Dict]:
        """获取锁信息"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT pid, hostname, acquired_at
                    FROM process_lock
                    WHERE lock_name = %s
                """, (lock_name,))
                return cursor.fetchone()

# 使用示例
def run_pipeline_with_lock(subject: str):
    lock = MySQLLock(db)
    lock_name = f"kg_pipeline_{subject}"

    if not lock.acquire(lock_name):
        info = lock.get_lock_info(lock_name)
        raise RuntimeError(
            f"Another process is running (pid={info['pid']}, host={info['hostname']})"
        )

    try:
        # 执行流程
        process_subject(subject)
    finally:
        lock.release(lock_name)
13.4 LLM 推理断点续传
步骤级断点：
def process_llm_batches(candidates, state_db, cache_dir):
    """带缓存的 LLM 批处理"""
    for batch in candidates:
        batch_key = batch_id(batch)

        # 检查状态
        status = state_db.get_status(batch_key)
        if status == 'completed':
            logging.info(f"跳过已完成批次: {batch_key}")
            continue

        # 检查缓存
        cache_key = get_cache_key(batch, prompt_version='v2')
        cached = state_db.get_cached_response(cache_key)
        if cached:
            logging.info(f"使用缓存结果: {cache_key}")
            state_db.mark_completed(batch_key, cached['result_file'])
            continue

        # 标记处理中
        state_db.mark_processing(batch_key)

        try:
            result = call_llm(batch)
            # 保存缓存
            cache_path = save_cache(cache_key, result)
            state_db.mark_completed(batch_key, cache_path)
            # 记录成本
            state_db.track_cost(result['tokens'], result['cost'])
        except Exception as e:
            retry = state_db.get_retry_count(batch_key) + 1
            if retry < MAX_RETRIES:
                state_db.mark_pending(batch_key, retry_count=retry)
            else:
                state_db.mark_failed(batch_key, error=str(e))
                # 写入失败日志
                save_failed_batch(batch, str(e))
13.5 成本控制与监控
实时成本累积：
# 配置文件 config/pipeline.yaml
cost_limits:
  daily_limit_cents: 5000   # 日预算 50 元
  total_limit_cents: 20000  # 总预算 200 元
  warning_threshold: 0.7    # 70% 时告警

alert:
  enabled: true
  method: "console"         # 个人项目：控制台告警
  # method: "email"         # 可扩展邮件通知
成本检查函数：
def check_cost_limit(state_db, subject: str) -> bool:
    """检查是否超出成本限制"""
    current_cost = state_db.get_total_cost(subject)
    config = load_config()

    if current_cost >= config['cost_limits']['total_limit_cents']:
        logging.error(f"已超出总预算 {current_cost} 分")
        return False

    if current_cost >= config['cost_limits']['daily_limit_cents']:
        logging.warning(f"已超出日预算 {current_cost} 分")

    if current_cost >= config['cost_limits']['total_limit_cents'] * config['alert']['warning_threshold']:
        logging.warning(f"成本已达 {current_cost} 分，接近预算上限")

    return True

def call_llm_with_cost_check(batch, state_db):
    """带成本检查的 LLM 调用"""
    if not check_cost_limit(state_db, batch['subject']):
        raise RuntimeError("超出成本限制，停止调用")
    return call_llm(batch)
13.6 缓存策略（SHA256）
改进：使用 SHA256 替代 MD5，避免碰撞风险：
import hashlib
import json

def get_cache_key(batch, prompt_version: str, model: str) -> str:
    """生成唯一缓存键"""
    ids = sorted([kp.uri for kp in batch])
    key_dict = {
        'uris': ids,
        'prompt_version': prompt_version,
        'model': model,
        # 可选：加入 prompt template hash
    }
    key_str = json.dumps(key_dict, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()[:32]
13.7 版本控制与数据快照
目录结构：
data/
├── versions/
│   ├── v1_20250328/
│   │   ├── math_knowledge_points.csv
│   │   ├── math_prerequisites.csv
│   │   ├── math_prerequisite_candidates.csv
│   │   ├── math_teaches_before.csv
│   │   ├── math_related_to.csv      # relateTo 数据
│   │   ├── math_sub_category.csv    # subCategory 数据
│   │   ├── state.db                 # SQLite 状态文件
│   │   └── manifest.json
│   └── v2_20250329/
│       └── ...
├── cache/
│   └── llm_responses/   # 缓存与版本无关，可跨版本复用
├── state/
│   └── math.lock        # 进程锁文件
│   └── failed_batches/  # 失败批次日志
└── config/
    └── pipeline.yaml    # 配置文件
Manifest 记录：
{
  "version": "v1_20250328",
  "subject": "math",
  "source_data": {
    "ttl_version": "v0.1",
    "main_ttl_version": "v3.0"
  },
  "generated_at": "2025-03-28T10:30:00",
  "stats": {
    "total_kps": 4490,
    "prerequisites": 1234,
    "prerequisite_candidates": 567,
    "teaches_before": 890,
    "related_to": 9870,
    "sub_category": 328
  },
  "cost": {
    "total_tokens": 12345,
    "total_cost_cents": 1234,
    "calls_by_provider": {"zhipu": 100, "deepseek": 50}
  },
  "llm_config": {
    "providers": ["zhipu", "deepseek"],
    "model_versions": {"zhipu": "glm-4-flash", "deepseek": "deepseek-V3"},
    "temperature": 0.3,
    "prompt_version": "v2"
  }
}
13.8 Graceful Shutdown
手动中断处理：
import signal
import sys

class GracefulShutdown:
    def __init__(self, state_db):
        self.state_db = state_db
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)

    def _handler(self, signum, frame):
        logging.warning(f"收到中断信号 {signum}, 准备优雅退出...")
        self.shutdown_requested = True

    def check(self) -> bool:
        """检查是否需要中断"""
        if self.shutdown_requested:
            logging.info("保存当前状态，准备退出...")
            self.state_db.save_pending_states()
            return True
        return False

def process_with_shutdown(candidates, state_db):
    shutdown = GracefulShutdown(state_db)
    for batch in candidates:
        if shutdown.check():
            logging.info("用户中断，已保存进度，下次可继续")
            sys.exit(0)
        process_batch(batch, state_db)
13.9 幂等性设计
Neo4j 导入使用 MERGE：
// 知识点节点（基于 uri 唯一）
MERGE (kp:KnowledgePoint {uri: $uri})
SET kp.name = $name,
    kp.subject = $subject,
    kp.grade = $grade,
    kp.type = $type

// 前置关系（基于端点和类型唯一）
MATCH (from:KnowledgePoint {uri: $from_uri})
MATCH (to:KnowledgePoint {uri: $to_uri})
MERGE (from)-[r:PREREQUISITE]->(to)
SET r.confidence = $confidence,
    r.source = $source,
    r.evidence_types = $evidence_types
13.10 重试与错误恢复
错误类型	重试次数	退避策略	处理方式
LLM 调用超时	2	指数退避（1s, 2s）	状态标记 pending，下次继续
LLM 返回格式错误	1	立即重试	解析失败记录日志
网络临时故障	3	固定间隔 2s	自动重试
成本超限	0	停止调用	抛出异常，记录状态
数据解析错误	0	记录跳过	写入 failed_batches
错误日志结构化（智谱建议）
问题：原方案将失败批次写入日志文件，难以批量重试。
改进：将失败批次信息写入 SQLite 表，便于开发一键重试脚本。
-- 失败批次表（新增）
CREATE TABLE failed_batches (
    id INTEGER PRIMARY KEY,
    subject TEXT NOT NULL,
    version TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    batch_uris TEXT NOT NULL,        -- JSON 数组
    error_type TEXT NOT NULL,        -- 错误类型分类
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_retry_at TIMESTAMP,
    status TEXT DEFAULT 'pending'    -- pending/retrying/resolved/abandoned
);

-- 一键重试脚本
def retry_failed_batches(state_db, max_retries=3):
    """重试所有待处理或重试中的失败批次"""
    failed = state_db.query("""
        SELECT * FROM failed_batches
        WHERE status IN ('pending', 'retrying')
        AND retry_count < ?
    """, (max_retries,))

    for batch in failed:
        try:
            state_db.update_failed_batch(batch['id'], status='retrying')
            result = call_llm(json.loads(batch['batch_uris']))
            # 成功：标记为 resolved
            state_db.update_failed_batch(
                batch['id'],
                status='resolved',
                result_file=save_result(result)
            )
        except Exception as e:
            state_db.update_failed_batch(
                batch['id'],
                retry_count=batch['retry_count'] + 1,
                error_message=str(e)
            )
错误类型分类：
错误类型	说明	处理建议
json_parse_error	LLM 返回格式损坏	检查 Prompt，增加格式修复
token_limit_exceeded	输入超 Token 限制	减小批次大小
timeout	网络或 LLM 超时	增加超时时间，重试
rate_limit	API 调用频率限制	增加等待时间
network_error	网络临时故障	重试
unknown	其他错误	检查日志，人工介入
13.10.1 动态批大小调整（新增）
问题：不同章节知识点数量差异大，固定批大小可能导致 Token 超限。
import tiktoken

def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """预估文本 Token 数"""
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def build_dynamic_batch(knowledge_points: list, max_tokens: int = 4000) -> list:
    """
    动态构建批次，确保不超过 Token 限制
    """
    batches = []
    current_batch = []
    current_tokens = 0

    # Prompt 模板基础 Token 数
    base_prompt = get_prompt_template()
    base_tokens = estimate_tokens(base_prompt)

    for kp in knowledge_points:
        kp_text = f"| {kp.name} | {kp.type} | {kp.definition} |"
        kp_tokens = estimate_tokens(kp_text)

        if current_tokens + kp_tokens + base_tokens > max_tokens:
            # 当前批次已满，开始新批次
            if current_batch:
                batches.append(current_batch)
            current_batch = [kp]
            current_tokens = kp_tokens
        else:
            current_batch.append(kp)
            current_tokens += kp_tokens

    if current_batch:
        batches.append(current_batch)

    return batches
13.10.2 关系去重与合并（新增）
问题：多个来源可能生成相同关系，需要合并去重。
def merge_duplicate_relations(relations: list) -> list:
    """
    合并重复关系，取最高置信度 + 合并证据
    """
    merged = {}
    for rel in relations:
        key = (rel["from"], rel["to"], rel["relation_type"])
        if key not in merged:
            merged[key] = rel.copy()
        else:
            # 保留更高置信度
            if rel["confidence"] > merged[key]["confidence"]:
                merged[key]["confidence"] = rel["confidence"]
            # 合并证据/来源
            merged[key]["evidence_types"] = list(set(
                merged[key]["evidence_types"] + rel["evidence_types"]
            ))
            merged[key]["source"] = ",".join(set(
                merged[key]["source"].split(",") + rel["source"].split(",")
            ))

    return list(merged.values())
13.11 脚本执行流程
def run_math_pipeline():
    subject = "math"
    version = generate_version()
    config = load_config()

    # 进程锁
    with ProcessLock(f"data/state/{subject}.lock"):
        state_db = StateDB(f"data/versions/{version}/state.db")

        # Step 1: 数据解析（幂等）
        if state_db.get_step_status("parse_ttl") != "completed":
            kps = parse_ttl(f"data/ttl/{subject}.ttl")
            save_kps(kps, version)
            state_db.mark_step_completed("parse_ttl")

        # Step 2: 教材匹配（幂等）
        if state_db.get_step_status("textbook_match") != "completed":
            kps = load_kps(version)
            enriched_kps = match_textbook(kps)
            save_kps(enriched_kps, version)
            state_db.mark_step_completed("textbook_match")

        # Step 3: 定义依赖抽取（幂等）
        if state_db.get_step_status("definition_deps") != "completed":
            def_deps = extract_definition_dependencies(load_kps(version))
            save_def_deps(def_deps, version)
            state_db.mark_step_completed("definition_deps")

        # Step 4: 关系数据提取（幂等）
        if state_db.get_step_status("extract_relations") != "completed":
            relations = extract_relations(subject)
            save_relations(relations, version)
            state_db.mark_step_completed("extract_relations")

        # Step 5: LLM 推理（断点续传 + 成本控制）
        candidates = generate_candidates(load_kps(version), load_def_deps(version))
        process_llm_batches_with_cache(candidates, state_db, config)

        # Step 6: 证据融合（幂等）
        if state_db.get_step_status("fuse") != "completed":
            prerequisites = fuse(load_def_deps(version), load_llm_results(version))
            save_prerequisites(prerequisites, version)
            state_db.mark_step_completed("fuse")

        # Step 7: Neo4j 导入（幂等 MERGE）
        import_to_neo4j(version)

        # 生成 manifest
        generate_manifest(version, state_db)

        logging.info(f"Pipeline 完成: {version}")

十四、成本估算与优化策略
14.1 数学学科成本估算（智谱修正）
智谱指出：数学知识点 4490 个，批大小 50，理论上应该是 4490/50 ≈ 90 次调用，而非 1000 次。
修正后的计算公式：
批次调用次数 = 知识点总数 / 批次大小
数学: 4490 / 50 ≈ 90 次

考虑多模型投票（2个模型）: 90 × 2 = 180 次（GLM + DeepSeek）
考虑失败重试（平均10%）：180 × 1.1 ≈ 200 次

但 GLM-4-flash 免费，实际付费调用仅为 DeepSeek 部分
修正后的成本估算：
处理阶段	LLM 调用次数	模型	单次成本	预估成本
定义依赖抽取	0	-	-	0 元
LLM 推理（GLM）	~90	GLM-4-flash	免费	0 元
LLM 推理（DeepSeek投票）	~90	DeepSeek-V3	~0.01元/批	~0.9 元
重试（约10%）	~10	DeepSeek-V3	~0.01元/批	~0.1 元
数学学科总计	~200 次（含免费）	-	-	约 1-2 元
重要：GLM-4-flash 免费，是主力模型。DeepSeek 仅用于投票验证，成本极低。
14.2 成本优化措施
1. 优先免费模型：GLM-4-flash 作为主力，免费
2. 付费模型仅在必要时：验证高价值关系（投票阶段）
3. 结果缓存：所有调用持久化，避免重复
4. 批量处理：减少调用次数
5. 成本监控：实时累积，超限告警
6. GLM 多轮验证：免费模型可多轮验证，提升准确率而不增加成本
14.3 全学科成本预估（修正）
学科	知识点数	批次调用次数	预估成本（DeepSeek）
数学	4,490	~90	~1-2 元
物理	3,385	~68	~0.7-1.5 元
化学	5,718	~115	~1-2.5 元
生物	15,209	~305	~3-6 元
其他 5 学科	~27,000	~540	~5-10 元
总计	56,391	~1,120	约 10-20 元
注：GLM-4-flash 调用约 1,120 次（免费），DeepSeek 调用约 1,120 次（付费约 10-20 元）。
| 物理 | 3,385 | ~700 | 3-8 元 |
| 化学 | 5,718 | ~1,200 | 6-12 元 |
| 生物 | 15,209 | ~3,000 | 15-30 元 |

十五、风险与缓解（更新）
风险	缓解措施
任务中断导致重复工作	断点续传 + SQLite 状态记录
付费模型重复调用	SHA256 缓存 + 状态表
脚本误删已有数据	版本目录隔离 + Neo4j MERGE
版本混乱	独立目录 + manifest 元数据
处理状态丢失	SQLite 事务保护
成本超预算	实时监控 + 告警 + 限制
误启动多进程	进程锁机制
用户手动中断无保存	Graceful Shutdown
知识点类型缺失	CSV 必须导出 type 列
relateTo 语义混淆	严格区分 RELATED_TO vs PREREQUISITE

十六、技术栈更新
技术项	选择	说明
状态存储	MySQL	已有环境，事务支持，并发性能好
缓存键算法	SHA256	替代 MD5，避免碰撞
进程锁	portalocker / MySQL 表锁	跨平台文件锁 或 分布式锁
配置格式	YAML	外置配置，灵活调整
错误日志	MySQL 表	结构化存储，便于重试脚本
告警方式	控制台日志	个人项目首选
16.1 数据库依赖
# requirements-scripts.txt 新增
pymysql>=1.0.2
pyyaml>=6.0
portalocker>=2.7.0

十七、脚本目录结构更新
ai-edu-ai-service/scripts/kg_construction/
├── requirements-scripts.txt
├── config/
│   ├── pipeline.yaml           # 流程配置
│   └── database.yaml           # MySQL 配置
├── db_connection.py            # 新增：MySQL 连接管理
├── state_db.py                 # 新增：状态管理类
├── clean_math_data.py
├── extract_textbook_info.py
├── merge_math_data.py
├── extract_relations.py        # 提取 relateTo/subCategory
├── infer_teaches_before.py
├── extract_definition_dependencies.py
├── infer_prerequisites_llm.py
├── fuse_prerequisites.py
├── import_math_to_neo4j.py
├── validate_prerequisites.py
├── state_manager.py            # 新增：SQLite 状态管理
├── cache_manager.py            # 新增：LLM 缓存管理
├── cost_tracker.py             # 新增：成本监控
├── process_lock.py             # 新增：进程锁
├── graceful_shutdown.py        # 新增：优雅退出
├── run_math_pipeline.py        # 新增：主流程脚本
└── logs/
    └── failed_batches/         # 新增：失败批次日志