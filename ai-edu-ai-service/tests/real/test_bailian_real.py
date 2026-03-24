"""
阿里百炼 真实 API 测试
需要设置 DASHSCOPE_API_KEY 环境变量
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestBailianRealAPI:
    """阿里百炼 真实 API 测试"""

    @pytest.mark.requires_bailian
    def test_basic_chat(self):
        """测试基本对话"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("bailian", "qwen-turbo")
        response = llm.invoke("你好，请用一句话介绍自己")

        assert response is not None
        assert response.content
        print(f"\n✅ 百炼响应: {response.content[:100]}...")

    @pytest.mark.requires_bailian
    def test_stream_chat(self):
        """测试流式对话"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("bailian", "qwen-turbo")
        chunks = list(llm.stream("数到5"))

        assert len(chunks) > 0
        full_content = "".join(chunk.content for chunk in chunks)
        print(f"\n✅ 百炼流式响应: {full_content}")

    @pytest.mark.requires_bailian
    def test_model_variants(self):
        """测试不同模型变体"""
        from core.gateway.factory import LLMFactory

        models = ["qwen-turbo", "qwen-plus", "qwen-math-turbo"]
        for model in models:
            llm = LLMFactory.create("bailian", model)
            response = llm.invoke("你好")
            assert response.content
            print(f"\n✅ 百炼 {model}: {response.content[:50]}...")

    @pytest.mark.requires_bailian
    def test_math_model(self):
        """测试数学专用模型"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("bailian", "qwen-math-turbo")
        response = llm.invoke("计算: 123 + 456 = ?")

        assert response.content
        print(f"\n✅ 数学模型: {response.content}")

    @pytest.mark.requires_bailian
    def test_tool_calling(self):
        """测试工具调用能力"""
        from core.gateway.factory import LLMFactory
        from langchain_core.tools import tool

        @tool
        def query_database(sql: str) -> str:
            """查询数据库"""
            return f"查询结果: {sql}"

        llm = LLMFactory.create("bailian", "qwen-turbo")
        llm_with_tools = llm.bind_tools([query_database])

        response = llm_with_tools.invoke("帮我查询用户表")
        assert response is not None
        print(f"\n✅ 百炼工具调用: {response}")


class TestBailianErrors:
    """百炼错误处理测试"""

    @pytest.mark.requires_bailian
    def test_encoding_handling(self):
        """测试中文编码处理"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("bailian", "qwen-turbo")
        # 测试中文问题
        response = llm.invoke("请用中文回答：什么是人工智能？")
        assert response.content
        print(f"\n✅ 百炼中文响应: {response.content[:100]}...")