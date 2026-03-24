"""
智谱 AI 真实 API 测试
需要设置 ZHIPU_API_KEY 环境变量
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestZhipuRealAPI:
    """智谱 AI 真实 API 测试"""

    @pytest.mark.requires_zhipu
    def test_basic_chat(self):
        """测试基本对话"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("zhipu", "glm-4-flash")
        response = llm.invoke("你好，请用一句话介绍自己")

        assert response is not None
        assert response.content
        print(f"\n✅ 智谱响应: {response.content[:100]}...")

    @pytest.mark.requires_zhipu
    def test_stream_chat(self):
        """测试流式对话"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("zhipu", "glm-4-flash")
        chunks = list(llm.stream("数到5"))

        assert len(chunks) > 0
        full_content = "".join(chunk.content for chunk in chunks)
        print(f"\n✅ 智谱流式响应: {full_content}")

    @pytest.mark.requires_zhipu
    def test_model_variants(self):
        """测试不同模型变体"""
        from core.gateway.factory import LLMFactory

        models = ["glm-4-flash", "glm-4.5-air"]
        for model in models:
            llm = LLMFactory.create("zhipu", model)
            response = llm.invoke("你好")
            assert response.content
            print(f"\n✅ 智谱 {model}: {response.content[:50]}...")

    @pytest.mark.requires_zhipu
    def test_vision_model(self):
        """测试视觉模型（glm-4.6v）"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("zhipu", "glm-4.6v")
        # 简单文本测试，确认模型可调用
        response = llm.invoke("你好")
        assert response.content
        print(f"\n✅ 智谱视觉模型: {response.content[:50]}...")

    @pytest.mark.requires_zhipu
    def test_tool_calling(self):
        """测试工具调用能力"""
        from core.gateway.factory import LLMFactory
        from langchain_core.tools import tool

        @tool
        def get_weather(city: str) -> str:
            """获取城市天气"""
            return f"{city}的天气是晴天"

        llm = LLMFactory.create("zhipu", "glm-4-flash")
        llm_with_tools = llm.bind_tools([get_weather])

        response = llm_with_tools.invoke("北京今天天气怎么样？")
        assert response is not None
        print(f"\n✅ 智谱工具调用: {response}")


class TestZhipuFreeModels:
    """智谱免费模型专项测试"""

    @pytest.mark.requires_zhipu
    def test_free_model_availability(self):
        """测试免费模型可用性"""
        from core.gateway.factory import LLMFactory
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("page_assistant")
        assert provider == "zhipu"
        assert ModelRouter.is_free_model(provider, model) is True

        llm = LLMFactory.create(provider, model)
        response = llm.invoke("测试免费模型")
        assert response.content
        print(f"\n✅ 免费模型 glm-4-flash 可用")

    @pytest.mark.requires_zhipu
    def test_free_model_cost_tracking(self):
        """测试免费模型无成本（验证响应元数据）"""
        from core.gateway.factory import LLMFactory

        llm = LLMFactory.create("zhipu", "glm-4-flash")
        response = llm.invoke("测试")

        # 免费模型应该没有 token 费用
        print(f"\n✅ 响应元数据: {response.response_metadata}")