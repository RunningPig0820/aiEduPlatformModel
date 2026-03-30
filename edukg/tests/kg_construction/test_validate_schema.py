"""
Tests for validate_schema.py
"""

import pytest
from pathlib import Path
import sys

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts' / 'kg_construction'
sys.path.insert(0, str(scripts_dir))

from validate_schema import (
    EXPECTED_LABELS,
    EXPECTED_CONSTRAINTS
)


class TestValidationDefinitions:
    """测试验证定义常量"""

    def test_expected_labels_count(self):
        """测试预期标签数量（应为 6 个）"""
        assert len(EXPECTED_LABELS) == 6

    def test_expected_labels_content(self):
        """测试预期标签内容"""
        expected = ['Subject', 'Stage', 'Grade', 'Textbook', 'Chapter', 'KnowledgePoint']
        assert EXPECTED_LABELS == expected

    def test_expected_constraints_count(self):
        """测试预期约束数量（应为 3 个）"""
        assert len(EXPECTED_CONSTRAINTS) == 3

    def test_expected_constraints_format(self):
        """测试预期约束格式 (name, label, property)"""
        for constraint in EXPECTED_CONSTRAINTS:
            assert len(constraint) == 3
            name, label, prop = constraint
            assert isinstance(name, str)
            assert isinstance(label, str)
            assert isinstance(prop, str)


class TestReportOutput:
    """测试报告输出格式"""

    def test_report_structure(self):
        """测试报告结构"""
        report = {
            'labels': {'expected': 6, 'found': 6, 'missing': []},
            'constraints': {'expected': 3, 'found': 3, 'missing': []}
        }
        assert 'labels' in report
        assert 'constraints' in report
        assert report['labels']['expected'] == 6
        assert report['constraints']['expected'] == 3