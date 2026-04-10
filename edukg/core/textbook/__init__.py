"""
教材数据处理模块

提供教材数据生成和知识点匹配功能。

主要组件:
- TextbookDataGenerator: 教材数据生成器
- URIGenerator: URI 生成器
- KPMatcher: 知识点匹配器
- is_valid_knowledge_point: 知识点过滤函数
"""

from edukg.core.textbook.data_generator import TextbookDataGenerator
from edukg.core.textbook.uri_generator import URIGenerator
from edukg.core.textbook.kp_matcher import KPMatcher
from edukg.core.textbook.filters import (
    is_valid_knowledge_point,
    filter_knowledge_points,
    NON_KNOWLEDGE_POINT_MARKERS,
)

__all__ = [
    "TextbookDataGenerator",
    "URIGenerator",
    "KPMatcher",
    "is_valid_knowledge_point",
    "filter_knowledge_points",
    "NON_KNOWLEDGE_POINT_MARKERS",
]