"""
路由器真实 API 测试
测试场景路由到真实模型
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestRouterRealAPI:
    """路由器真实 API 测试"""

    @pytest.mark.requires_zhipu
    def test_page_assistant_scene(self):
        """测试页面助手场景（免费模型）"""
        from core.gateway.router import ModelRouter

        llm, model_used = ModelRouter.create_llm(scene="page_assistant")
        response = llm.invoke("这是一个测试问题")

        assert response.content
        assert model_used == "zhipu/glm-4-flash"
        print(f"\n✅ 页面助手场景: {model_used} -> {response.content[:50]}...")

    @pytest.mark.requires_zhipu
    def test_faq_scene(self):
        """测试 FAQ 场景（免费模型）"""
        from core.gateway.router import ModelRouter

        llm, model_used = ModelRouter.create_llm(scene="faq")
        response = llm.invoke("什么是 Python？")

        assert response.content
        assert ModelRouter.is_free_model(*model_used.split("/"))
        print(f"\n✅ FAQ 场景: {model_used}")

    @pytest.mark.requires_zhipu
    def test_image_analysis_scene(self):
        """测试图片分析场景（视觉模型）"""
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("image_analysis")
        assert provider == "zhipu"
        assert model == "glm-4.6v"
        assert ModelRouter.supports_vision(provider, model)
        print(f"\n✅ 图片分析场景: {provider}/{model}")

    @pytest.mark.requires_deepseek
    def test_homework_grading_scene(self):
        """测试作业批改场景"""
        from core.gateway.router import ModelRouter

        llm, model_used = ModelRouter.create_llm(scene="homework_grading")
        response = llm.invoke("请批改这道题：1+1=3")

        assert response.content
        assert "deepseek" in model_used
        print(f"\n✅ 作业批改场景: {model_used} -> {response.content[:50]}...")


class TestRouterPriority:
    """路由优先级测试"""

    @pytest.mark.requires_zhipu
    def test_free_model_priority(self):
        """测试免费模型优先"""
        from core.gateway.router import ModelRouter

        # 这些场景应该使用免费模型
        free_scenes = ["page_assistant", "faq"]

        for scene in free_scenes:
            provider, model = ModelRouter.get_model(scene)
            assert ModelRouter.is_free_model(provider, model), f"{scene} 应该使用免费模型"
            print(f"\n✅ {scene} -> {provider}/{model} (免费)")


class TestRouterCapabilities:
    """路由能力检测测试"""

    def test_capability_detection(self):
        """测试能力检测"""
        from core.gateway.router import ModelRouter

        # 视觉能力
        assert ModelRouter.supports_vision("zhipu", "glm-4.6v") is True
        assert ModelRouter.supports_vision("zhipu", "glm-4-flash") is False

        # 工具能力
        assert ModelRouter.supports_tools("zhipu", "glm-4-flash") is True
        assert ModelRouter.supports_tools("deepseek", "deepseek-chat") is True

        # 免费模型
        assert ModelRouter.is_free_model("zhipu", "glm-4-flash") is True
        assert ModelRouter.is_free_model("zhipu", "glm-4.7") is False

        print(f"\n✅ 能力检测正确")