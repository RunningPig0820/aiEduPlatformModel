"""
Concept 提取服务测试

测试 ConceptExtractor 类
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from edukg.core.curriculum.kg_builder import URIGenerator, KGConfig
from edukg.core.curriculum.concept_extractor import (
    ConceptExtractor,
    ConceptExtractionResult,
)


class TestConceptExtractor:
    """Concept 提取器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = ConceptExtractor()

        assert extractor.uri_generator is not None

    def test_generate_concept(self):
        """测试生成 Concept 实体"""
        extractor = ConceptExtractor()

        concept = extractor.generate_concept(
            label="凑十法",
            class_id="shuxuefangfa-xxx",
        )

        assert concept["label"] == "凑十法"
        assert concept["uri"].startswith("http://edukg.org/knowledge/0.2/instance/math#")
        assert "types" in concept
        assert "shuxuefangfa" in concept["types"][0]

    def test_generate_concept_with_context(self):
        """测试带上下文生成 Concept"""
        extractor = ConceptExtractor()

        concept = extractor.generate_concept(
            label="有理数",
            class_id="shu-xxx",
            context="第一学段 数与代数",
        )

        assert concept["label"] == "有理数"
        assert "types" in concept

    def test_batch_generate_concepts(self):
        """测试批量生成 Concept"""
        extractor = ConceptExtractor()

        knowledge_points = [
            ("凑十法", "shuxuefangfa-xxx"),
            ("有理数", "shu-xxx"),
        ]

        concepts = extractor.batch_generate_concepts(knowledge_points)

        assert len(concepts) == 2
        assert concepts[0]["label"] == "凑十法"
        assert concepts[1]["label"] == "有理数"

    def test_extract_concepts_from_kps(self):
        """测试从知识点列表提取 Concept"""
        extractor = ConceptExtractor()

        # 模拟知识点数据（带类型推断结果）
        kps_with_types = [
            {
                "knowledge_point": "凑十法",
                "class_label": "数学方法",
                "class_id": "shuxuefangfa-xxx",
            },
            {
                "knowledge_point": "有理数",
                "class_label": "数",
                "class_id": "shu-xxx",
            },
        ]

        concepts = extractor.extract_concepts_from_kps(kps_with_types)

        assert len(concepts) == 2

    def test_save_concepts(self, tmp_path):
        """测试保存 concepts.json"""
        extractor = ConceptExtractor()

        concepts = [
            {
                "uri": "http://edukg.org/knowledge/0.2/instance/math#test-abc",
                "label": "凑十法",
                "types": ["shuxuefangfa-xxx"],
            }
        ]

        output_path = tmp_path / "concepts.json"
        extractor.save_concepts(concepts, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["label"] == "凑十法"

    def test_concept_uri_consistency(self):
        """测试同一知识点生成 URI 一致"""
        extractor = ConceptExtractor()

        concept1 = extractor.generate_concept("凑十法", "shuxuefangfa-xxx")
        concept2 = extractor.generate_concept("凑十法", "shuxuefangfa-xxx")

        assert concept1["uri"] == concept2["uri"]


class TestConceptExtractionResult:
    """Concept 提取结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = ConceptExtractionResult(
            knowledge_point="凑十法",
            concept_uri="http://edukg.org/knowledge/0.2/instance/math#xxx",
            class_id="shuxuefangfa-xxx",
        )

        assert result.knowledge_point == "凑十法"
        assert result.class_id == "shuxuefangfa-xxx"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])