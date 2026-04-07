"""
PDF OCR 服务测试
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from edukg.core.curriculum.pdf_ocr import BaiduOCRService, OCRAPIError, OCRResult


class TestBaiduOCRService:
    """百度 OCR 服务测试"""

    def test_init_with_params(self):
        """测试使用参数初始化"""
        service = BaiduOCRService(
            api_key="custom_api_key",
            secret_key="custom_secret_key"
        )
        assert service.api_key == "custom_api_key"
        assert service.secret_key == "custom_secret_key"

    @patch("edukg.core.curriculum.pdf_ocr.settings")
    def test_init_missing_credentials(self, mock_settings):
        """测试缺少凭证时抛出异常"""
        # Mock settings 返回空值
        mock_settings.BAIDU_OCR_API_KEY = ""
        mock_settings.BAIDU_OCR_SECRET_KEY = ""

        with pytest.raises(ValueError, match="百度 OCR API Key 未配置"):
            BaiduOCRService()

    def test_extract_text_file_not_found(self):
        """测试文件不存在时抛出异常"""
        service = BaiduOCRService(
            api_key="test_api_key",
            secret_key="test_secret_key"
        )

        with pytest.raises(FileNotFoundError, match="PDF 文件不存在"):
            service.extract_text("/nonexistent/file.pdf")

    @patch("edukg.core.curriculum.pdf_ocr.convert_from_path")
    @patch("edukg.core.curriculum.pdf_ocr.BaiduOCRService._ocr_image")
    @patch("edukg.core.curriculum.pdf_ocr.Path.exists")
    def test_extract_text_success(self, mock_exists, mock_ocr, mock_convert):
        """测试成功提取文字"""
        # Mock 文件存在
        mock_exists.return_value = True

        # Mock PDF 转图片
        mock_image = MagicMock()
        mock_image.save = MagicMock()
        mock_convert.return_value = [mock_image, mock_image]

        # Mock OCR 识别
        mock_ocr.return_value = "测试文字内容"

        service = BaiduOCRService(
            api_key="test_api_key",
            secret_key="test_secret_key"
        )

        result = service.extract_text("test.pdf", verbose=False)

        assert isinstance(result, OCRResult)
        assert result.total_pages == 2
        assert len(result.pages) == 2
        assert result.pages[0]["text"] == "测试文字内容"

    def test_save_ocr_result(self, tmp_path):
        """测试保存 OCR 结果"""
        result = OCRResult(
            pdf_path="test.pdf",
            total_pages=2,
            pages=[
                {"page_num": 1, "text": "第一页内容"},
                {"page_num": 2, "text": "第二页内容"},
            ],
            processed_at="2026-04-07T10:00:00Z",
        )

        output_path = tmp_path / "ocr_result.json"

        service = BaiduOCRService(
            api_key="test_api_key",
            secret_key="test_secret_key"
        )
        service.save_ocr_result(result, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["pdf_path"] == "test.pdf"
        assert data["total_pages"] == 2
        assert len(data["pages"]) == 2

    @patch("edukg.core.curriculum.pdf_ocr.httpx.post")
    def test_get_access_token(self, mock_post):
        """测试获取 Access Token"""
        # Mock API 响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 2592000,
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        service = BaiduOCRService(
            api_key="test_api_key",
            secret_key="test_secret_key"
        )
        token = service._get_access_token()

        assert token == "test_token"
        assert service._access_token == "test_token"


class TestOCRAPIError:
    """OCR API 错误测试"""

    def test_error_message(self):
        """测试错误消息"""
        error = OCRAPIError("API 调用失败")
        assert str(error) == "API 调用失败"


class TestOCRResult:
    """OCR 结果测试"""

    def test_ocr_result_creation(self):
        """测试 OCR 结果创建"""
        result = OCRResult(
            pdf_path="test.pdf",
            total_pages=1,
            pages=[{"page_num": 1, "text": "测试内容"}],
            processed_at="2026-04-07T10:00:00Z",
        )

        assert result.pdf_path == "test.pdf"
        assert result.total_pages == 1
        assert len(result.pages) == 1


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])