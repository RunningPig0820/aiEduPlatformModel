"""
Tests for split_material_ttl.py
"""

import pytest
from pathlib import Path
import sys

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts' / 'kg_construction'
sys.path.insert(0, str(scripts_dir))

from split_material_ttl import (
    extract_subject_from_name,
    SUBJECT_KEYWORDS,
    DEFAULT_SUBJECTS
)


class TestExtractSubjectFromName:
    """测试教材名称学科提取"""

    def test_extract_math(self):
        """测试提取数学学科"""
        assert extract_subject_from_name("高中数学必修第一册A版") == "math"

    def test_extract_physics(self):
        """测试提取物理学科"""
        assert extract_subject_from_name("高中物理必修第一册") == "physics"
        assert extract_subject_from_name("物理选择性必修第二册") == "physics"

    def test_extract_chemistry(self):
        """测试提取化学学科"""
        assert extract_subject_from_name("高中化学必修第一册") == "chemistry"
        assert extract_subject_from_name("化学选择性必修1——化学反应原理") == "chemistry"

    def test_extract_biology(self):
        """测试提取生物学科"""
        assert extract_subject_from_name("高中生物学必修1——分子与细胞") == "biology"
        assert extract_subject_from_name("普通高中课程标准实验教科书生物2必修") == "biology"

    def test_extract_history(self):
        """测试提取历史学科"""
        assert extract_subject_from_name("历史必修——中外历史纲要（上）") == "history"
        assert extract_subject_from_name("历史选择性必修1——国家制度与社会治理") == "history"

    def test_extract_geo(self):
        """测试提取地理学科"""
        assert extract_subject_from_name("地理必修第一册") == "geo"
        assert extract_subject_from_name("普通高中教科书地理选择性必修1") == "geo"

    def test_extract_chinese(self):
        """测试提取语文学科"""
        assert extract_subject_from_name("高中语文必修上册") == "chinese"
        assert extract_subject_from_name("高中语文选择性必修上册") == "chinese"

    def test_extract_english(self):
        """测试提取英语学科"""
        assert extract_subject_from_name("高中英语必修第一册") == "english"
        assert extract_subject_from_name("普通高中教科书英语选择性必修——第三册") == "english"

    def test_extract_politics(self):
        """测试提取政治学科"""
        assert extract_subject_from_name("思想政治必修1——中国特色社会主义") == "politics"
        assert extract_subject_from_name("思想政治选择性必修2——法律与生活") == "politics"

    def test_unknown_subject(self):
        """测试未匹配返回 unknown"""
        assert extract_subject_from_name("第五章 原子核") == "unknown"
        assert extract_subject_from_name("索引") == "unknown"


class TestSubjectKeywords:
    """测试学科关键词映射"""

    def test_keywords_count(self):
        """测试关键词数量"""
        assert len(SUBJECT_KEYWORDS) >= 10  # 至少 10 个关键词

    def test_default_subjects_count(self):
        """测试默认学科数量（应为 9 个）"""
        assert len(DEFAULT_SUBJECTS) == 9

    def test_subjects_unique(self):
        """测试学科代码唯一"""
        assert len(DEFAULT_SUBJECTS) == len(set(DEFAULT_SUBJECTS))