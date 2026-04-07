"""
知识点对比和 TTL 生成服务测试
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from edukg.core.curriculum.kp_comparison import (
    ConceptComparator,
    ComparisonResult,
    ComparisonReport,
)
from edukg.core.curriculum.ttl_generator import (
    TTLGenerator,
    TTLConfig,
)


class TestConceptComparator:
    """知识点对比服务测试"""

    def test_find_partial_match_contains(self):
        """测试包含关系的部分匹配"""
        comparator = ConceptComparator()
        comparator._concepts_cache = {"正数", "负数"}

        result = comparator._find_partial_match("正数和负数", comparator._concepts_cache)
        assert result in ["正数", "负数"]

    def test_find_partial_match_no_match(self):
        """测试无匹配"""
        comparator = ConceptComparator()
        comparator._concepts_cache = {"一元一次方程", "二元一次方程"}

        result = comparator._find_partial_match("凑十法", comparator._concepts_cache)
        assert result is None

    def test_compare_knowledge_point_exact_match(self):
        """测试精确匹配"""
        comparator = ConceptComparator()
        comparator._concepts_cache = {"一元一次方程", "有理数"}

        result = comparator.compare_knowledge_point("一元一次方程", comparator._concepts_cache)

        assert result.status == "matched"
        assert result.concept_label == "一元一次方程"
        assert result.confidence == 1.0

    def test_compare_knowledge_point_new(self):
        """测试新知识点"""
        comparator = ConceptComparator()
        comparator._concepts_cache = {"一元一次方程"}

        result = comparator.compare_knowledge_point("凑十法", comparator._concepts_cache)

        assert result.status == "new"
        assert result.concept_label is None

    def test_compare_from_file_not_found(self):
        """测试文件不存在"""
        comparator = ConceptComparator()
        with pytest.raises(FileNotFoundError, match="知识点文件不存在"):
            comparator.compare_from_curriculum_kps("/nonexistent/file.json")

    def test_save_report(self, tmp_path):
        """测试保存报告"""
        report = ComparisonReport(
            comparison_at="2026-04-07T10:00:00Z",
            total_extracted=10,
            matched_count=6,
            new_count=4,
            match_rate="60%",
            results=[
                {"knowledge_point": "一元一次方程", "status": "matched"},
                {"knowledge_point": "凑十法", "status": "new"},
            ],
            by_stage={"第一学段": {"total": 5, "matched": 3, "new": 2}},
        )

        output_path = tmp_path / "kp_comparison_report.json"
        comparator = ConceptComparator()
        comparator.save_report(report, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["total_extracted"] == 10
        assert data["match_rate"] == "60%"


class TestTTLGenerator:
    """TTL 生成服务测试"""

    def test_escape_uri(self):
        """测试 URI 转义"""
        generator = TTLGenerator()

        assert generator._escape_uri("一元一次方程") == "一元一次方程"
        assert generator._escape_uri("20以内数的认识") == "20以内数的认识"
        assert generator._escape_uri("正数和负数") == "正数和负数"
        assert generator._escape_uri("有理数（第一课时）") == "有理数第一课时"

    def test_generate_ttl(self, tmp_path):
        """测试生成 TTL"""
        # 创建测试数据
        kps_data = {
            "stages": [
                {
                    "stage": "第一学段",
                    "domains": [
                        {
                            "domain": "数与代数",
                            "knowledge_points": ["加减法", "乘法"],
                        }
                    ],
                }
            ]
        }

        kps_path = tmp_path / "curriculum_kps.json"
        with open(kps_path, "w", encoding="utf-8") as f:
            json.dump(kps_data, f)

        output_path = tmp_path / "curriculum_kps.ttl"

        generator = TTLGenerator()
        generator.generate_ttl(str(kps_path), str(output_path), verbose=False)

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        # 检查前缀声明
        assert "@prefix curriculum:" in content
        assert "@prefix rdf:" in content

        # 检查知识点定义
        assert "加减法" in content
        assert "乘法" in content
        assert "belongsToStage" in content
        assert "belongsToDomain" in content

    def test_generate_ttl_file_not_found(self):
        """测试文件不存在"""
        generator = TTLGenerator()
        with pytest.raises(FileNotFoundError, match="知识点文件不存在"):
            generator.generate_ttl("/nonexistent/file.json", "output.ttl")

    def test_generate_from_comparison_report(self, tmp_path):
        """测试从对比报告生成 TTL"""
        # 创建测试数据
        report_data = {
            "results": [
                {"knowledge_point": "凑十法", "status": "new", "suggested_types": ["数学概念"]},
                {"knowledge_point": "一元一次方程", "status": "matched"},
            ]
        }

        report_path = tmp_path / "kp_comparison_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f)

        output_path = tmp_path / "new_kps.ttl"

        generator = TTLGenerator()
        generator.generate_from_comparison_report(
            str(report_path),
            str(output_path),
            only_new=True,
            verbose=False,
        )

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        # 只有新知识点
        assert "凑十法" in content
        assert "一元一次方程" not in content


class TestTTLConfig:
    """TTL 配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = TTLConfig()

        assert config.namespace == "http://edukg.org/curriculum/math#"
        assert config.prefix == "curriculum"

    def test_custom_config(self):
        """测试自定义配置"""
        config = TTLConfig(
            namespace="http://example.org/test#",
            prefix="test",
        )

        assert config.namespace == "http://example.org/test#"
        assert config.prefix == "test"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])