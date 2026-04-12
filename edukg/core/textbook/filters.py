"""
知识点过滤规则

用于过滤教材中非知识点的标记（如"数学活动"、"小结"等）。
"""

import re

# ============ 非知识点标记集合 ============
# 这些标记出现在教材目录中，但不是真正的知识点
NON_KNOWLEDGE_POINT_MARKERS = {
    # 活动类
    "数学活动",
    "★数学乐园",
    "☆摆一摆，想一想",
    "阅读与思考",
    "实验与探究",
    "信息技术应用",
    "数学文化",

    # 总结复习类
    "小结",
    "整理和复习",
    "本章综合与测试",
    "本节综合与测试",
    "构建知识体系",
    "构建知识体系和应用",
    "构建知识体系及练习训练",
    "章前引言",
    "知识梳理",

    # 练习测试类
    "复习题",
    "习题训练",
    "测试",
    "单元测试",
    "综合练习",
    "试卷分析",

    # 综合类
    "本册综合",

    # 其他
    "部分中英文词汇索引",
    "附录",
    "课题学习",
}

# ============ 非知识点前缀 ============
# 以这些前缀开头的也不是知识点
# 注意：包含全角空格和普通空格两种情况
NON_KNOWLEDGE_POINT_PREFIXES = [
    "阅读与思考 ",    # 普通空格
    "阅读与思考　",   # 全角空格
    "实验与探究 ",
    "实验与探究　",
    "信息技术应用 ",   # 普通空格
    "信息技术应用　",  # 全角空格
    "章前引言及",
    "构建知识体系及",
    "复习题",
]

# ============ 非知识点正则模式 ============
# 使用正则匹配特定模式
NON_KNOWLEDGE_POINT_PATTERNS = [
    r"^例\d",           # 例1, 例2, 例3 等
    r"^例\d、例\d",     # 例3、例4 由三视图描述几何体
]


def is_valid_knowledge_point(name: str) -> bool:
    """
    判断是否为有效知识点

    Args:
        name: 知识点名称

    Returns:
        True 如果是有效的知识点，False 否则
    """
    if not name or not name.strip():
        return False

    name = name.strip()

    # 检查是否在非知识点标记集合中
    if name in NON_KNOWLEDGE_POINT_MARKERS:
        return False

    # 检查是否以非知识点前缀开头
    for prefix in NON_KNOWLEDGE_POINT_PREFIXES:
        if name.startswith(prefix):
            return False

    # 检查是否匹配非知识点正则模式
    for pattern in NON_KNOWLEDGE_POINT_PATTERNS:
        if re.match(pattern, name):
            return False

    # 检查是否为纯数字或章节编号格式（如 "1.1", "1.2.3"）
    # 这些通常是章节编号，不是知识点
    if _is_chapter_number(name):
        return False

    return True


def _is_chapter_number(name: str) -> bool:
    """
    判断是否为章节编号格式

    Args:
        name: 名称

    Returns:
        True 如果是章节编号格式
    """
    # 匹配 "1.1", "1.2.3", "1.1.1" 等格式
    pattern = r'^\d+(\.\d+)+$'
    if re.match(pattern, name):
        return True

    # 匹配纯数字
    if name.isdigit():
        return True

    return False


def filter_knowledge_points(kps: list) -> list:
    """
    过滤知识点列表，移除非知识点

    Args:
        kps: 知识点名称列表

    Returns:
        过滤后的知识点列表
    """
    return [kp for kp in kps if is_valid_knowledge_point(kp)]


def get_filter_stats(original: list, filtered: list) -> dict:
    """
    获取过滤统计信息

    Args:
        original: 原始列表
        filtered: 过滤后列表

    Returns:
        统计信息字典
    """
    removed = set(original) - set(filtered)
    return {
        "original_count": len(original),
        "filtered_count": len(filtered),
        "removed_count": len(removed),
        "removed_items": list(removed)
    }