"""
阿里百炼集成测试 (Mock API)
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestBailianIntegration:
    """阿里百炼集成测试"""

    @patch("core.gateway.factory.ChatOpenAI")
    def test_invoke_chat(self, mock_chat):
        """测试基本对话调用"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "这是一个百炼测试响应"
        mock_instance.invoke.return_value = mock_response
        mock_chat.return_value = mock_instance

        llm = LLMFactory.create("bailian", "qwen-turbo")
        response = llm.invoke("你好")

        assert response.content == "这是一个百炼测试响应"

    @patch("core.gateway.factory.ChatOpenAI")
    def test_stream_chat(self, mock_chat):
        """测试流式对话"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        chunks = [
            MagicMock(content="这"),
            MagicMock(content="是"),
            MagicMock(content="百炼"),
        ]
        mock_instance.stream.return_value = iter(chunks)
        mock_chat.return_value = mock_instance

        llm = LLMFactory.create("bailian", "qwen-turbo")
        result = ""
        for chunk in llm.stream("你好"):
            result += chunk.content

        assert result == "这是百炼"

    @patch("core.gateway.factory.ChatOpenAI")
    def test_bind_tools(self, mock_chat):
        """测试工具绑定"""
        from core.gateway.factory import LLMFactory
        from langchain_core.tools import tool

        @tool
        def query_tool(question: str) -> str:
            """查询工具"""
            return f"answer: {question}"

        mock_instance = MagicMock()
        mock_instance.bind_tools = MagicMock(return_value=mock_instance)
        mock_chat.return_value = mock_instance

        llm = LLMFactory.create("bailian", "qwen-turbo")
        llm_with_tools = llm.bind_tools([query_tool])

        mock_instance.bind_tools.assert_called_once()

    @patch("core.gateway.factory.ChatOpenAI")
    def test_model_variants(self, mock_chat):
        """测试不同模型变体"""
        from core.gateway.factory import LLMFactory

        models = ["qwen-turbo", "qwen-plus", "qwen-math-turbo"]

        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance

        for model in models:
            LLMFactory.create("bailian", model)

        assert mock_chat.call_count == len(models)

    @patch("core.gateway.factory.ChatOpenAI")
    def test_dashscope_api_key_used(self, mock_chat):
        """测试使用百炼 API Key (OpenAI 兼容模式)"""
        from core.gateway.factory import LLMFactory

        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance

        LLMFactory.create("bailian", "qwen-turbo")

        call_kwargs = mock_chat.call_args[1]
        assert "openai_api_key" in call_kwargs
        assert call_kwargs["openai_api_base"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"