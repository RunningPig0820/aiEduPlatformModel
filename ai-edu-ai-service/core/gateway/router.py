"""
模型路由器 - 根据场景自动选择最优模型
"""
from typing import Tuple, Optional

from config.model_config import SCENE_MODEL_MAPPING, DEFAULT_SCENE, MODEL_CONFIG
from core.gateway.factory import LLMFactory
from langchain_core.language_models.chat_models import BaseChatModel


class ModelRouter:
    """
    模型路由器 - 根据场景自动选择最优模型

    特性:
    - 场景驱动路由
    - 免费模型优先
    - 默认模型 fallback
    """

    @staticmethod
    def get_model(scene: str) -> Tuple[str, str]:
        """
        根据场景获取推荐模型

        Args:
            scene: 场景代码

        Returns:
            Tuple[str, str]: (provider, model)
        """
        return SCENE_MODEL_MAPPING.get(scene, DEFAULT_SCENE)

    @staticmethod
    def create_llm(
        scene: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Tuple[BaseChatModel, str]:
        """
        创建 LLM 实例

        优先级:
        1. 显式指定的 provider + model
        2. 场景映射的模型

        Args:
            scene: 场景代码
            provider: 显式指定的 provider
            model: 显式指定的 model
            temperature: 温度参数

        Returns:
            Tuple[BaseChatModel, str]: (LLM 实例, "provider/model" 字符串)
        """
        # 如果显式指定了 provider
        if provider:
            final_provider = provider
            final_model = model or LLMFactory.get_default_model(provider)
        elif scene:
            # 根据场景路由
            final_provider, final_model = ModelRouter.get_model(scene)
        else:
            # 使用默认
            final_provider, final_model = DEFAULT_SCENE

        # 创建 LLM
        llm = LLMFactory.create(final_provider, final_model, temperature)

        return llm, f"{final_provider}/{final_model}"

    @staticmethod
    def get_scene_defaults() -> dict:
        """获取场景默认配置"""
        return {
            scene: {"provider": provider, "model": model}
            for scene, (provider, model) in SCENE_MODEL_MAPPING.items()
        }

    @staticmethod
    def is_free_model(provider: str, model: str) -> bool:
        """检查是否是免费模型"""
        if provider not in MODEL_CONFIG:
            return False
        if model not in MODEL_CONFIG[provider]["models"]:
            return False
        return MODEL_CONFIG[provider]["models"][model].get("free", False)

    @staticmethod
    def supports_vision(provider: str, model: str) -> bool:
        """检查是否支持视觉"""
        if provider not in MODEL_CONFIG:
            return False
        if model not in MODEL_CONFIG[provider]["models"]:
            return False
        return MODEL_CONFIG[provider]["models"][model].get("supports_vision", False)

    @staticmethod
    def supports_tools(provider: str, model: str) -> bool:
        """检查是否支持工具调用"""
        if provider not in MODEL_CONFIG:
            return False
        if model not in MODEL_CONFIG[provider]["models"]:
            return False
        return MODEL_CONFIG[provider]["models"][model].get("supports_tools", False)