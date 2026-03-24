"""
智谱集成测试 (Mock API)
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestZhipuIntegration:
    """智谱 AI 集成测试"""

    @patch("core.gateway.factory.ChatZhipuAI")
    def test_invoke_chat(self, mock_chat):
        """测试基本对话调用"""
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "这是一个测试响应"
        mock_instance.invoke.return_value = mock_response
        mock_chat.return_value = mock_instance

        from core.gateway.factory import LLMFactory
        llm = LLMFactory.create("zhipu", "glm-4-flash")
        response = llm.invoke("你好")

        assert response.content == "这是一个测试响应"

    @patch("core.gateway.factory.ChatZhipuAI")
    def test_stream_chat(self, mock_chat):
        """测试流式对话"""
        mock_instance = MagicMock()
        chunks = [
            MagicMock(content="这"),
            MagicMock(content="是"),
            MagicMock(content="测试"),
        ]
        mock_instance.stream.return_value = iter(chunks)
        mock_chat.return_value = mock_instance

        from core.gateway.factory import LLMFactory
        llm = LLMFactory.create("zhipu", "glm-4-flash")
        result = ""
        for chunk in llm.stream("你好"):
            result += chunk.content

        assert result == "这是测试"

    @patch("core.gateway.factory.ChatZhipuAI")
    def test_bind_tools(self, mock_chat):
        """测试工具绑定"""
        from core.gateway.factory import LLMFactory
        from langchain_core.tools import tool

        @tool
        def test_tool(query: str) -> str:
            """测试工具"""
            return f"result: {query}"

        mock_instance = MagicMock()
        mock_instance.bind_tools = MagicMock(return_value=mock_instance)
        mock_chat.return_value = mock_instance

        llm = LLMFactory.create("zhipu", "glm-4-flash")
        llm_with_tools = llm.bind_tools([test_tool])

        mock_instance.bind_tools.assert_called_once()

    @patch("core.gateway.factory.ChatZhipuAI")
    def test_model_variants(self, mock_chat):
        """测试不同模型变体"""
        from core.gateway.factory import LLMFactory

        models = ["glm-4-flash", "glm-4.5-air", "glm-4.6v", "glm-4.7"]

        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance

        for model in models:
            LLMFactory.create("zhipu", model)

        assert mock_chat.call_count == len(models)