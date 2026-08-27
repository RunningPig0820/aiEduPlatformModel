# 分学科处理策略（续）
> summary: 学科分三类：强逻辑链学科(数理化生)建 PREREQUISITE，语言学科(英语)建语法词汇层级，主题关联学科(历史语文地理政治)建主题分类。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-分学科处理策略-2.md
> 类别：数据关联

---

### 八、分学科处理策略（学科类型划分）（续）

> 检索摘要：学科分三类：强逻辑链学科(数理化生)建 PREREQUISITE，语言学科(英语)建语法词汇层级，主题关联学科(历史语文地理政治)建主题分类。

### 8.4 分学科细化策略（新增）
> 检索摘要：分学科细化策略：强逻辑链学科定制停用词+物理公式符号前置，英语 GRADED 难度递进，主题学科 THEME 主题聚类。

#### 8.4.1 强逻辑链学科（数理化生）
> 检索摘要：强逻辑链学科定制学科停用词表（数学/物理/化学/生物），物理公式符号依赖特殊处理提取符号含义前置。

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

#### 8.4.2 语言学科（英语）
> 检索摘要：英语 GRADED 关系表示难度递进（词汇→短语→句型）而非学习依赖，按词汇分级与语法层级构建递进关系。

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

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§八、分学科处理策略（学科类型划分）（续））
