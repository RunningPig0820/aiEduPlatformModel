"""
模型路由器测试
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestModelRouter:
    """模型路由器测试"""

    def test_get_model_for_known_scene(self):
        """测试已知场景获取模型"""
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("page_assistant")
        assert provider == "zhipu"
        assert model == "glm-4-flash"

    def test_get_model_for_unknown_scene(self):
        """测试未知场景使用默认模型"""
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("unknown_scene")
        assert provider == "zhipu"
        assert model == "glm-4-flash"

    def test_get_model_homework_grading(self):
        """测试作业批改场景路由到 DeepSeek"""
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("homework_grading")
        assert provider == "deepseek"
        assert model == "deepseek-chat"

    def test_get_model_image_analysis(self):
        """测试图片分析场景路由到视觉模型"""
        from core.gateway.router import ModelRouter

        provider, model = ModelRouter.get_model("image_analysis")
        assert provider == "zhipu"
        assert model == "glm-4.6v"

    @patch("core.gateway.router.LLMFactory.create")
    def test_create_llm_with_scene(self, mock_create):
        """测试根据场景创建 LLM"""
        from core.gateway.router import ModelRouter

        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        llm, model_used = ModelRouter.create_llm(scene="page_assistant")

        mock_create.assert_called_once_with("zhipu", "glm-4-flash", 0.7)
        assert model_used == "zhipu/glm-4-flash"

    @patch("core.gateway.router.LLMFactory.create")
    def test_create_llm_with_explicit_provider(self, mock_create):
        """测试显式指定 provider 创建 LLM"""
        from core.gateway.router import ModelRouter

        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        llm, model_used = ModelRouter.create_llm(
            scene="page_assistant",
            provider="deepseek",
            model="deepseek-coder"
        )

        mock_create.assert_called_once_with("deepseek", "deepseek-coder", 0.7)
        assert model_used == "deepseek/deepseek-coder"

    @patch("core.gateway.router.LLMFactory.create")
    def test_create_llm_without_scene_or_provider(self, mock_create):
        """测试无场景和 provider 时使用默认"""
        from core.gateway.router import ModelRouter

        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        llm, model_used = ModelRouter.create_llm()

        mock_create.assert_called_once_with("zhipu", "glm-4-flash", 0.7)
        assert model_used == "zhipu/glm-4-flash"

    def test_is_free_model_true(self):
        """测试免费模型检测 - 是免费"""
        from core.gateway.router import ModelRouter

        assert ModelRouter.is_free_model("zhipu", "glm-4-flash") is True

    def test_is_free_model_false(self):
        """测试免费模型检测 - 不是免费"""
        from core.gateway.router import ModelRouter

        assert ModelRouter.is_free_model("zhipu", "glm-4.7") is False
        assert ModelRouter.is_free_model("deepseek", "deepseek-chat") is False

    def test_supports_vision_true(self):
        """测试视觉支持检测 - 支持"""
        from core.gateway.router import ModelRouter

        assert ModelRouter.supports_vision("zhipu", "glm-4.6v") is True

    def test_supports_vision_false(self):
        """测试视觉支持检测 - 不支持"""
        from core.gateway.router import ModelRouter

        assert ModelRouter.supports_vision("zhipu", "glm-4-flash") is False

    def test_supports_tools_all_models(self):
        """测试工具调用支持 - 所有模型都支持"""
        from core.gateway.router import ModelRouter

        assert ModelRouter.supports_tools("zhipu", "glm-4-flash") is True
        assert ModelRouter.supports_tools("deepseek", "deepseek-chat") is True
        assert ModelRouter.supports_tools("bailian", "qwen-turbo") is True

    def test_get_scene_defaults(self):
        """测试获取场景默认配置"""
        from core.gateway.router import ModelRouter

        defaults = ModelRouter.get_scene_defaults()

        assert "page_assistant" in defaults
        assert defaults["page_assistant"]["provider"] == "zhipu"
        assert defaults["page_assistant"]["model"] == "glm-4-flash"

    def test_free_model_priority(self):
        """测试免费模型优先策略"""
        from core.gateway.router import ModelRouter

        # 页面助手应该使用免费模型
        provider, model = ModelRouter.get_model("page_assistant")
        assert ModelRouter.is_free_model(provider, model) is True

        # FAQ 应该使用免费模型
        provider, model = ModelRouter.get_model("faq")
        assert ModelRouter.is_free_model(provider, model) is True