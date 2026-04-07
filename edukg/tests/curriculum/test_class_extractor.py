"""
Class 提取服务测试

测试 ClassExtractor 类
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from edukg.core.curriculum.kg_builder import URIGenerator, KGConfig
from edukg.core.curriculum.class_extractor import (
    ClassExtractor,
    ClassExtractionResult,
)


class TestClassExtractor:
    """Class 提取器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = ClassExtractor()

        assert extractor.uri_generator is not None
        assert len(extractor.existing_classes) > 0

    def test_load_existing_classes(self):
        """测试加载现有 Class 列表"""
        extractor = ClassExtractor()

        # 应该有 38 个现有 Class
        assert len(extractor.existing_classes) == 38

        # 检查关键 Class 存在
        class_labels = [c["label"] for c in extractor.existing_classes]
        assert "数学概念" in class_labels
        assert "数学方法" in class_labels
        assert "数学定义" in class_labels

    def test_get_class_list_for_prompt(self):
        """测试获取 Class 列表用于 prompt"""
        extractor = ClassExtractor()

        class_list = extractor.get_class_list_for_prompt()

        # 应该是一个字符串，包含所有 Class 名称
        assert isinstance(class_list, str)
        assert "数学概念" in class_list
        assert "数学方法" in class_list

    def test_infer_type_existing_class(self):
        """测试推断知识点类型 - 已有 Class"""
        extractor = ClassExtractor()

        # Mock LLM 响应
        with patch.object(extractor, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "class": "数学方法",
                "confidence": 0.9,
                "reason": "凑十法是一种计算方法"
            }

            result = extractor.infer_type("凑十法")

            assert result.class_label == "数学方法"
            assert result.confidence >= 0.8
            assert result.is_new_class is False

    def test_infer_type_new_class(self):
        """测试推断知识点类型 - 需要新增 Class"""
        extractor = ClassExtractor()

        # Mock LLM 响应 - 建议新增 Class
        with patch.object(extractor, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "class": "小学数概念",
                "confidence": 0.85,
                "reason": "这是小学特有的数概念",
                "suggest_new": True,
                "parent_class": "数学概念"
            }

            result = extractor.infer_type("20以内数的认识")

            assert result.class_label == "小学数概念"
            assert result.is_new_class is True
            assert result.parent_class == "数学概念"

    def test_batch_infer_types(self):
        """测试批量推断类型"""
        extractor = ClassExtractor()

        # Mock LLM 响应
        with patch.object(extractor, '_call_llm') as mock_llm:
            mock_llm.side_effect = [
                {"class": "数学方法", "confidence": 0.9, "reason": "计算方法"},
                {"class": "数学概念", "confidence": 0.95, "reason": "数的概念"},
            ]

            knowledge_points = ["凑十法", "有理数"]
            results = extractor.batch_infer_types(knowledge_points)

            assert len(results) == 2
            assert results[0].class_label == "数学方法"
            assert results[1].class_label == "数学概念"

    def test_generate_class_definition(self):
        """测试生成 Class 定义"""
        extractor = ClassExtractor()

        class_def = extractor.generate_class_definition(
            label="小学数概念",
            parent_uri="http://edukg.org/knowledge/0.1/class/math#shuxuegainian-xxx",
        )

        assert class_def["label"] == "小学数概念"
        assert class_def["description"] == "小学数概念"
        assert class_def["type"] == "owl:Class"
        assert len(class_def["parents"]) == 1
        assert class_def["uri"].startswith("http://edukg.org/knowledge/0.2/class/math#")

    def test_extract_classes_from_kps(self):
        """测试从知识点列表提取 Class"""
        extractor = ClassExtractor()

        # Mock LLM 响应
        with patch.object(extractor, 'batch_infer_types') as mock_batch:
            mock_batch.return_value = [
                ClassExtractionResult(
                    knowledge_point="凑十法",
                    class_label="数学方法",
                    confidence=0.9,
                    is_new_class=False,
                ),
                ClassExtractionResult(
                    knowledge_point="20以内数的认识",
                    class_label="小学数概念",
                    confidence=0.85,
                    is_new_class=True,
                    parent_class="数学概念",
                ),
            ]

            kps = ["凑十法", "20以内数的认识"]
            classes = extractor.extract_classes_from_kps(kps)

            # 应该只有一个新 Class（小学数概念）
            assert len(classes) == 1
            assert classes[0]["label"] == "小学数概念"

    def test_save_classes(self, tmp_path):
        """测试保存 classes.json"""
        extractor = ClassExtractor()

        classes = [
            {
                "uri": "http://edukg.org/knowledge/0.2/class/math#test-abc",
                "id": "test-abc",
                "subject": "math",
                "label": "测试概念",
                "description": "测试概念",
                "parents": [],
                "type": "owl:Class",
            }
        ]

        output_path = tmp_path / "classes.json"
        extractor.save_classes(classes, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["subject"] == "math"
        assert data["class_count"] == 1


class TestClassExtractionResult:
    """Class 提取结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = ClassExtractionResult(
            knowledge_point="凑十法",
            class_label="数学方法",
            confidence=0.9,
            is_new_class=False,
        )

        assert result.knowledge_point == "凑十法"
        assert result.class_label == "数学方法"
        assert result.confidence == 0.9
        assert result.is_new_class is False


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])