"""
智谱集成测试 (Mock API)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestZhipuIntegration:
    """智谱 AI 集成测试"""

    @pytest.mark.asyncio
    async def test_invoke_chat(self):
        """测试基本对话调用"""
        from core.gateway.factory import LLMFactory

        with patch("core.gateway.factory.ChatZhipuAI") as mock_chat:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "这是一个测试响应"
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            llm = LLMFactory.create("zhipu", "glm-4-flash")
            response = llm.invoke("你好")

            assert response.content == "这是一个测试响应"

    @pytest.mark.asyncio
    async def test_stream_chat(self):
        """测试流式对话"""
        from core.gateway.factory import LLMFactory

        with patch("core.gateway.factory.ChatZhipuAI") as mock_chat:
            mock_instance = MagicMock()
            # 模拟流式响应
            chunks = [
                MagicMock(content="这"),
                MagicMock(content="是"),
                MagicMock(content="测试"),
            ]
            mock_instance.stream.return_value = iter(chunks)
            mock_chat.return_value = mock_instance

            llm = LLMFactory.create("zhipu", "glm-4-flash")
            result = ""
            for chunk in llm.stream("你好"):
                result += chunk.content

            assert result == "这是测试"

    def test_bind_tools(self):
        """测试工具绑定"""
        from core.gateway.factory import LLMFactory
        from langchain_core.tools import tool

        @tool
        def test_tool(query: str) -> str:
            """测试工具"""
            return f"result: {query}"

        with patch("core.gateway.factory.ChatZhipuAI") as mock_chat:
            mock_instance = MagicMock()
            mock_instance.bind_tools = MagicMock(return_value=mock_instance)
            mock_chat.return_value = mock_instance

            llm = LLMFactory.create("zhipu", "glm-4-flash")
            llm_with_tools = llm.bind_tools([test_tool])

            mock_instance.bind_tools.assert_called_once()

    def test_tool_calls_in_response(self):
        """测试响应中的工具调用"""
        from core.gateway.factory import LLMFactory

        with patch("core.gateway.factory.ChatZhipuAI") as mock_chat:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.content = None
            mock_response.tool_calls = [
                {
                    "name": "test_tool",
                    "args": {"query": "test"},
                    "id": "call_123"
                }
            ]
            mock_instance.invoke.return_value = mock_response
            mock_chat.return_value = mock_instance

            llm = LLMFactory.create("zhipu", "glm-4-flash")
            response = llm.invoke("调用工具")

            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["name"] == "test_tool"

    def test_model_variants(self):
        """测试不同模型变体"""
        from core.gateway.factory import LLMFactory

        models = ["glm-4-flash", "glm-4.5-air", "glm-4.6v", "glm-4.7"]

        with patch("core.gateway.factory.ChatZhipuAI") as mock_chat:
            mock_instance = MagicMock()
            mock_chat.return_value = mock_instance

            for model in models:
                LLMFactory.create("zhipu", model)

            assert mock_chat.call_count == len(models)