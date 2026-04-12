"""
教材数据处理模块

提供教材数据生成和知识点匹配功能。

主要组件:
- TextbookDataGenerator: 教材数据生成器
- URIGenerator: URI 生成器
- KPMatcher: 知识点匹配器
- DataCleaner: 数据清洗器
- ChapterEnhancer: 章节专题增强器
- KPAttributeInferer: 知识点属性推断器
- is_valid_knowledge_point: 知识点过滤函数
"""

from edukg.core.textbook.data_generator import TextbookDataGenerator
from edukg.core.textbook.uri_generator import URIGenerator
from edukg.core.textbook.kp_matcher import KPMatcher
from edukg.core.textbook.data_cleaner import DataCleaner
from edukg.core.textbook.chapter_enhancer import ChapterEnhancer
from edukg.core.textbook.kp_attribute_inferer import KPAttributeInferer
from edukg.core.textbook.filters import (
    is_valid_knowledge_point,
    filter_knowledge_points,
    NON_KNOWLEDGE_POINT_MARKERS,
)

__all__ = [
    "TextbookDataGenerator",
    "URIGenerator",
    "KPMatcher",
    "DataCleaner",
    "ChapterEnhancer",
    "KPAttributeInferer",
    "is_valid_knowledge_point",
    "filter_knowledge_points",
    "NON_KNOWLEDGE_POINT_MARKERS",
]