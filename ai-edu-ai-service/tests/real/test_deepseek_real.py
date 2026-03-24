"""
DeepSeek 真实 API 测试
需要设置 DEEPSEEK_API_KEY 环境变量
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestDeepSeekRealAPI:
    """DeepSeek 真实 API 测试"""

    @pytest.mark.requires_deepseek
    def test_basic_chat(self):
        """测试基本对话"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("deepseek", "deepseek-chat")
        response = llm.invoke("你好，请用一句话介绍自己")

        assert response is not None
        assert response.content
        print(f"\n✅ DeepSeek 响应: {response.content[:100]}...")

    @pytest.mark.requires_deepseek
    def test_stream_chat(self):
        """测试流式对话"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("deepseek", "deepseek-chat")
        chunks = list(llm.stream("数到5"))

        assert len(chunks) > 0
        full_content = "".join(chunk.content for chunk in chunks)
        print(f"\n✅ DeepSeek 流式响应: {full_content}")

    @pytest.mark.requires_deepseek
    def test_model_variants(self):
        """测试不同模型变体"""
        from core.gateway.factory import LLMFactory

        models = ["deepseek-chat", "deepseek-coder"]
        for model in models:
            llm = LLMFactory.create("deepseek", model)
            response = llm.invoke("你好")
            assert response.content
            print(f"\n✅ DeepSeek {model}: {response.content[:50]}...")

    @pytest.mark.requires_deepseek
    def test_tool_calling(self):
        """测试工具调用能力"""
        from core.gateway.factory import LLMFactory
        from langchain_core.tools import tool

        @tool
        def search(query: str) -> str:
            """搜索工具"""
            return f"搜索结果: {query}"

        llm = LLMFactory.create("deepseek", "deepseek-chat")
        llm_with_tools = llm.bind_tools([search])

        response = llm_with_tools.invoke("帮我搜索一下天气")
        assert response is not None
        print(f"\n✅ DeepSeek 工具调用: {response}")

    @pytest.mark.requires_deepseek
    def test_code_generation(self):
        """测试代码生成能力（deepseek-coder）"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("deepseek", "deepseek-coder")
        response = llm.invoke("写一个 Python 函数计算斐波那契数列")

        assert response.content
        assert "def" in response.content or "function" in response.content.lower()
        print(f"\n✅ DeepSeek Coder 代码生成:\n{response.content[:200]}...")


class TestDeepSeekScenes:
    """DeepSeek 场景路由测试"""

    @pytest.mark.requires_deepseek
    def test_homework_grading_scene(self):
        """测试作业批改场景"""
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("homework_grading")
        assert provider == "deepseek"
        assert model == "deepseek-chat"

    @pytest.mark.requires_deepseek
    def test_content_generation_scene(self):
        """测试内容生成场景"""
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("content_generation")
        assert provider == "deepseek"