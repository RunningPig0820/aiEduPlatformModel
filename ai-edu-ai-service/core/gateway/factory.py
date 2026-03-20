"""
LLM Factory - 创建 LangChain ChatModel 实例
"""
from typing import Optional, Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel

from config.settings import settings


class LLMFactory:
    """
    LLM 工厂 - 根据配置创建 LangChain ChatModel 实例

    支持的 Provider:
    - zhipu: 智谱 AI (GLM 系列)
    - deepseek: DeepSeek (通过 OpenAI 兼容协议)
    - bailian: 阿里云百炼 (通义千问)
    """

    # Provider 默认模型映射
    DEFAULT_MODELS: Dict[str, str] = {
        "zhipu": "glm-4-flash",
        "deepseek": "deepseek-chat",
        "bailian": "qwen-turbo",
    }

    # Provider 默认参数
    PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
        "zhipu": {
            "api_key_env": "ZHIPU_API_KEY",
        },
        "deepseek": {
            "api_key_env": "DEEPSEEK_API_KEY",
            "api_base": "https://api.deepseek.com/v1",
        },
        "bailian": {
            "api_key_env": "BAILIAN_API_KEY",
        },
    }

    @staticmethod
    def create(
        provider: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> BaseChatModel:
        """
        创建 LangChain ChatModel 实例

        Args:
            provider: LLM 提供商名称 (zhipu, deepseek, bailian)
            model: 模型名称，不传则使用默认模型
            temperature: 温度参数，控制随机性
            **kwargs: 其他传递给 ChatModel 的参数

        Returns:
            BaseChatModel: LangChain ChatModel 实例

        Raises:
            ValueError: 不支持的 provider 或缺少 API Key
        """
        provider = provider.lower()

        if provider not in LLMFactory.DEFAULT_MODELS:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Supported providers: {list(LLMFactory.DEFAULT_MODELS.keys())}"
            )

        # 使用默认模型
        if model is None:
            model = LLMFactory.DEFAULT_MODELS[provider]

        # 根据不同 provider 创建对应的 ChatModel
        if provider == "zhipu":
            return LLMFactory._create_zhipu(model, temperature, **kwargs)
        elif provider == "deepseek":
            return LLMFactory._create_deepseek(model, temperature, **kwargs)
        elif provider == "bailian":
            return LLMFactory._create_bailian(model, temperature, **kwargs)
        else:
            raise ValueError(f"Provider {provider} not implemented")

    @staticmethod
    def _create_zhipu(
        model: str,
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """创建智谱 ChatModel"""
        from langchain_community.chat_models import ChatZhipuAI

        api_key = settings.ZHIPU_API_KEY
        if not api_key:
            raise ValueError("ZHIPU_API_KEY not configured in environment")

        return ChatZhipuAI(
            model=model,
            temperature=temperature,
            zhipuai_api_key=api_key,
            **kwargs
        )

    @staticmethod
    def _create_deepseek(
        model: str,
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """创建 DeepSeek ChatModel (使用 OpenAI 兼容协议)"""
        from langchain_openai import ChatOpenAI

        api_key = settings.DEEPSEEK_API_KEY
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not configured in environment")

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=api_key,
            openai_api_base="https://api.deepseek.com/v1",
            **kwargs
        )

    @staticmethod
    def _create_bailian(
        model: str,
        temperature: float,
        **kwargs
    ) -> BaseChatModel:
        """创建百炼 ChatModel (通义千问)"""
        from langchain_community.chat_models import ChatTongyi

        api_key = settings.BAILIAN_API_KEY
        if not api_key:
            raise ValueError("BAILIAN_API_KEY not configured in environment")

        return ChatTongyi(
            model=model,
            temperature=temperature,
            dashscope_api_key=api_key,
            **kwargs
        )

    @staticmethod
    def list_providers() -> list:
        """列出所有支持的 provider"""
        return list(LLMFactory.DEFAULT_MODELS.keys())

    @staticmethod
    def get_default_model(provider: str) -> str:
        """获取 provider 的默认模型"""
        if provider not in LLMFactory.DEFAULT_MODELS:
            raise ValueError(f"Unknown provider: {provider}")
        return LLMFactory.DEFAULT_MODELS[provider]