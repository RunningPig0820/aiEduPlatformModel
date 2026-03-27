"""
DeepSeek 集成测试 (Mock API)
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDeepSeekIntegration:
    """DeepSeek 集成测试"""

    @patch("core.gateway.factory.ChatOpenAI")
    def test_api_base_configuration(self, mock_chat):
        """测试 API Base 配置"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance

        LLMFactory.create("deepseek", "deepseek-chat")

        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs["openai_api_base"] == "https://api.deepseek.com/v1"

    @patch("core.gateway.factory.ChatOpenAI")
    def test_invoke_chat(self, mock_chat):
        """测试基本对话调用"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "这是一个 DeepSeek 测试响应"
        mock_instance.invoke.return_value = mock_response
        mock_chat.return_value = mock_instance

        llm = LLMFactory.create("deepseek", "deepseek-chat")
        response = llm.invoke("你好")

        assert response.content == "这是一个 DeepSeek 测试响应"

    @patch("core.gateway.factory.ChatOpenAI")
    def test_stream_chat(self, mock_chat):
        """测试流式对话"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        chunks = [
            MagicMock(content="这"),
            MagicMock(content="是"),
            MagicMock(content="DeepSeek"),
        ]
        mock_instance.stream.return_value = iter(chunks)
        mock_chat.return_value = mock_instance

        llm = LLMFactory.create("deepseek", "deepseek-chat")
        result = ""
        for chunk in llm.stream("你好"):
            result += chunk.content

        assert result == "这是DeepSeek"

    @patch("core.gateway.factory.ChatOpenAI")
    def test_bind_tools(self, mock_chat):
        """测试工具绑定"""
        from core.gateway.factory import LLMFactory
        from langchain_core.tools import tool

        @tool
        def search_tool(query: str) -> str:
            """搜索工具"""
            return f"search: {query}"

        mock_instance = MagicMock()
        mock_instance.bind_tools = MagicMock(return_value=mock_instance)
        mock_chat.return_value = mock_instance

        llm = LLMFactory.create("deepseek", "deepseek-chat")
        llm_with_tools = llm.bind_tools([search_tool])

        mock_instance.bind_tools.assert_called_once()

    @patch("core.gateway.factory.ChatOpenAI")
    def test_model_variants(self, mock_chat):
        """测试不同模型变体"""
        from core.gateway.factory import LLMFactory

        models = ["deepseek-chat", "deepseek-coder"]

        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance

        for model in models:
            LLMFactory.create("deepseek", model)

        assert mock_chat.call_count == len(models)