"""
关系提取服务测试

测试 RelationExtractor 类
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from edukg.core.curriculum.kg_builder import URIGenerator, KGConfig
from edukg.core.curriculum.relation_extractor import (
    RelationExtractor,
    RelationExtractionResult,
)


class TestRelationExtractor:
    """关系提取器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = RelationExtractor()

        assert extractor.uri_generator is not None

    def test_generate_related_to_relation(self):
        """测试生成 RELATED_TO 关系"""
        extractor = RelationExtractor()

        relation = extractor.generate_related_to_relation(
            statement_uri="http://xxx/statement#1",
            statement_label="凑十法的定义",
            concept_uri="http://xxx/instance#1",
            concept_label="凑十法",
        )

        assert relation["relation"] == "relatedTo"
        assert relation["from"]["label"] == "凑十法的定义"
        assert relation["to"]["label"] == "凑十法"

    def test_generate_part_of_relation(self):
        """测试生成 PART_OF 关系"""
        extractor = RelationExtractor()

        relation = extractor.generate_part_of_relation(
            part_uri="http://xxx/instance#1",
            part_label="20以内加法",
            whole_uri="http://xxx/instance#2",
            whole_label="加法",
        )

        assert relation["relation"] == "partOf"
        assert relation["from"]["label"] == "20以内加法"
        assert relation["to"]["label"] == "加法"

    def test_generate_belongs_to_relation(self):
        """测试生成 BELONGS_TO 关系"""
        extractor = RelationExtractor()

        relation = extractor.generate_belongs_to_relation(
            child_uri="http://xxx/instance#1",
            child_label="凑十法",
            parent_uri="http://xxx/instance#2",
            parent_label="进位加法",
        )

        assert relation["relation"] == "belongsTo"
        assert relation["from"]["label"] == "凑十法"
        assert relation["to"]["label"] == "进位加法"

    def test_extract_relations_with_llm(self):
        """测试使用 LLM 提取关系"""
        extractor = RelationExtractor()

        # Mock LLM 响应
        with patch.object(extractor, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "relations": [
                    {
                        "from": "凑十法",
                        "relation": "belongsTo",
                        "to": "进位加法",
                        "confidence": 0.85,
                    }
                ]
            }

            concepts = [
                {"label": "凑十法", "uri": "http://xxx#1"},
                {"label": "进位加法", "uri": "http://xxx#2"},
            ]

            results = extractor.extract_concept_relations(concepts)

            assert len(results) > 0

    def test_generate_statement_concept_relations(self):
        """测试生成 Statement → Concept 关系"""
        extractor = RelationExtractor()

        statements = [
            {
                "uri": "http://xxx/statement#1",
                "label": "凑十法的定义",
                "content": "凑十法是一种计算方法...",
            }
        ]

        concepts = [
            {
                "uri": "http://xxx/instance#1",
                "label": "凑十法",
            }
        ]

        relations = extractor.generate_statement_concept_relations(
            statements, concepts
        )

        # 应该生成 RELATED_TO 关系
        assert len(relations) > 0
        assert relations[0]["relation"] == "relatedTo"

    def test_save_relations(self, tmp_path):
        """测试保存 relations.json"""
        extractor = RelationExtractor()

        relations = [
            {
                "from": {"uri": "http://xxx#1", "label": "A"},
                "relation": "relatedTo",
                "to": {"uri": "http://xxx#2", "label": "B"},
            }
        ]

        output_path = tmp_path / "relations.json"
        extractor.save_relations(relations, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "relations" in data
        assert data["metadata"]["total_relations"] == 1


class TestRelationExtractionResult:
    """关系提取结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = RelationExtractionResult(
            from_label="凑十法",
            from_uri="http://xxx#1",
            relation="belongsTo",
            to_label="进位加法",
            to_uri="http://xxx#2",
            confidence=0.85,
        )

        assert result.from_label == "凑十法"
        assert result.relation == "belongsTo"
        assert result.confidence == 0.85


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])