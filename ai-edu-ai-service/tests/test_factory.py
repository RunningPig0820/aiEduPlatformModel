"""
LLM Factory 测试
"""
import pytest
from unittest.mock import patch, MagicMock


class TestLLMFactory:
    """LLM Factory 单元测试"""

    def test_list_providers(self):
        """测试列出所有 providers"""
        from core.gateway.factory import LLMFactory

        providers = LLMFactory.list_providers()
        assert "zhipu" in providers
        assert "deepseek" in providers
        assert "bailian" in providers

    def test_get_default_model(self):
        """测试获取默认模型"""
        from core.gateway.factory import LLMFactory

        assert LLMFactory.get_default_model("zhipu") == "glm-4-flash"
        assert LLMFactory.get_default_model("deepseek") == "deepseek-chat"
        assert LLMFactory.get_default_model("bailian") == "qwen-turbo"

    def test_unknown_provider_raises_error(self):
        """测试未知的 provider 抛出异常"""
        from core.gateway.factory import LLMFactory

        with pytest.raises(ValueError) as exc_info:
            LLMFactory.create("unknown_provider")
        assert "Unknown provider" in str(exc_info.value)

    def test_missing_api_key_raises_error(self):
        """测试缺少 API Key 抛出异常"""
        import os
        from core.gateway.factory import LLMFactory

        # 临时移除 API Key
        original_key = os.environ.pop("ZHIPU_API_KEY", None)

        try:
            with pytest.raises(ValueError) as exc_info:
                LLMFactory._create_zhipu("glm-4-flash", 0.7)
            assert "not configured" in str(exc_info.value)
        finally:
            if original_key:
                os.environ["ZHIPU_API_KEY"] = original_key

    @patch("core.gateway.factory.ChatZhipuAI")
    def test_create_zhipu(self, mock_chat_zhipu):
        """测试创建智谱 ChatModel"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_chat_zhipu.return_value = mock_instance

        result = LLMFactory._create_zhipu("glm-4-flash", 0.7)

        mock_chat_zhipu.assert_called_once()
        call_kwargs = mock_chat_zhipu.call_args[1]
        assert call_kwargs["model"] == "glm-4-flash"
        assert call_kwargs["temperature"] == 0.7
        assert result == mock_instance

    @patch("core.gateway.factory.ChatOpenAI")
    def test_create_deepseek(self, mock_chat_openai):
        """测试创建 DeepSeek ChatModel"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance

        result = LLMFactory._create_deepseek("deepseek-chat", 0.7)

        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "deepseek-chat"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["openai_api_base"] == "https://api.deepseek.com/v1"
        assert result == mock_instance

    @patch("core.gateway.factory.ChatTongyi")
    def test_create_bailian(self, mock_chat_tongyi):
        """测试创建百炼 ChatModel"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_chat_tongyi.return_value = mock_instance

        result = LLMFactory._create_bailian("qwen-turbo", 0.7)

        mock_chat_tongyi.assert_called_once()
        call_kwargs = mock_chat_tongyi.call_args[1]
        assert call_kwargs["model"] == "qwen-turbo"
        assert call_kwargs["temperature"] == 0.7
        assert result == mock_instance

    @patch("core.gateway.factory.LLMFactory._create_zhipu")
    def test_create_uses_default_model(self, mock_create_zhipu):
        """测试 create 方法使用默认模型"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_create_zhipu.return_value = mock_instance

        LLMFactory.create("zhipu")

        mock_create_zhipu.assert_called_once_with("glm-4-flash", 0.7)

    @patch("core.gateway.factory.LLMFactory._create_zhipu")
    def test_create_with_custom_model(self, mock_create_zhipu):
        """测试 create 方法使用自定义模型"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_create_zhipu.return_value = mock_instance

        LLMFactory.create("zhipu", model="glm-4.7", temperature=0.5)

        mock_create_zhipu.assert_called_once_with("glm-4.7", 0.5)