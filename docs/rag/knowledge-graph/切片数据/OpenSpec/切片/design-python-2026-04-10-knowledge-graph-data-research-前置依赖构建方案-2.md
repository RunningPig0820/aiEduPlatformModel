# 前置依赖构建方案（续）
> summary: 前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-前置依赖构建方案-2.md
> 类别：数据关联

---

### 五、前置依赖关系构建方案（多证据融合）（续）

> 检索摘要：前置依赖构建核心原则：教学顺序≠学习依赖，教材顺序存 TEACHES_BEFORE，真正学习依赖存 PREREQUISITE。

### 5.4 定义依赖抽取（强证据）- 改进版
> 检索摘要：定义依赖抽取改进：原简单字符串匹配易误报（"指数"匹配"指数函数"），改进为词边界匹配+停用词+同义词+概念层级。

从知识点的定义文本中提取关键词，匹配其他知识点名称。
智谱建议改进：原方案使用简单字符串匹配（if other_kp.name in kp.definition），容易产生误报（如"指数"匹配"指数函数"、"合"匹配"集合"）。

#### 5.4.1 词边界匹配 + 停用词表
> 检索摘要：定义依赖用词边界匹配+停用词表（过滤方法/概念等泛化词）+定义文本预处理，降低子串误报，保证完整词匹配。

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

#### 5.4.2 知识点类型标准化
> 检索摘要：知识点类型标准化映射：公理/定律/原理统一为定理，方程/表达式归公式，术语归定义，特征/属性归性质。

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

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§五、前置依赖关系构建方案（多证据融合）（续））
