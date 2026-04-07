"""
Statement 提取服务测试

测试 StatementExtractor 类
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from edukg.core.curriculum.kg_builder import URIGenerator, KGConfig
from edukg.core.curriculum.statement_extractor import (
    StatementExtractor,
    StatementExtractionResult,
)


class TestStatementExtractor:
    """Statement 提取器测试"""

    def test_init_default(self):
        """测试默认初始化"""
        extractor = StatementExtractor()

        assert extractor.uri_generator is not None

    def test_generate_definition_with_llm(self):
        """测试使用 LLM 生成定义"""
        extractor = StatementExtractor()

        # Mock LLM 响应
        with patch.object(extractor, '_call_llm') as mock_llm:
            mock_llm.return_value = {
                "definition": "凑十法是一种计算方法，将一个数拆分成10和另一部分，便于快速计算。",
                "confidence": 0.9,
            }

            result = extractor.generate_definition("凑十法")

            assert "凑十法" in result["definition"]
            assert result["confidence"] >= 0.5

    def test_generate_definition_without_llm(self):
        """测试无 LLM 时的默认定义"""
        # 创建无 API key 的 extractor
        extractor = StatementExtractor(api_key="")

        result = extractor.generate_definition("有理数")

        # 应该返回默认定义
        assert "有理数" in result["definition"]

    def test_generate_statement(self):
        """测试生成 Statement 实体"""
        extractor = StatementExtractor()

        statement = extractor.generate_statement(
            concept_label="凑十法",
            concept_uri="http://edukg.org/knowledge/0.2/instance/math#xxx",
            definition="凑十法是一种计算方法...",
        )

        assert "凑十法" in statement["label"]
        assert statement["uri"].startswith("http://edukg.org/knowledge/0.2/statement/math#")
        assert statement["content"] == "凑十法是一种计算方法..."
        assert "types" in statement

    def test_batch_generate_statements(self):
        """测试批量生成 Statement"""
        extractor = StatementExtractor()

        # Mock LLM 响应
        with patch.object(extractor, '_call_llm') as mock_llm:
            mock_llm.side_effect = [
                {"definition": "凑十法的定义...", "confidence": 0.9},
                {"definition": "有理数的定义...", "confidence": 0.95},
            ]

            concepts = [
                {"label": "凑十法", "uri": "http://xxx#1"},
                {"label": "有理数", "uri": "http://xxx#2"},
            ]

            statements = extractor.batch_generate_statements(concepts)

            assert len(statements) == 2
            assert "凑十法" in statements[0]["label"]
            assert "有理数" in statements[1]["label"]

    def test_extract_statements_from_concepts(self):
        """测试从 Concept 列表提取 Statement"""
        extractor = StatementExtractor()

        # Mock LLM
        with patch.object(extractor, '_call_llm') as mock_llm:
            mock_llm.return_value = {"definition": "定义内容", "confidence": 0.9}

            concepts = [
                {"label": "凑十法", "uri": "http://xxx#1", "types": ["shuxuefangfa-xxx"]},
            ]

            statements = extractor.extract_statements_from_concepts(concepts, verbose=False)

            assert len(statements) == 1

    def test_save_statements(self, tmp_path):
        """测试保存 statements.json"""
        extractor = StatementExtractor()

        statements = [
            {
                "uri": "http://edukg.org/knowledge/0.2/statement/math#xxx",
                "label": "凑十法的定义",
                "types": ["shuxuedingyi-xxx"],
                "content": "凑十法是一种计算方法...",
            }
        ]

        output_path = tmp_path / "statements.json"
        extractor.save_statements(statements, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["content"] == "凑十法是一种计算方法..."


class TestStatementExtractionResult:
    """Statement 提取结果测试"""

    def test_create_result(self):
        """测试创建结果"""
        result = StatementExtractionResult(
            concept_label="凑十法",
            statement_uri="http://edukg.org/knowledge/0.2/statement/math#xxx",
            definition="定义内容",
        )

        assert result.concept_label == "凑十法"
        assert result.definition == "定义内容"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])