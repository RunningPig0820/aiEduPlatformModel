# 前置依赖构建方案（续）
> summary: 前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-前置依赖构建方案-3.md
> 类别：数据关联

---

### 五、前置依赖关系构建方案（多证据融合）（续）

> 检索摘要：前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。

#### 5.4.3 同义词映射（新增）
> 检索摘要：定义中用同义词而非精确知识点名（方程vs等式），按学科建同义词映射表扩展匹配模式，提高定义依赖召回。

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

#### 5.4.4 概念层级依赖（新增）
> 检索摘要：概念层级依赖：整式方程是方程子类，定义出现整式方程则间接依赖方程，沿 CONCEPT_HIERARCHY 向上追溯父类。

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

### 5.5 LLM 多模型投票 - 改进版
> 检索摘要：LLM 前置推断用 GLM-4-flash + DeepSeek 两模型投票，temperature 0.3、批大小10、滑动窗口携带前序章节知识点上下文。

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

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§五、前置依赖关系构建方案（多证据融合）（续））
