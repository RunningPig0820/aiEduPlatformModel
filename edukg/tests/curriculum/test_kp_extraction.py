"""
知识点提取服务测试
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from edukg.core.curriculum.kp_extraction import (
    LLMExtractor,
    CurriculumKnowledgePoints,
    KnowledgePoint,
)


class TestLLMExtractor:
    """LLM 提取器测试"""

    def test_init_with_params(self):
        """测试使用参数初始化"""
        extractor = LLMExtractor(api_key="test_api_key")
        assert extractor.api_key == "test_api_key"
        assert extractor.model == "glm-4-flash"

    def test_init_missing_api_key(self):
        """测试缺少 API Key 时抛出异常"""
        with patch("edukg.core.curriculum.kp_extraction.settings") as mock_settings:
            mock_settings.ZHIPU_API_KEY = ""
            with pytest.raises(ValueError, match="智谱 API Key 未配置"):
                LLMExtractor()

    def test_chunk_text_short(self):
        """测试短文本不分块"""
        extractor = LLMExtractor(api_key="test_api_key")
        text = "这是一段短文本"
        chunks = extractor._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_long(self):
        """测试长文本分块"""
        extractor = LLMExtractor(api_key="test_api_key")
        # 创建一个超过 8000 字符的文本
        text = "这是一段测试文本。\n\n" * 2000
        chunks = extractor._chunk_text(text, max_chars=1000)
        assert len(chunks) > 1

    def test_extract_json_from_response_direct(self):
        """测试直接解析 JSON"""
        extractor = LLMExtractor(api_key="test_api_key")
        response = '{"stages": [{"stage": "第一学段"}]}'
        result = extractor._extract_json_from_response(response)
        assert result["stages"][0]["stage"] == "第一学段"

    def test_extract_json_from_response_code_block(self):
        """测试从代码块提取 JSON"""
        extractor = LLMExtractor(api_key="test_api_key")
        response = '''
这是一些文本
```json
{"stages": [{"stage": "第一学段"}]}
```
更多文本
'''
        result = extractor._extract_json_from_response(response)
        assert result["stages"][0]["stage"] == "第一学段"

    def test_extract_json_from_response_invalid(self):
        """测试无效响应抛出异常"""
        extractor = LLMExtractor(api_key="test_api_key")
        with pytest.raises(ValueError, match="无法从响应中提取有效的 JSON"):
            extractor._extract_json_from_response("这不是 JSON")

    def test_merge_stages(self):
        """测试合并学段结果"""
        extractor = LLMExtractor(api_key="test_api_key")

        stages_list = [
            [
                {
                    "stage": "第一学段",
                    "grades": "1-2年级",
                    "domains": [
                        {"domain": "数与代数", "knowledge_points": ["加减法"]}
                    ],
                }
            ],
            [
                {
                    "stage": "第一学段",
                    "grades": "1-2年级",
                    "domains": [
                        {"domain": "数与代数", "knowledge_points": ["乘法"]},
                        {"domain": "图形与几何", "knowledge_points": ["认识图形"]},
                    ],
                }
            ],
        ]

        merged = extractor._merge_stages(stages_list)

        assert len(merged) == 1
        assert merged[0]["stage"] == "第一学段"
        assert len(merged[0]["domains"]) == 2
        # 检查知识点是否合并
        num_domain = next(
            d for d in merged[0]["domains"] if d["domain"] == "数与代数"
        )
        assert len(num_domain["knowledge_points"]) == 2

    def test_extract_from_ocr_result_file_not_found(self):
        """测试 OCR 结果文件不存在"""
        extractor = LLMExtractor(api_key="test_api_key")
        with pytest.raises(FileNotFoundError, match="OCR 结果文件不存在"):
            extractor.extract_from_ocr_result("/nonexistent/file.json")

    @patch("edukg.core.curriculum.kp_extraction.LLMExtractor.extract_knowledge_points")
    def test_extract_from_ocr_result_success(self, mock_extract):
        """测试从 OCR 结果提取知识点"""
        # 创建临时 OCR 结果文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            ocr_data = {
                "pdf_path": "test.pdf",
                "pages": [
                    {"page_num": 1, "text": "第一学段内容"},
                    {"page_num": 2, "text": "第二学段内容"},
                ],
            }
            json.dump(ocr_data, f)
            temp_path = f.name

        try:
            # Mock extract_knowledge_points
            mock_result = CurriculumKnowledgePoints(
                source="test.pdf",
                extracted_at="2026-04-07T10:00:00Z",
                total_stages=2,
                total_knowledge_points=10,
                stages=[],
            )
            mock_extract.return_value = mock_result

            extractor = LLMExtractor(api_key="test_api_key")
            result = extractor.extract_from_ocr_result(temp_path, verbose=False)

            assert result.source == "test.pdf"
            assert result.total_stages == 2
        finally:
            os.unlink(temp_path)

    def test_save_result(self, tmp_path):
        """测试保存结果"""
        result = CurriculumKnowledgePoints(
            source="test.pdf",
            extracted_at="2026-04-07T10:00:00Z",
            total_stages=1,
            total_knowledge_points=3,
            stages=[
                {
                    "stage": "第一学段",
                    "grades": "1-2年级",
                    "domains": [
                        {
                            "domain": "数与代数",
                            "knowledge_points": ["加减法", "乘法", "除法"],
                        }
                    ],
                }
            ],
        )

        output_path = tmp_path / "curriculum_kps.json"

        extractor = LLMExtractor(api_key="test_api_key")
        extractor.save_result(result, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["source"] == "test.pdf"
        assert data["total_knowledge_points"] == 3


class TestCurriculumKnowledgePoints:
    """知识点结构测试"""

    def test_creation(self):
        """测试创建知识点结构"""
        result = CurriculumKnowledgePoints(
            source="test.pdf",
            extracted_at="2026-04-07T10:00:00Z",
            total_stages=1,
            total_knowledge_points=1,
            stages=[{"stage": "第一学段"}],
        )

        assert result.source == "test.pdf"
        assert result.total_stages == 1


class TestKnowledgePoint:
    """知识点测试"""

    def test_creation(self):
        """测试创建知识点"""
        kp = KnowledgePoint(
            name="一元一次方程",
            stage="第三学段",
            domain="数与代数",
        )

        assert kp.name == "一元一次方程"
        assert kp.stage == "第三学段"
        assert kp.domain == "数与代数"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])