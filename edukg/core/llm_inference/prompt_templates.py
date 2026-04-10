"""
LLM Prompt 模板集合

提供前置关系推断和知识点匹配的 Prompt 模板。
"""

# ============ 前置关系推断 Prompt ============
PREREQUISITE_PROMPT = """
你是一位教育专家，请判断以下知识点之间的学习依赖关系。

**学习依赖（PREREQUISITE）**: 不学A就学不懂B（核心前置）
**教学顺序（TEACHES_BEFORE）**: 教材先教A后教B，但学B不一定需要先学A

知识点A: {kp_a_name}
知识点A描述: {kp_a_description}

知识点B: {kp_b_name}
知识点B描述: {kp_b_description}

请回答以下问题：
1. 学习B是否需要先学习A？(是/否)
2. 置信度：(高/中/低) - 高表示非常确定，中表示比较确定，低表示不确定
3. 原因：(简短说明，不超过50字)

请严格按照以下 JSON 格式回答：
```json
{
    "is_prerequisite": true或false,
    "confidence": 0.0到1.0之间的数值,
    "reason": "原因说明"
}
```

注意：区分"教学顺序"和"学习依赖"。如果教材先教A后教B，但学B不需要先学A，请回答否。
"""

# ============ 知识点匹配 Prompt ============
# 用于 kg-math-complete-graph 的知识点匹配
KP_MATCH_PROMPT = """
你是一位教育专家，请判断以下两个知识点是否表示同一个概念。

教材知识点名称: {textbook_kp_name}
教材知识点描述: {textbook_kp_description}

知识图谱知识点名称: {kg_kp_name}
知识图谱知识点描述: {kg_kp_description}

请回答以下问题：
1. 这两个知识点是否表示同一概念？(是/否)
2. 置信度：(0.0-1.0)
3. 原因：(简短说明，不超过50字)

请严格按照以下 JSON 格式回答：
```json
{
    "is_match": true或false,
    "confidence": 0.0到1.0之间的数值,
    "reason": "原因说明"
}
```

注意：如果只是相关但不是同一概念，请回答否。
"""

# ============ 定义依赖抽取 Prompt ============
DEFINITION_DEPS_PROMPT = """
你是一位教育专家，请从以下知识点的定义中识别出它依赖的其他知识点名称。

知识点名称: {kp_name}
知识点定义: {kp_definition}

已知的知识点列表（仅从以下列表中选择）:
{kp_list}

请回答：
1. 该知识点定义中引用或依赖的其他知识点名称
2. 置信度：(0.0-1.0)

请严格按照以下 JSON 格式回答：
```json
{
    "dependencies": ["知识点名称1", "知识点名称2", ...],
    "confidence": 0.0到1.0之间的数值
}
```

注意：只返回定义中明确提及的知识点，不要推断隐含依赖。
"""


def format_prerequisite_prompt(
    kp_a_name: str,
    kp_a_description: str,
    kp_b_name: str,
    kp_b_description: str
) -> str:
    """
    格式化前置关系推断 Prompt

    Args:
        kp_a_name: 知识点A名称
        kp_a_description: 知识点A描述
        kp_b_name: 知识点B名称
        kp_b_description: 知识点B描述

    Returns:
        格式化后的 Prompt
    """
    return PREREQUISITE_PROMPT.format(
        kp_a_name=kp_a_name,
        kp_a_description=kp_a_description or "无描述",
        kp_b_name=kp_b_name,
        kp_b_description=kp_b_description or "无描述"
    )


def format_kp_match_prompt(
    textbook_kp_name: str,
    textbook_kp_description: str,
    kg_kp_name: str,
    kg_kp_description: str
) -> str:
    """
    格式化知识点匹配 Prompt

    Args:
        textbook_kp_name: 教材知识点名称
        textbook_kp_description: 教材知识点描述
        kg_kp_name: 知识图谱知识点名称
        kg_kp_description: 知识图谱知识点描述

    Returns:
        格式化后的 Prompt
    """
    return KP_MATCH_PROMPT.format(
        textbook_kp_name=textbook_kp_name,
        textbook_kp_description=textbook_kp_description or "无描述",
        kg_kp_name=kg_kp_name,
        kg_kp_description=kg_kp_description or "无描述"
    )


def format_definition_deps_prompt(
    kp_name: str,
    kp_definition: str,
    kp_list: str
) -> str:
    """
    格式化定义依赖抽取 Prompt

    Args:
        kp_name: 知识点名称
        kp_definition: 知识点定义
        kp_list: 已知知识点列表（字符串形式）

    Returns:
        格式化后的 Prompt
    """
    return DEFINITION_DEPS_PROMPT.format(
        kp_name=kp_name,
        kp_definition=kp_definition or "无定义",
        kp_list=kp_list
    )