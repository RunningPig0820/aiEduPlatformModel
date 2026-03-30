"""
Tests for split_main_ttl.py
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts' / 'kg_construction'
sys.path.insert(0, str(scripts_dir))

from split_main_ttl import (
    extract_subject_from_uri,
    extract_ttl_headers,
    DEFAULT_SUBJECTS
)


class TestExtractSubjectFromUri:
    """测试 URI 学科提取"""

    def test_extract_biology(self):
        """测试提取 biology 学科"""
        uri = "http://edukg.org/knowledge/3.0/instance/biology#main-E10004"
        assert extract_subject_from_uri(uri) == "biology"

    def test_extract_math(self):
        """测试提取 math 学科"""
        uri = "http://edukg.org/knowledge/3.0/instance/math#main-E1"
        assert extract_subject_from_uri(uri) == "math"

    def test_extract_chemistry(self):
        """测试提取 chemistry 学科"""
        uri = "http://edukg.org/knowledge/3.0/instance/chemistry#main-EXXX"
        assert extract_subject_from_uri(uri) == "chemistry"

    def test_extract_all_subjects(self):
        """测试所有学科"""
        for subject in DEFAULT_SUBJECTS:
            uri = f"http://edukg.org/knowledge/3.0/instance/{subject}#main-E1"
            assert extract_subject_from_uri(uri) == subject

    def test_invalid_uri_returns_unknown(self):
        """测试无效 URI 返回 unknown"""
        uri = "http://example.org/something/else"
        assert extract_subject_from_uri(uri) == "unknown"

    def test_no_instance_prefix_returns_unknown(self):
        """测试没有 instance 前缀返回 unknown"""
        uri = "http://edukg.org/knowledge/3.0/ontology/class#C1"
        assert extract_subject_from_uri(uri) == "unknown"


class TestExtractTtlHeaders:
    """测试 TTL 头部提取"""

    def test_extract_single_prefix(self):
        """测试提取单个 prefix"""
        content = "@prefix ns1: <http://example.org/> .\n\n<http://example.org/entity> a :Class ."
        headers = extract_ttl_headers(content)
        assert "@prefix ns1:" in headers

    def test_extract_multiple_prefixes(self):
        """测试提取多个 prefix"""
        content = "@prefix ns1: <http://a.org/> .\n@prefix ns2: <http://b.org/> .\n\n<http://example.org/entity> a :Class ."
        headers = extract_ttl_headers(content)
        assert "@prefix ns1:" in headers
        assert "@prefix ns2:" in headers

    def test_extract_base(self):
        """测试提取 @base 指令"""
        content = "@base <http://example.org/> .\n\n<entity> a :Class ."
        headers = extract_ttl_headers(content)
        assert "@base" in headers

    def test_empty_content(self):
        """测试空内容"""
        headers = extract_ttl_headers("")
        assert headers == ""

    def test_no_prefixes(self):
        """测试没有 prefix 的内容"""
        content = "<http://example.org/entity> a :Class ."
        headers = extract_ttl_headers(content)
        assert headers == ""


class TestSubjectsList:
    """测试学科列表"""

    def test_subjects_count(self):
        """测试学科数量（应为 8 个）"""
        assert len(DEFAULT_SUBJECTS) == 8

    def test_subjects_content(self):
        """测试学科列表内容"""
        expected = ['biology', 'chemistry', 'chinese', 'geo', 'history', 'math', 'physics', 'politics']
        assert DEFAULT_SUBJECTS == expected